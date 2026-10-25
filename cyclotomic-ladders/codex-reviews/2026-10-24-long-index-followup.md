# Cyclotomic-ladders: shortening the long A072942 searches

> **Authorship:** Codex (OpenAI), 2026-10-24. Static follow-up requested
> while the owner was running n = 60. This is a report for Claude's later
> implementation and testing. Candidate-count reductions are proved
> arithmetic; runtime gains are unmeasured. No project code, campaign
> state, evidence, or machine settings were changed.

## Assessment

There is a worthwhile structural experiment left: replace weak wheel
primes with stronger cyclotomic primes above the planner's hard ceiling
of 89. Concrete substitutions below reduce the number of generated
candidates by factors of 1.37–2.13 at the long indices, with a smaller
1.18 option for n = 60. Some also shorten the full coverage segment.
These are illustrative feasible arithmetic configurations, not proven
optimal wheels or measured speedups.

There is no supported claim here that an available change will turn all
of the remaining searches into a few hours. At the stored model medians,
n = 84, 96, and 90 require approximately 6.5x, 10.1x, and 11.3x total
speedups to finish within 24 hours. The existing round already removed
several expensive kernel costs. For the larger goal, the research target
is a different way of enumerating strong-wheel candidates while completing
short numerical intervals. That redesign is much less certain than the
wheel substitutions and needs an operation-count and memory case before
implementation.

The n = 60 checkpoint is consistent with the measured engine rate. It
does not reveal a hidden factor-of-several campaign overhead to recover.

Read this with the [experiment plan](2026-10-24-long-index-validation-plan.md),
[finding ledger](README.md), and [original review](2026-10-23-static-review.md).
The governing method remains [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

## Snapshot and interpretation

| Item | State used in this report |
|---|---|
| Repository HEAD | `35f48897eac28a5ec0ac4f60c3ce2e3a92d8708c` |
| Working tree | Parent `CODEX_REVIEWS.md` and `README.md` modified; this entire project untracked |
| Engine history | Claude's round 1, engine v2, 2026-10-23; recorded in OPTIMIZATION_LOG.md and BENCHMARKS.md |
| Active data snapshot | n = 60 checkpoint saved 2026-10-24 00:30:27 local time |
| Other long-target checkpoints | None found for 72, 84, 96, or 90 at inspection |
| Method | Static source/data reads, mathematical derivation, lightweight arithmetic, primary-source lookup |
| Excluded execution | No imports or execution of project engines, models, launchers, tests, searches, benchmarks, profilers, CUDA compilation, or GPU queries |

The commit alone does not identify these untracked source files; hashes
are recorded below. The report is a timestamped observation, not a live
status display. Some original README/RESULTS frontier text predates the
campaign and must not override newer checkpoint/evidence data.

The problem is to find the **least** x > 2 for which every Phi_d(x), d | n,
is prime. Finding a candidate in an arbitrary residue class is therefore
insufficient: every smaller admissible x still needs coverage. This is
the definition in [OEIS A072942](https://oeis.org/A072942).

### Existing improvements are already included

Round 1 halved the window pattern, enabled the pairs layout and packed
offset tables, generated the last tail round, reordered the device forms
by degree, and remeasured width, depth, and table budgets. At n = 60 the
recorded improvement was 1.23–1.37x. The other long filters received
opening measurements; 72, 84, and 96 did not receive the same detailed
phase investigation as 60 and 90. See [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md),
round 1, especially the final phase table and section 5g.

The original negation-folded generic-tail proposal, CYL-002, should not
be repeated unchanged: that generic tail no longer runs at the campaign
filters. Generated tables already have high recorded L1 hit rates.
Known-factor-first certificates, CYL-003, can shorten certification but
do not shorten a days-long search for a candidate. The current disposition
ledger records these distinctions.

## How much improvement is needed?

The table uses exact medians in [model_results.json](../model_results.json)
and the round-1 steady-state rates in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md).
The third column includes completion of the existing segment containing
the model median. It is a fixed-rate scenario, not a newly conditioned
prediction, a probability guarantee, or a new measurement.

| Index | Median-location work time | Through existing segment containing median | Speed factor for 24 h | Speed factor for 6 h |
|---|---:|---:|---:|---:|
| 72 | 53.54 h | 53.80 h | 2.24x | 8.97x |
| 84 | 156.40 h | 156.87 h | 6.54x | 26.15x |
| 96 | 238.65 h | 243.22 h | 10.13x | 40.54x |
| 90 | 269.45 h | 270.14 h | 11.26x | 45.02x |

These factors assume the existing coverage segmentation remains fixed.
A changed wheel requires recalculating segment completion, not simply
dividing these clocks by a candidate-count factor. Proof time is extra.
The stored Q1–P90 work-time ranges are broad: 17.7–240.5 h, 51.1–712.9 h,
78.3–1082.8 h, and 87.8–1232.6 h respectively. CYL-009's model calibration
and conditioning concerns remain; the table is useful for sizing the
required engineering gain, not promising dates.

At n = 60, the stored median is 3.352915912687866e25. Dividing by the
recorded 6.1e20 x/s gives 15.27 h; using the checkpoint-derived cumulative
rate of about 5.49e20 gives about 17 h. The source of the discrepancy in
the pasted explanation is largely the choice of rate, not missing work.

### What the live checkpoint actually establishes

At the timestamp above, n = 60 recorded j = 0, u = 18,590 of 26,047
launches, and elapsed time 1,376.9225 s. The segment spans
1,058,888,978,151,626,673,891,840 units of x. Using its own progress
denominator gives approximately 7.55739e23 equivalent x-units of work,
or 5.48861e20 x/s. That agrees reasonably with the stored 5.5–6.1e20
engine readings; launch sizes and startup costs make this an estimate.

The official completed cursor was still k = 3. The exception-zone marker
showed that the host had already covered the small zone through 8193,
but **no GPU segment had closed**. The fractional work above is spread
across residue classes and must not become a contiguous searched floor.
The first segment's estimated total duration was 32.15 minutes, with
about 9.2 minutes left at that historical snapshot. Six pending run-11
records were not n = 60 discoveries.

## CYL-011 — choose wheel primes using the cyclotomic root counts

**Classification:** new structural finding; exact candidate-density
calculation, unmeasured runtime proposal. Relevant source:
[cyclotomic_gpu.py](../cyclotomic_gpu.py), `WHEEL_TOP` at 270,
`_wheel_value` at 430, `_split_levels` at 466, `wheel_candidates` at 547,
and `plan` at 737. `window_depth` at 688 already considers the stronger
primes outside the wheel.

### Why the current cutoff misses valuable primes

For a prime q, the factorization

    product_{d | n} Phi_d(x) = x^n - 1

means that the forbidden residues are exactly the roots of x^n = 1 in
F_q. The nonzero residues form a cyclic group, so there are

    g_n(q) = gcd(n, q - 1)

distinct forbidden residues. This remains true if q divides n; repeated
polynomial factors do not create additional distinct roots. Zero is
never forbidden. After x = U*t, each q not dividing U has an invertible
change of coordinates and the same root count.

Thus a nonforced wheel prime keeps q - g_n(q) classes. For distinct
wheel primes CRT makes their conditions independent over the complete
period. Its candidate density in t is exactly

    D(Q) = product_{q in Q} (q - g_n(q)) / q.

The comment beside `WHEEL_TOP = 89` says larger primes have poor value
density. That inherited rationale fails for this family: gcd(n, q - 1)
has large spikes above 89.

| Index | Example q above 89 | Forbidden classes | Fraction rejected |
|---|---:|---:|---:|
| 60 | 181 | 60 | 33.15% |
| 72 | 109 | 36 | 33.03% |
| 84 | 127 | 42 | 33.07% |
| 96 | 193 | 96 | 49.74% |
| 90 | 181 | 90 | 49.72% |

These exclusions are **already applied by the later sieve**. Moving them
into the wheel reduces generation work, not the final set of valid
candidates. Removed weak wheel primes must return to the sieve. The
proposal neither invents an additional mathematical exclusion nor claims
that the present search is incorrect.

The exceptional equality case is unchanged: a cyclotomic value equal to
q is prime despite divisibility by q. All proposed primes are below the
existing q2 = 8192. Preserve the brute-force exception zone through
q2 + 1 and use the sieve only above it, as specified in
[cyclotomic_search.py](../cyclotomic_search.py), `k_floor`/`zone` at 160–180.

### Concrete substitutions worth testing

Start from each current wheel in the round-1 section 5g table. Remove the
listed primes, insert the listed primes, and retain all others. The
candidate reduction is D(old)/D(new). Period ratios apply equally to W'
and W = U*W' because U is unchanged.

| Index / option | Remove from wheel | Add to wheel | Exact-density candidate reduction, rounded | New/old period |
|---|---|---|---:|---:|
| 60, short period | 23, 29 | 181 | 1.1774x | 0.2714 |
| 60, balanced | 23, 43, 71, 73 | 101, 181, 241 | 1.4008x | 0.8595 |
| 72 | 23, 29, 43, 67 | 97, 109, 181 | 1.5272x | 0.9959 |
| 84 | 23, 41, 73 | 113, 127 | 1.3676x | 0.2085 |
| 96, balanced | 23, 43 | 193 | 1.5632x | 0.1951 |
| 90, balanced | 23, 43, 71 | 181, 271 | 2.0101x | 0.6985 |
| 90, short period | 17, 23, 43, 71 | 181, 271 | 1.7736x | 0.0411 |
| 96, aggressive | 23, 29, 43 | 193, 241 | 1.6827x | 1.6217 |
| 90, aggressive | 17, 23, 43, 71 | 181, 271, 541 | 2.1276x | 22.2301 |

For example the short-period n = 60 option has the exact ratio

    ((21/23)*(25/29)) / (121/181) = 1.177407164...

and period ratio 181/(23*29). The n = 72 option is particularly useful
as a first experiment: roughly one-third fewer generated candidates at
almost the same period, on a target without an existing checkpoint.
The balanced 84/96/90 options also shorten the period. The aggressive
90 option must carry its substantial completion-latency price explicitly.

Here are explicit level splits, so these are reviewable constructions
rather than a request to see whether a larger cutoff happens to work.
Write M_i for each level's modulus and R_i for its allowed-residue count.
The source's combined second modulus is M_2*M_3.

| Index / option | Level 1 | Level 2 | Level 3 | R_1, R_2, R_3 |
|---|---|---|---|---|
| 60 short | 17,19,37,41 | 43,181 | 71,73 | 88725; 4477; 3721 |
| 60 balanced | 17,19,29,37 | 41,181 | 101,241 | 105625; 2541; 14661 |
| 72 | 17,31,41,61 | 11,181 | 97,109 | 363825; 1305; 5329 |
| 84 | 11,17,19,31,37 | 61,71 | 113,127 | 950625; 2793; 7225 |
| 96 balanced | 11,19,29,31 | 37,41,61 | 73,193 | 73125; 40425; 4753 |
| 90 balanced | 5,13,17,37,181 | 41,61 | 73,271 | 544635; 961; 9955 |
| 90 short | 5,13,37,41,61 | 73,271 | 181 | 383439; 9955; 91 |
| 96 aggressive | 19,37,41,193 | 11,31,241 | 61,73 | 1040325; 43425; 2401 |
| 90 aggressive | 5,13,37,41,61 | 73,541 | 181,271 | 383439; 24805; 16471 |

| Index / option | M_1 | M_2*M_3 | W' |
|---|---:|---:|---:|
| 60 short | 489991 | 40339289 | 19765888556399 |
| 60 balanced | 346579 | 180634561 | 62604145516819 |
| 72 | 1318027 | 21050843 | 27745579446761 |
| 84 | 4075291 | 62154181 | 253296374441671 |
| 96 balanced | 187891 | 1303753793 | 244963603920563 |
| 90 balanced | 7400185 | 49477283 | 366141047497355 |
| 90 short | 6014905 | 3580723 | 21537708676315 |
| 96 aggressive | 5562839 | 365951993 | 2035732018788127 |
| 90 aggressive | 6014905 | 1937171143 | 11651900393886415 |

Every row satisfies M_1 < 2^32, M_2*M_3 < 2^32, R_1 < 2^21,
R_2 and R_3 < 65536, W' < 2^63, and 257*W' + 8192 < 2^64.
These are the documented integer and narrow-record budgets at pb = 256.
They do not establish favorable memory use, successful construction,
correct kernel execution, or that the existing split heuristic will
choose the listed partition. Several partitions are intentionally
noncontiguous in sorted prime order.

The current planner considers nested greedy prefixes ranked by
`-log(keep)/log(q)`, not all subsets. Increasing the ceiling is therefore
necessary to make these primes available but does not establish that
the planner will consider a good substitution. Retain the current plan
as a baseline, seed these explicit alternatives, and compare a bounded
set of one/two/multiple-prime exchanges under the actual representation
and completion constraints. Do not replace one arbitrary cutoff with a
claim of global optimality.

### What the ratios do and do not buy

Moving strong primes into the wheel removes them from the window's
ranking. The remaining candidates may need more window tests to reach
the same relative `BIT_SURV`; tables, launch decomposition, registers,
and downstream queues also change. With the final sieve predicate fixed,
the final survivor count per absolute interval is unchanged. In
particular the Fermat/host work need not shrink with the generation count.

At n = 60, the recorded device shares are 51.6% sieve kernel, 30.4%
generated tail, and 17.9% Fermat. Even if the *whole sieve kernel* got
1.4008x faster and all else stayed fixed, Amdahl's law gives only

    1 / (0.484 + 0.516/1.4008) = approximately 1.17x overall.

This is an illustration, not a prediction: a new wheel can redistribute
tail costs too. It explains why candidate-count ratios cannot be called
measured overall speedups or multiplied into the model clocks blindly.

## CYL-012 — separate useful wheel size from coverage completion size

**Classification:** representation research proposal; exact coverage
requirement and cost counterexample, unproved performance benefit.
It extends the earlier CYL-007/CYL-008 concerns to the long-index speed
objective. Relevant source: [cyclotomic_gpu.py](../cyclotomic_gpu.py),
`GpuEngine` launch decomposition at 3632–3687, and
[launch.py](../launch.py), checkpoint loading at 750–775.

### The present completion cost is already large

| Index | Existing 256-period segment span | Time per segment at recorded rate |
|---|---:|---:|
| 60 | 1.058889e24 | 28.93 min; about 32.15 min at the observed live rate |
| 72 | 9.992333e23 | 20.56 min |
| 84 | 1.058889e24 | 9.80 h |
| 96 | 1.446651e24 | 10.57 h |
| 90 | 3.651341e22 | 58.52 min |

Adding a prime q to a full CRT wheel multiplies its period by q but
reduces the generation density only by (q - g)/q. Under an idealized
unchanged cost per generated candidate, a complete new segment therefore
costs **q - g times** as long, not less time.

For n = 96 and q = 193, the attractive candidate ratio is 193/97, almost
2x. But a naive insertion with the existing 256-period completion scheme
would make its first segment take roughly 10.575 h * 97 = 42.7 days.
The new span would be 2.792e26, over eight times the stored median.
This example prices the geometry; it does not assert that the enlarged
wheel otherwise passes every representation bound.

The balanced substitutions in CYL-011 avoid much of this problem. At
the **old** rates, their segment lengths alone imply about 24.9 minutes
(60 balanced), 20.5 minutes (72), 2.04 hours (84), 2.06 hours (96
balanced), and 40.9 minutes (90 balanced). These are geometry comparisons,
not predictions of the new engine's rate. The short-period 90 alternative
would have a 2.40-minute segment at the old rate, sacrificing some density
gain for much more frequent completion.

The aggressive 96 and 90 alternatives instead need 17.15 and 21.68 hours
per new segment at the old rates. Even under the optimistic assumption
that each count factor becomes an equal line-rate gain, both remain
around 10.19 hours per segment. They should not displace the balanced
options merely because their raw count factors are larger. Test shorter
windows as a separate option and price their throughput loss; sub-128
widths were not remeasured on these cyclotomic filters in round 1.

For a half-open segment system starting at B with width S, a hypothetical
first solution X is confirmed after finishing through

    C(X) = B + S * (floor((X - B)/S) + 1).

The +1 is necessary when X is exactly a segment boundary. Compare
expected completion times and deadline coverage using actual segment
boundaries, not only a partial-launch x/s score. A smaller work unit can
make a found candidate confirm sooner; it cannot by itself eliminate
the search work below that candidate.

### A larger redesign must skip work before generation

The research direction is to enumerate the strong-wheel survivors of a
bounded absolute interval [L,H) without enumerating and then discarding
the rest of an enormous CRT period. An ordered CRT merge, an interval
index over partial CRT products, or disjoint class streams with a common
completed numerical boundary are possible designs to price.

The invariant is exact and independent of implementation. If R is the
set of allowed residues modulo W', every admissible integer t has a
unique representation t = r + kW', r in R. For each r, include exactly

    ceil((L/U - r)/W') <= k < ceil((H/U - r)/W'),

with rational-looking endpoints evaluated by equivalent exact integer
inequalities L <= U*(r+kW') < H. Intersecting with disjoint half-open
tiles partitions all candidates once. All component streams must finish
a tile before its upper bound is committed. Boundary candidates and the
exception zone remain explicit.

That identity is a correctness proof, **not an efficient enumerator**.
Materializing all residues of a large wheel, generating every CRT pair
and clipping afterward, or scanning a dense t-space bitmap may cost more
than the existing sieve. A viable design must bound setup, memory,
discarded combinations, and work per emitted candidate at the real
units and target heights. The project already has compacted queues;
calling ordinary compaction a new algorithm would add nothing.

A more concrete two-factor design is available to price. Let A and B
be coprime products of wheel primes with allowed residues a and b. Form
a sorted table of c_b = A^(-1)*b mod B. For each a, put
d_a = A^(-1)*a mod B. The canonical CRT representative is

    t = a + A*((c_b - d_a) mod B),       0 <= t < A*B.

For a tile [l,h) inside that period, the required z = (c_b-d_a) mod B
lies in the integer interval

    [max(0, ceil((l-a)/A)), min(B, ceil((h-a)/A))).

Translating this interval by d_a modulo B gives at most two sorted-table
ranges. Binary searches could emit only the pairs belonging to the tile.
Absolute tiles are first split at period boundaries and translated to
this canonical interval. This is a precise, disjoint interval join; it
preserves each CRT pair once.

The cost is scanning the A residues for each tile, sorting and storing
the B table, binary searches, irregular reads, and any third-factor join.
The balanced n = 90 wheel already has trillions of full CRT combinations.
Adding q = 541 gives only another 541/451 = 1.20 density factor while
multiplying that Cartesian combination count by 451. Even balanced
two-table sizes would move from a few million toward tens of millions
of entries, before indexing or multiple table copies. The decomposition
is therefore a concrete research starting point, not a demonstrated
way to obtain a tenfold gain.

There is a relevant local precedent in
[OPTIMIZATION.md section 2.15](../../OPTIMIZATION.md#215-enumerate-what-the-period-cannot-hold-the-classes-of-a-partially-forced-prime):
move a partially forced prime into an outer class dimension and enumerate
**every** surviving class. This can free internal period bits, but the
physical all-class completion interval still grows. Its successful
polynomial-runs example does not solve the latency problem automatically.

For an external architectural comparison, the primary
[primesieve source overview](https://github.com/kimwalisch/primesieve/blob/master/src/README.md)
describes segmented interval sieving with different representations for
different prime ranges. That supports considering interval-based state,
not importing its speed figures or treating a CPU prime generator as a
drop-in replacement for this sparse cyclotomic GPU sieve.

### Migration and leastness

The current launcher rejects a changed W because its saved cursor has a
different meaning. When only decomposition changes it resets partial u,
but the earlier CYL-007 accounting/pending-state reconciliation remains
open. It is now relevant to a real running campaign; the old ledger's
pre-campaign rationale no longer describes the current state.

For the first experiments, prefer the untouched 72/84/96/90 targets.
Any later n = 60 rollout needs a deliberate migration from a fully
committed absolute boundary, preserving evidence and consistently
replaying or reconciling uncommitted work. A faster implementation must
not reinterpret a saved partial cursor. This report does not alter or
stop the active run.

## Limits on other suggested shortcuts

- **More forced primes or one attractive residue class:** the complete
  forcing condition is q - 1 dividing n. The high-value primes above
  leave many valid classes; choosing only one would lose leastness.
- **Divisor floors:** the recorded, certificate-verified a(48) value
  supplies a floor of 951632152101389850 for n = 96. It is only 2.9e-8
  of the stored median. It cannot save days. Evidence flags were read,
  not reverified here; the recorded 66/78/88 candidates still have
  unproved forms and must retain that qualification.
- **Faster primality arithmetic:** the existing log prices symmetric
  Montgomery squaring around 1.04x overall at n = 60. Even deleting its
  entire 17.9% Fermat stage would yield only about 1.22x. It remains a
  bounded engineering idea, not the answer to a 10x requirement.
- **More host workers:** saved progress and the recorded host load do
  not show a multi-fold host bottleneck. A phase measurement may still
  be useful at each untouched long filter, but extra workers alone have
  no demonstrated route to the requested gain.
- **Shared 60/90 work:** the earlier CYL-010 cost objection stands.
  Shared forms do not establish enough shared generated candidates.
- **Searching promising classes out of order:** may locate a probable
  candidate sooner but leaves the smaller interval to exhaust. It does
  not finish the least-value task sooner without an additional coverage
  advantage.

## Recommended handoff

First test CYL-011's n = 72 and n = 84 substitutions, with the current
plans as controls and exact same-interval survivor comparisons. These
have favorable period costs and avoid migrating the active hunt. Then
price n = 96 and the more latency-sensitive n = 90 alternatives. Revisit
n = 60 only after a measured result and a reviewed migration route exist.

If these yield only moderate gains, record that result. The next question
is CYL-012's operation/memory case for bounded interval enumeration, not
another round of percentage-level tuning presented as a solution to the
days-long requirement. No design in this report has demonstrated the
6.5–11.3x overall improvement required by the hardest three median
scenarios. See the companion plan for concrete acceptance and rejection
criteria.

## Source hashes

SHA256 at review time; case is immaterial. Runtime checkpoints were read
as timestamped data and were allowed to continue changing under the
owner's hunt.

| File | SHA256 |
|---|---|
| cyclotomic_reference.py | `F844DE2805262DB9568D73120C4410C16F6A8D893473FDCA1E7077DF2675779C` |
| cyclotomic_search.py | `3B9B2F1B42464FF89AA656CC8589F5021953BEC8341C0547A6E201CE0348F3D2` |
| cyclotomic_gpu.py | `72B777C23E0F0D3B84837912793AF53D291DFD7D4AEEBAA74A98A3A8CD6F1DAB` |
| cyclotomic_model.py | `71E6D318235CABE9E813CC5FAB25C6A0A4AA3E95C62936D4A5F84C3D06B3346D` |
| launch.py | `645940E02A2790C305398B21ED20D7B346EF34C483A789332D02F6BFD918E7DA` |
| score.py | `D76B76131273C2565FF941204148BD501EB28C7005A361D1CC6A12E1530B2314` |
| model_results.json | `62B34B2102B3EFCACDC6D2C6A2BC095037354A765DB9ADD55C97EB085B05A204` |
| OPTIMIZATION_LOG.md | `5707F6E204B155521FE3CA62E4D139E3BF3718BA9758E9048FD36F31E7051827` |
| BENCHMARKS.md | `99D89FCA5D10646DB9F5D18368E48975AE256330A6C1CC1AC9282284D7CCEDCC` |
