# Optimization log — difference-ladders

Every attempt, its measurement, and what was kept or rejected, failures
included. Process: [OPTIMIZATION.md](../OPTIMIZATION.md). Letters: b and p
on A216666 and A216668, m on A229073 (CLAUDE.md 5i); the engine's own
names (x, `pb`, `PRP_Q2`, ...) where a passage describes the code.

## Round 0 — the build, and what was measured at the day-long filters (2026-11-23)

**What was inherited.** cyclotomic-ladders' engine v2 and planner p2, taken
whole: power-ladders' window sieve with the device Fermat stage, its
window pattern of one period, its planner (wheel and window chosen
together by expected clock to a confirmed find), every constant as that
project measured it. Changed for this project: the kill sets (the residues
b ≡ 1/(ζ − 1) for each primitive p-th root of unity ζ, from a primitive
root), the Fermat stage's value arithmetic ((b+1)^p − b^p as two
truncated powers and their difference mod 2^(32·limbs), where that
project formed cyclotomic values by Horner), the tail's residue list
(NRES_MAX 128 → 256), no class (nothing is forced: the unit is 1 at every
filter and the class-space machinery is refused every other unit), and the
gate battery re-parametrized for weak, unforced wheels in b-space.

**The target (rule 3b).** From the model's quantiles at the rates below:
**A216666 n = 11** (a(11): median 9 months, the first filter of that family
whose median clock passes a day; n = 10's median is 14 hours) and
**A216668 n = 24** (a(24): median 22 days; n = 18's a(18) is 19 minutes,
and n = 19..23 sieve the same forms as 18 and will almost surely settle
with it). Every measurement below names its filter; the openings (A216666
n = 9, A216668 n = 18) and A216666's first promotion (n = 10) were
checked, not optimized.

**The harnesses** (session scratchpad, not committed — CLAUDE.md rule 9),
so the next person can rewrite them in ten minutes: `prof.py` (the planned
campaign engine at a filter and height; every kernel a launch enqueues —
nebuild, the sieve, each tail round, each Fermat form — wrapped in CUDA
events, summed per kernel over 24 launches after two warm-ups, against the
wall); `ab.py` (one planned engine per arm with keyword overrides, every
arm over the SAME first launches of the segment at a height, one warm-up,
three interleaved rounds, ratios to the first arm with [min, max]; the
candidates counted exactly per launch, never launches × the launch size —
the partial-launch overcount); `hostprice.py` (1,200 windows of the planned
engine, every value that reaches the host classified inline by the pool's
own `sprp_run` and timed, the rare paths counted with the paths stubbed);
`blscost.py` (a b near a height with the value at p prime, then the N − 1
factoring and the certificate timed); `freeze_shapes.py` (score.py's shapes
without the gates, twice, for the fingerprints).

### The phase split at the day-long filters

The planned engines, inherited constants (six Fermat forms on A216666 at
the time), 24 launches; the kernels summed to 100% of the wall clock at
both filters (the host is overlapped and nothing else sits in the loop):

| kernel | A216666 n = 11, b = 3·10²¹ | A216668 n = 24, b = 3·10¹⁹ |
|---|---|---|
| sieve (window + in-block rounds) | 34.9 ms/launch, 35.8% | 23.3 ms, 29.2% |
| generated tail rounds | 23.2 ms, 23.8% | 22.6 ms, 28.4% |
| Fermat p = 2 | 5.7 ms, 5.9% | 6.5 ms, 8.1% |
| Fermat p = 3 | 8.1 ms, 8.3% | 9.5 ms, 11.9% |
| Fermat p = 5 | 10.8 ms, 11.1% | 9.5 ms, 12.0% |
| Fermat p = 7 | 2.3 ms, 2.4% | 2.6 ms, 3.3% |
| Fermat p = 11 | 5.9 ms, 6.1% | — |
| Fermat p = 13 | 6.4 ms, 6.6% | 5.6 ms, 7.0% |
| nebuild | 0.02 ms | 0.07 ms |
| **launch** | **97.4 ms, 6.87·10¹⁰ candidates** | **79.7 ms, 3.42·10¹⁰** |

7.0·10¹¹ and 4.3·10¹¹ candidates a second. **The weak wheel is the whole
story**: the planned wheels keep 0.51% (n = 11) and 2.6% (n = 24) of the
line, the window takes 77–78 primes before the survival target, and enough
values survive the sieve that the Fermat stage costs as much as the
window. At cyclotomic-ladders' forced classes the same kernels ran 5·10¹²
candidates a second, which is the yardstick the survey priced this cluster
at; it does not hold here. The forms past p = 7 cost far more per value
tested than their share of the queue suggests (the value at p = 13 is 28 limbs at
b = 3·10²¹, fully unrolled), which is what the next measurement exploited.

### The sieve depth (PRP_Q2), paired, at the day-long filters

Candidates' line per second against the planned 8,192, three interleaved
rounds of eight launches (the streams differ by depth, as they must):

| depth | A216666 n = 11 | A216668 n = 24 |
|---|---|---|
| 4,096 | 0.777 [0.770, 0.779] | — |
| **8,192** | **1.000** | **1.000** |
| 16,384 | 1.006 [1.001, 1.006] | 0.846 [0.837, 0.848] |
| 32,768 | 0.930 | — |
| 65,536 | 0.769 | — |

Kept at 8,192: 16,384 is a tie at n = 11 and loses 15% at n = 24, where
the second octave adds two tail rounds (the residue lists past 128 slots,
primes with 2·61·89 | q − 1, begin at 10,859).

### The device Fermat stage's form count (PRP_FORMS), paired, with the host priced

The stage tests the leading forms of every survivor on the device; fewer
forms hand more values to the host. Device rate against six forms (A216666)
or five (A216668), and the values a second the host must then classify:

| filter, height | 6 forms | 5 forms | 4 forms | 3 forms |
|---|---|---|---|---|
| A216666 n = 11, 3·10²¹ | 1.000 (43/s) | **1.069** [1.059, 1.076] (1,301/s) | 1.120 (43,390/s) | 0.969 (695,000/s) |
| A216666 n = 10, 3.7·10¹⁵ | 1.000 (161/s) | **1.045** [1.045, 1.050] (5,100/s) | 1.081 (131,900/s) | — |
| A216666 n = 9, 5.6·10¹⁰ | 1.000 (692/s) | **1.026** [1.017, 1.040] (17,370/s) | 1.072 (352,200/s) | — |
| A216668 n = 24, 3·10¹⁹ | — | **1.000** (2,422/s) | 1.058 (85,430/s) | 0.805 |
| A216668 n = 18, 2.9·10¹¹ | 0.949 (501/s) | **1.000** (16,890/s) | 0.945 | — |

(A216668's "6 forms" tests its sixth sieved form, p = 17, which lies past
the census floor's first six conditions.) The host's cost per base-2 test
(gmpy2) of the value at b = 3·10²¹: p = 5 13 µs, 7 26 µs, 11 94 µs,
13 144 µs; at 3·10¹⁹: p = 13 100 µs, 17 218 µs, 19 300 µs, 31 1.3 ms.
**Shipped: five forms
on A216666** (`launch.PRP_FORMS`), 1.069x at the day-long filter for about
0.2 core-s per second of host. **Declined: four forms**, 1.12x at n = 11 and
1.06x at A216668 n = 24, because it hands the host 43,000 to 350,000 values
a second — five to ten cores, for days — which the load budget (CLAUDE.md
5f) does not buy for 5%; the owner may take it with `PRP_FORMS` if the
machine is idle otherwise. A216668 stays at five, the most its census
floor allows and the best measured at both of its filters. The campaign
shapes of score.py were frozen at five.

### The host, priced by its counted rate (rules 5c and 5k)

1,200 windows (launches) of the planned engine at each day-long filter,
every value reaching the host classified by the pool's own `sprp_run`:

| | A216666 n = 11, 3·10²¹ | A216668 n = 24, 3·10¹⁹ |
|---|---|---|
| line per window | 1.34·10¹³ b, 0.10 s of device | 1.32·10¹² b, 0.089 s |
| device s per b | 7.6·10⁻¹⁵ | 6.7·10⁻¹⁴ |
| values to the host | 127 a window | 199 a window |
| classification | 296 µs each: 0.038 core-s a window | 469 µs each: 0.093 core-s a window |
| host core-s per device-s | 0.37: a pool of 1 at the 2x margin | 1.05: a pool of 3 |
| runs seen (census) | 5: 148,123; 6: 4,107; 7: 78; 8: 2 | 4: 1,967; 6: 231,857; 7: 5,215; 10: 82; 17: 1 |

The pool is sized at run time from a measurement at the campaign's own
filter (`Campaign.calibrate`), so these numbers are a check, not a
constant. The rare host paths, each priced by its counted rate
(`huntlib.hostcost.price_line`):

* NEAR verification (A216666 n = 11): never in 1,200 windows (0 of 1,200),
  0.54 s each -> 0% of 0.10 s windows. The model expects about 105 values
  of run 10 over a(11)'s whole search (b from 5·10¹⁸ to 3.2·10²¹), one in
  2.7 days: 2·10⁻⁶ of the clock.
* NEAR verification (A216668 n = 24): never in 1,200 windows (0 of 1,200),
  1.4 s each (nine primes to 1,171 digits and fourteen composites) -> 0% of
  0.089 s windows. The model expects about 440 values of run 23 over
  a(24)'s search, twenty a day: 0.03% of the clock.
* The uncapped re-read of a value at the run cap (filter + 6): never in
  either 1,200, and rarer than a NEAR by the cap's six conditions.
* A discovery's verification and certificates: seconds to a minute,
  expected (`HostCost.expect`), once per find.

Every per-value host step in the loop runs inside
`huntlib.hostcost.HostCost.item`, and the selftest's slow-step drill checks
that a slow one is announced by its b.

### The proof cost, and the ceiling (rule 5h)

(b+1)^p − b^p − 1 = p · b · (b+1) · (b² + b + 1)^e · E(b), e = 2 when
p ≡ 1 (mod 6). The BLS75 route, measured on values near each height (b, b + 1
and b² + b + 1 factored completely; a prime factor of b² + b + 1 past
3.3·10²⁴ proved one level down and carried as a subproof; E(b) through the
bounded factor_partial):

| p | b = 3·10¹⁹ (A216668 a(24)) | b = 3·10²¹ (A216666 a(11)) | b = 10³⁹ (the ceiling) |
|---|---|---|---|
| 2 | — | — | share 1.00, Theorem 1, 0.1 s |
| 11 | 0.515, Theorem 1, 1.7 s | 0.484, Theorem 5, 3.0 s | 0.269, NONE |
| 13 | 0.524, Theorem 1, 2.2 s | 0.538, Theorem 1, 2.1 s | 0.222, NONE |
| 17 | 0.255, NONE | 0.269, NONE | — |
| 19 | 0.374, Theorem 5, 3.9 s | 0.351, Theorem 5, 3.7 s | 0.138, NONE |

("share" is log F / log N, F the fully factored part of N − 1.) So at
every height the campaigns can reach in years, the values at p ≤ 13 and
p = 19 are proved in a few seconds each, and p = 17 and every p ≥ 23 have
no N − 1 route at any height — a structural fact of the shape, not of the
height. Near the ceiling b² + b + 1 is 78 digits, past what the bounded
factoring takes apart, and the p = 11, 13, 19 routes go too. The first
pass of this table factored b² + b + 1 with the bounded factor_partial and
left p = 13 at b = 3·10²¹ at share 0.30 — no route; it is now factored
completely below 10⁶⁰ (`QUAD_FULL_BELOW`), and its prime factors past the
bound are given their own proofs (`big_prime_subproofs`).

**What the general prover would cost could not be measured here**: neither
python-flint (APR-CL) nor PARI/gp is installed, and the python-flint copy
an earlier session (cyclotomic-ladders, 2026-10-25) unpacked into its
scratchpad has since been cleared — only empty folders remain. That
project's measurements of FLINT's `fmpz_is_prime` on this machine were
0.1 s at 168 digits, 1.5–2.5 s at 335–386 and 24.7 s at 670. The values
this project would hand it: 170–346 digits for the free terms; 343 digits
(p = 23) at A216666's a(9), 524 (p = 29) at a(10), 645 (p = 31) at a(11);
about 950 (p = 61) at A216668's a(18) and 1,710 (p = 89) at a(24). On the
usual fourth-power growth of APR-CL that is seconds to a minute per value
through a(11), a couple of minutes at A216668's a(18), and roughly a
quarter of an hour at a(24) — an EXTRAPOLATION, to be replaced by a
measurement once a prover is installed. At the 10⁴⁰ ceiling the largest
value is 3,500 digits (A216668, p = 89), hours by the same extrapolation.

**The ceiling stays huntlib's K_CEIL = 10⁴⁰** (the repository's default;
rule 5h allows a lower one only with a measurement saying why). Nothing
measured says why: the values without an N − 1 route are without one at
every height, so a lower ceiling would prove nothing more, and the
campaigns cannot reach 10³⁰ in any useful time (A216666's a(12), median
3.9·10²⁴, is out of reach). What the ceiling's height does decide is the
general prover's cost per discovery, which is hours at worst. The decision
the owner faces is not the ceiling but the prover: python-flint (APR-CL, a
pip package; a proof but no checkable certificate) or an ECPP program (a
certificate anyone can check, slower). Until then every record lists its
unproved values.

### score.py measured the battery, not the engine — fixed

The first full score.py read every fingerprint correctly but the shapes at
1.1x to 5x under their fresh-process rates (D18 1.2·10¹² against 5.9·10¹²
b/s, S9 1.5·10¹³ against 3.4·10¹³): the gates leave a heavy Python heap
(kill-set caches, survivor lists, the host tables of dozens of engines) and
the cyclic collector walked it between launches. score.py now collects,
freezes the heap (`gc.freeze()`) and empties CuPy's pools after the gates;
the shapes then read their fresh-process rates within 1%. The campaign
never runs a gate. (Worth checking in the other projects' score.py: the
same structure, unmeasured.)

### What round 1 owes (the termination test is not done)

OPTIMIZATION.md Part 3 has not been run. Every phase above 5% at the
day-long filters still needs an optimization, a roofline or a structural
argument:

* **Nsight Compute** (Rule 1a) on the sieve kernel, the generated tail
  rounds and the Fermat kernels at A216666 n = 11 — not run this session.
  The Fermat kernels at 14 to 28 limbs are fully unrolled; whether they
  spill is the first question (`ncu --kernel-name prp_stage`).
* **The window's constants** (BIT_SURV, the width curve, the table budgets)
  and the **tail's** (TAIL_LITERAL, TAIL_ROUND_DROP) are cyclotomic-ladders'
  measurements on strong, forced wheels; nothing of them was re-swept on
  these weak ones.
* **The Fermat stage** (35–40% of the device): a squaring-specialised
  Montgomery product, and a stage that tests p = 5 before p = 3 on the
  values most likely to fail — both unpriced.
* **The four-form stage** is a priced, declined option (above): 1.12x at
  A216666 n = 11 for five to ten host cores.

## Gate battery at the end of round 0

`python launch.py --selftest`: 61 rows green (182 s warm; the first battery
after the kernels' first compile took several minutes longer). `python
score.py`: every gate green, every fingerprint reproduced, SCORE
132,111,633.

## Round 1 — engine v2 / planner p2: the sieve set by value, the Fermat stage beside the sieve (2026-11-23)

**The target (rule 3b), unchanged from round 0:** A216666 n = 11 (a(11):
median 9.2 months at the start of the round) and A216668 n = 24 (a(24):
median 22 days). Every measurement below names its filter; the three other
campaign filters (A216666 n = 9 and 10, A216668 n = 18) were checked for
every shipped change. **Result: 1.415x at A216666 n = 11 and 1.511x at
A216668 n = 24**, paired against engine v1's own configuration on the same
code (which reproduces v1's frozen SCORE fingerprint exactly); 1.328 /
1.329 / 1.692 at A216666 n = 9 / 10 and A216668 n = 18.

**The harnesses** (session scratchpad, not committed — CLAUDE.md rule 9):
`prof.py` (round 0's, extended: per-kernel CUDA events with the launch
synchronised, plus the queue count entering every tail round and every
Fermat form), `overlap.py` (the same events DURING a pipelined sweep, no
per-launch sync — what each kernel costs under contention), `ab.py` (arms =
module constants + engine keywords, built exactly as `launch.py` builds the
campaign engine, interleaved rounds, the stream's count and xor checked on
every run; timed in STEADY STATE, from the first launch's results to the
(N+1)-th's, because a caller that breaks off early leaves one launch in
flight with two buffers and two with three), `twoeng.py` (two independent
engines swept at once: the concurrency ceiling), `knap2.py` (CPU only: the
sieve set as a knapsack with the measured costs), `parity.py` (hash-test
parity against the CPU engine before G24 existed), `warm.py` (one engine
per planned filter, to put NVRTC's compiles in CuPy's cache in short
commands), `rowtime.py` (the selftest's rows one by one, timed),
`freeze_shapes.py` / `v1shape.py` / `anchab.py` (score.py's shapes:
fingerprints, v1 against v2 under both timing protocols, the anchors
interleaved), `gatemem.py` / `aftergates.py` (CuPy's pool after each gate,
and an anchor's rate after the gates).

### What Nsight Compute said at A216666 n = 11 (Rule 1a)

The phase split first, the planned v1 engine at b = 3·10²¹, 16 launches
synchronised: 93.5 ms a launch — the sieve kernel 35.7 ms (38%), the
Fermat stage 33.9 ms (36%: p = 5 10.96, p = 3 8.35, p = 11 6.19, p = 2
5.94, p = 7 2.42), the generated tail rounds 23.9 ms (26%). The tail's
first queue held 155.86 M entries against a cap of 155.93 M, but its
spread over launches was ±15,000 and no launch overflowed (OPTIMIZATION.md
2.16 ruled out); 17.56 M values entered the Fermat stage a launch and
5.63 M / 904 K / 72.8 K / 3,912 / 123 passed p = 2 / 3 / 5 / 7 / 11.

* **The sieve kernel**: 3 blocks an SM (29.45 KB of shared memory; the
  registers allow 4), IPC 2.04, issue slots 51% busy, LSU 66%, ALU 58%,
  shared-memory data pipe 62% with 2.5-way bank conflicts, 0.8 eligible
  warps a scheduler: LATENCY-bound at its occupancy, no pipe near a peak.
  11.6% of the stall samples were instruction fetch ("no instruction"): the
  kernel was 14,032 SASS instructions, 224 KB. SASS census by barrier
  segment: the window and extraction 64.7% of executed instructions (funnel
  shifts 32%, LOP3 20%, LDS.64 14%), in-block round 1 24.5% (7,778
  instructions), round 2 9.1%.
* **The Fermat kernels** p = 2, 3, 5: bound by the FMA-heavy pipe (71–80%
  of peak; math-pipe throttle the top stall), 31–78 registers; p = 5 also
  lost 33% of its samples to instruction fetch. p = 11: 162 registers and
  4% of issue slots busy — 3,912 values a launch, one warp an SM, every
  Montgomery product a dependent chain: pure latency, 6.2 ms.
* **The tail rounds**: rounds 0–3 healthy (48–60 registers, 65–80%
  occupancy, IPC 2.45, L1 hits 96–98%); round 5 — 358 primes in one
  generated kernel — 255 registers, 17% occupancy, L1 hits 84%, L2 54%,
  IPC 1.5: 8.5·10⁻¹³ s a test against 5.8·10⁻¹³ in round 0. A test is 14.7
  thread-instructions: about 9 a prime (lazy 32-bit reduction, a 64-bit
  address, the table load, shift, mask, predicate) and 5 of the pack's
  64-bit Barrett step shared between its two or three primes.

### The sieve set by value — the round's main lever (shipped, engine v2)

**The cost model** (`knap2.py`, measured costs): a per-candidate test
6.0·10⁻¹³ s; the Fermat stage 1.93·10⁻⁹ s per value entering it. So a sieve
prime is worth its test while it kills more than ~1/3000 of what it tests
— and what a kill saves depends on the FORM it kills through: the stage
tests 2b + 1 first and cheapest, so a b that a prime kills through 2b + 1
would have failed the stage's first test anyway (a kill there saves 525
tests' worth), while a b killed through a form the stage never tests saves
the whole stage (3,000). Every odd prime kills 2b + 1's residue, and about
a fifth of primes kill nothing else: those past ~600 cost more than they
save, while primes past 8192 with p | q − 1 for many sieved p (30031
kills 35 residues: three tests' worth) were never sieved. The depth was the
wrong cut.

**Why a deeper sieve had measured a tie** (round 0: PRP_Q2 16384 at 1.006):
measured at q2 = 16384 with every prime, the Fermat stage fell 33.9 → 18.9
ms a launch (7.9 M values instead of 17.6 M) and the tail rose 23.9 → 39.4
ms — its deepest round at 2.2·10⁻¹² s a test, because a generated round
reads each prime's kill pattern over [0, 2q): 2q bits, 4 KB at q = 16384,
and a few hundred of them leave L1. **The fix is the HASH TEST**: a prime
past HASH_FROM = 8192 is tested through an exact perfect hash — its
remainder made exact, the slot (r · H mod 2³²) >> (32 − s) with an odd H
searched (deterministically, from a fixed stream) so that the map is
injective on the prime's kill set, 2^s ≥ 2 × the kills, u16 slots holding
the killed residue or 0xFFFF — a few hundred bytes a prime. Hashed primes
never enter the window or the in-block rounds (the first 164 places of the
test order).

**The value rule** (`difference_search.select_primes`, read by both
engines): a prime to 89 is always sieved; past it, a prime is sieved when
its kills, each weighted by its form's rank among the sieved forms (0.18,
0.42, 0.75, 0.82 for the four cheapest — the stage's measured cost up to
that form over its whole cost — and 1 for the rest), divided by q, reach
SIEVE_TAU. The CPU engine sieves exactly the same set, so G9's discipline
carries over (G24).

Paired at A216666 n = 11, b = 3·10²¹ (16 launches × 3 rounds; the plan's
wheel throughout):

| sieve set | ratio to every prime ≤ 8192 |
|---|---|
| every prime ≤ 16384, hashed past 8192 | 1.106 |
| every prime ≤ 32768, hashed | 1.019 |
| **value-selected ≤ 32768, hashed** | **1.253 [1.237, 1.258]** |
| threshold × 0.6 / × 1.5 / × 2.2 | 0.990 / 0.993 / 0.985 of the line above |
| hashing from 4096 instead of 8192 | 1.003 |
| value-selected ≤ 49152 / ≤ 65536 (×1.4 threshold) | 0.993 / 0.968 (1.005) |

Its phase split: the Fermat stage 33.9 → 15.5 ms a launch (5.40 M values
in), the tail 23.9 → 23.7 ms. What the set changes besides the rate: WHICH
b reach the stage, so the stage's stream (and with it the census, which
counts the stream's runs by length, and the near-miss lines) is a
different one at equal coverage — never a find, which needs every form
prime and so survives any sieve. No campaign had run, so there is no census
to reconcile. **At every campaign filter**, the v2 set
against the v1 set, paired: A216666 n = 9 **1.236**, n = 10 **1.216**,
n = 11 1.253, A216668 n = 18 **1.529**, n = 24 **1.316**. Parity: G24 (new)
and `parity.py` before it — the GPU stream with hashed primes == the CPU
engine on populated windows, narrow and wide, past 2⁶⁴, with and without a
selection.

### The Fermat stage on its own stream (shipped)

The stage of launch i now runs on a second CUDA stream, waiting on an
event for launch i's tail, beside the sieve of launch i + 1 (the sieve
kernel leaves ~24 K registers and 36 of 48 warp slots an SM free). Both
streams are blocking streams, so a caller's null-stream synchronise still
waits for them. Paired: **1.069x at A216666 n = 11 and 1.057x at A216668
n = 24** in round-0 timing; **1.093x** at n = 11 in steady-state timing
(the earlier figures paid one extra launch in the timer). THREE LAUNCH
BUFFERS (two launches in flight, PRP_BUFFERS) over two: 1.006. Declined:
the sieve's stream at a higher CUDA priority, 0.983–0.988 with two, three
or four buffers (the stage is starved and the pipeline serialises on it).
**Measured under overlap** (`overlap.py`, final engine): the sieve kernel
36.3 ms a launch against 35.5 synchronised, the tail 30.5 against 22.2 —
the stage's FMA-bound kernels (p = 2, 3, 5) contend with the tail more than
with the sieve — and the wall clock (67.4 ms) is the main stream's (66.8):
the main stream is the critical path, the stage's 13.6 ms is mostly hidden
and its contention costs ~9 ms.

### The squarings by a squaring (shipped)

Every step of the base-2 chain squares; `mont_sqr` (separated operand
scanning on NL limbs: NL(NL − 1)/2 cross products, doubled, NL squares,
then the NL² of the reduction with each round's carry deferred to the next)
against CIOS's 2·NL². Kernel-only (synchronised, per kernel, at n = 11): p = 11 (23 limbs)
6.55 → 3.62 ms, p = 5 (10) 3.18 → 2.53, p = 7 (14) 1.57 → 1.27, p = 3 (5)
2.67 → 2.53, p = 2 (3) 1.90 → 1.96 — **the stage 1.33x**, p = 2 excluded
(PRP_SQR_MIN_NL = 4: at 3 limbs the doubling pass costs what the three
saved products save). End to end **1.007 at n = 11 and 1.009 at A216668
n = 24** (the stage is hidden behind the sieve) — two numbers, as
INNOVATION.md asks. G23 pins it against Python's pow at every limb count it
compiles and now requires both routes (the square and CIOS) exercised.

### The sieve kernel's code size (shipped)

The in-block rounds' item loop was fully unrolled — every thread's MAXIT
queue items (capacity / 128: 16 at n = 11) times the round's prime list:
16 copies of 38 primes, 7,778 SASS instructions in round 1. Not unrolled
(ROUND_ITEM_UNROLL = 1): **1.024 [1.021, 1.024] at n = 11, 1.017 at
A216668 n = 24, 1.009 at A216666 n = 10** (unrolled twice: 1.022 / 1.017 /
1.001). But the SCORE1L anchor — a 30030 wheel, three items a thread — ran
**1.30x slower** rolled up, so a round whose unrolled body is small stays
unrolled (ROUND_UNROLL_BUDGET = 256 items × primes): it gives SCORE1L back
(1.296 of rolled; fully unrolled 1.302) and ties at every campaign filter
(1.000, 0.998, 0.998).

### The tail's shape, re-swept on v2 (TAIL_ROUND_DROP shipped)

* **TAIL_ROUND_DROP 0.7 → 0.8** (shorter rounds, more compactions): 1.011
  / 1.033 / 1.033 at A216666 n = 11 / 10 / 9, 1.028 / 1.038 at A216668
  n = 24 / 18 (0.75: 1.011 / 1.018 at the openings; 0.85 0.997, 0.5 0.845
  at n = 11). It costs the SCORE6 anchor (a survivor-heavy n = 6 sieve
  stream, no campaign's configuration) 6% (0.7 reads 1.063 there): the
  campaign filters decide (rule 3b).
* **A cap on primes a round** (TAIL_ROUND_PRIMES_MAX): on v1 a cap of 192
  read 1.022 [1.013, 1.034] (64: 1.030, 128: 1.029 at 16 × 3); on v2
  0.993. Off. **`__launch_bounds__` on the generated rounds**
  (TAIL_MIN_BLOCKS): 3 blocks 1.002 over the cap alone, 0.920 at 256
  primes a round (spills). Off.
* **Where the hashed primes go**: after every unhashed prime (the
  prototype) or in strength order past the first 164 places (HASH_LAST
  False): **1.010 at n = 11 and at A216668 n = 24**, shipped — and the
  q2 = 65536 anchors stopped testing their strong hashed primes after
  thousands of weak unhashed ones (SCORE2L's generic round had gone 1.3 →
  17.5 ms).

### Re-swept on v2 and kept

* **SIEVE_TAU**, measured first as 6.0·10⁻¹³ / 1.93·10⁻⁹ = 3.1·10⁻⁴, moved
  to **6.2·10⁻⁴** once the stage was cheaper and hidden: twice the
  threshold read 1.005 / 1.022 / 1.010 at A216666 n = 11 / 10 / 9, 1.0065 /
  1.021 at A216668 n = 24 / 18; three times 1.011 / 1.002 / 1.023 at n = 10
  / 9 / A216668 18; half 0.975 at A216668 n = 24. **The depth** past the
  move: 16384 reads 0.953 at n = 11 and 0.931 at A216668 n = 24.
* **BIT_SURV** (the window's depth): 0.0045 1.005, 0.009 0.972 at n = 11.
  **K2_ROUND_PRIMES_MAX**: 32 1.005, 96 0.985. Flat; kept.
* **The occupancy floor** (OCC_MIN_BLOCKS4): 4 halves the block's
  second-level residues at n = 11 (23.2 KB, 96 registers, 4 blocks): 1.031
  alone, 1.028 on top of the rolled item loop (whose gain it shared: both
  halve the code a block runs); 0.985 at n = 10 and 0.939 at A216668
  n = 24, where the shape search lands on 2 blocks. Kept at 3: a per-filter
  table for 0.4% at one filter is not worth its gate. 5: 0.933. **The
  window patterns read through L1** instead of shared memory (PAT_SHARED
  False): 4 blocks, 0.920.
* **The wheel**: the planner's five best wheels at n = 11 by its own
  objective, measured — its pick 1.000, +67 (wide record, pb 160) 0.981,
  without 19 0.966, then 0.863 and 0.769, in the order its model ranks
  them. The plan stands, and it is p1's at every campaign filter.
* **PRP_FORMS** (with the stage on its own stream): 6 forms 0.996 (the host
  would get ~1.7 values a launch instead of 52 — at 5 it needs a fifth of a
  core, so the device decides), 4 forms 1.004 for ~22,000 values a second
  to the host (several cores, for days): kept at 5 (CLAUDE.md 5f).
* **PRP_GRID** 512 / 1024 / 4096: 1.002 / 0.999 / 0.998. Kept at 2048.

### Priced and declined

* **The tail overlapped with the next launch's sieve** (a third stream,
  the tail's queues per launch buffer: +2.1 GB a buffer): its ceiling
  measured first — TWO independent engines swept at once from one thread,
  each on its own streams and buffers, run **1.05x** the rate of one (1.051,
  1.052, 1.048). At most 5% for 2–4 GB more of the card; declined.
* **Testing p = 5 before p = 3** (round 0's open question): by the measured
  per-value costs (p = 3 1.47·10⁻⁹ s on 2.15 M values, p = 5 9.4·10⁻⁹ s on
  330 K), p = 5 first would cost ~20 ms a launch against ~6.3 now. The
  stage's order (cheapest first) stands by arithmetic.

### The battery, the benchmark protocol and the card's memory

* **score.py timed launches it did not count.** A campaign shape stopped
  the sweep after 16 results and closed it with the next launches still in
  flight — 17 timed for 16 under v1, 18 under v2's three buffers. `sweep`
  now takes `max_launches` (stop enqueueing, drain) and score.py times
  exactly its 16 (G24 checks a bounded sweep == the first launches of an
  unbounded one). Rule 4's separation at the SCORE shape: v1's
  configuration reads 1.321·10¹⁴ b/s by the old protocol (its frozen SCORE
  131.8 M) and 1.405·10¹⁴ by the new (**the protocol alone: 1.063**, 17/16);
  v2 1.766·10¹⁴ by the old and 1.987·10¹⁴ by the new. **The engine alone:
  1.415** under the new protocol (the steady-state A/B's figure); 1.337
  under the old, which charges v2 one more launch in flight than v1.
* **The gates walked the card to 24 GB.** Every campaign engine allocated
  its 2.1 GB tail queues at construction, G18 builds eleven engines only to
  read what they compile to, and G23's shallow Fermat-stage engines size
  their buffers analytically (gigabytes at q2 = 512) — and v2's per-buffer
  stage arrays made those three times larger. CuPy's pool cached it all
  (29.5 GB after G23), WDDM paged, and every engine timed after the gates
  in the same process ran 2–3x slow (an anchor 9.7·10¹¹ → 4.1·10¹¹ b/s;
  the battery 271 s). Fixed: the tail queues are allocated on the first
  launch, the stage's index ping-pong and counts are one set (the stages of
  successive launches run in order on one stream, so they never overlap),
  G23 and G24 release each case's engines. The peak after those gates 24 →
  10.6 GB, the anchor holds 9.35·10¹¹, **the selftest 271 → 194 s**,
  score.py 2m16s, and the anchors read their v1 rates again (SCORE2L
  1.03·10¹², SCORE1L 1.56·10¹², SCORE6 3.56·10⁹).
* **The first battery after a kernel change** compiles every distinct
  engine once (NVRTC) and does not fit rule 0's five minutes; `warm.py`
  (one engine per planned filter) and the selftest's rows run group by
  group fill the cache in short commands first.

### The termination table at A216666 n = 11, b = 3·10²¹ (OPTIMIZATION.md Part 3)

Per launch (6.87·10¹⁰ candidates), the final v2 engine; the wall clock
67.4 ms pipelined, of which the main stream is 66.8 ms:

| phase | share | verdict |
|---|---|---|
| sieve kernel: the window and extraction | ~23.6 ms, 35% | **Unsearched at the instruction level** (owed: INNOVATION.md Part 2 on this window at this filter — it was run on the kernel's ancestors in power-ladders and polynomial-runs, not here). What is measured: latency-bound at 3 blocks an SM (above); every way of buying occupancy priced (floor 4: 1.031, sharing its gain with the rolled item loop, and losing at two filters; floor 5 0.933; patterns via L1 0.920); BIT_SURV flat; concurrency's ceiling 1.05. |
| sieve kernel: the in-block rounds | ~12.3 ms, 18% | Optimization: the code-size fix (1.024, with its budget for small rounds); K2_ROUND_PRIMES_MAX flat. ~12 instructions a test. |
| tail rounds | 30.5 ms under contention (22.2 alone), 45% | Optimization: the value rule and the hash test (1.253 of the round's 1.415), TAIL_ROUND_DROP 0.8, the merged order; a test is 14.7 instructions, ~9 of them per prime and essential to a table test, ~5 the pack's 64-bit step (packs are capped at 2–3 primes by the 32-bit lazy bound). Overlap with the next sieve priced at ≤ 1.05. |
| Fermat stage (its own stream) | 13.6 ms alone, ~9 ms exposed as contention | Optimization: its own stream (1.093), the square (1.33x kernel-only), three buffers; priority, grid and form count measured and kept. A free stage would be worth at most ~1.17x (67.4 ms against the main stream's 57.7 alone); fewer values (a lower SIEVE_TAU) is the only lever left on it and the threshold is flat. |
| host | ~52 values a launch (~770 a second) | Under a core at the 2x margin; the rare paths of round 0 unchanged and rarer (fewer values). |

The table does not say "done": the window's instruction-level pass is owed,
and the tail's ~5 instructions a test of pack arithmetic and the stage's
contention are the priced levers left.

### Clocks at the v2 rates (the model's quantiles, README)

| term | rate (b/s) | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|
| A216666 a(9) | 4.75·10¹³ | 23 s | 77 s | 3 min | 6 min |
| A216666 a(10) | 1.44·10¹⁴ | 3.1 h | 9.7 h | 24 h | 1.9 days |
| A216666 a(11) | 1.99·10¹⁴ | 60 days | 6.1 months | 15 months | 2.4 years |
| A216668 a(18) | 1.07·10¹³ | 3 min | 10 min | 26 min | 51 min |
| A216668 a(24) | 2.39·10¹³ | 4 days | 14 days | 34 days | 64 days |

(v1: a(10) 13.7 h, a(11) 9.2 months, A216668 a(24) 22 days median.)

## Gate battery at the end of round 1

`python launch.py --selftest`: **62 rows green in 194 s** (warm; G24 new:
the value rule against killed_residues, every hashed prime of both
day-long engines emulated exhaustively from the device tables, the test
order, the selected stream == the CPU engine on the same set, the Fermat
stage over it, and the launch bound). `python score.py`: every gate green,
every fingerprint reproduced — the five campaign shapes re-frozen for v2's
sieve set (BENCHMARKS.md), the three anchors unchanged — **SCORE
198,578,537**.
