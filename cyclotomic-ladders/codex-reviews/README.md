# Codex reviews — cyclotomic-ladders

These are Codex-authored static mathematical and algorithmic analyses for
Claude's later implementation work. Follow the repository's
[Codex review workflow](../../CODEX_REVIEWS.md). The implementation and
historical project records retain their Claude attribution.

**Static review complete, 2026-10-23.** No code was changed, project code
executed, GPU used, tests or benchmarks run, or campaign state changed.
Proposals are not measured speedups or discovery evidence.

**Long-index follow-up complete, 2026-10-24.** Reviewed the engine-v2
optimization record and saved n = 60 campaign progress. Added concrete
wheel substitutions and a bounded-interval enumeration research direction
for the remaining long A072942 indices. This was also static and
documentation-only; the running hunt was untouched.

| Document | Snapshot / purpose | State |
|---|---|---|
| [2026-10-23 static review](2026-10-23-static-review.md) | HEAD 35f48897eac28a5ec0ac4f60c3ce2e3a92d8708c; project untracked, source hashes recorded; both primary families and A233512 | Static analysis complete |
| [2026-10-23 Claude validation plan](2026-10-23-validation-plan.md) | Ordered prerequisites, bounded experiments, independent correctness checks and rejection criteria | Future work; nothing executed |
| [2026-10-24 long-index follow-up](2026-10-24-long-index-followup.md) | Engine v2 and saved n = 60 progress; cyclotomic wheel substitutions, exact density/period prices, and limits on a one-day target | Static analysis complete; no measured new gains |
| [2026-10-24 long-index experiment plan](2026-10-24-long-index-validation-plan.md) | Explicit wheel comparisons, invariant absolute workloads, completion-time acceptance and interval-CRT research requirements | Future work; nothing executed |
| [2026-10-24 filter-pipeline follow-up](2026-10-24-filter-pipeline-followup.md) | Additional directions beyond wheel changes: sparse sieve-prime selection, interleaved Fermat rejection, and quantitative limits on catalogs/other representations | Static analysis complete; future experiments unmeasured |

The dated report is the historical record. Claude should update this
ledger as work proceeds, linking implementation revisions, validation
records and specific sections of OPTIMIZATION_LOG.md and BENCHMARKS.md.
Do not mark a finding validated on the basis of the static argument or
successful compilation alone.

| ID | Finding | Disposition | Evidence / implementation status |
|---|---|---|---|
| [CYL-001](2026-10-23-static-review.md#cyl-001-divisor-floors-and-inherited-coverage) | Inclusive divisor floors and inherited completed no-hit coverage | Proposed, not built | Set-inclusion proof and ten exact floors; the distance saved is at most 1.5e-6 of a search, so it is not a rate lever (OPTIMIZATION_LOG.md round 1, "priced, declined, or left for the owner"); a floor service outside the oracle remains a later session's correctness item |
| [CYL-002](2026-10-23-static-review.md#cyl-002-subgroup-roots-and-paired-residue-tables) | Subgroup construction and even-index paired residue tables | Priced, not built | Round 1 (2026-10-23) removed the generic tail round at every campaign filter (TAIL_LITERAL_LAST: the last round is generated, 1.03-1.07), so the mask-or-list scan the fold targeted no longer runs; the generated tables are L1-resident (96% hits), so halving them buys nothing measured. The subgroup construction changes build time only (0.5-2 s an engine) |
| [CYL-003](2026-10-23-static-review.md#cyl-003-try-known-factors-before-optional-factorization) | Try already proved certificate factors before optional factoring | Proposed, not built | Sufficient factored parts proved for Phi_13/Phi_26 at n = 78; a certificate-cost change, not a rate change; left for the session that first certifies an n = 78 find. **Material since 2026-10-24** (RESULTS.md): the a(66), a(78) and a(88) finds left Φ₁₁, Φ₂₂, Φ₃₃, Φ₆₆ (n = 66), Φ₃₉ (n = 78) and Φ₁₁, Φ₂₂, Φ₄₄, Φ₈₈ (n = 88) unproved, while Φ₁₃ and Φ₂₆ at n = 78 were proved by the launcher's shape route from the run's own factors; this route, or factoring the 67-digit Φ₅(x) and Φ₁₀(x) outside those runs, is the open item for a checkable certificate of the nine; all nine were proved prime by FLINT's APR-CL on 2026-10-25 (RESULTS.md), so the terms do not wait on it |
| [CYL-004](2026-10-23-static-review.md#cyl-004-proof-failure-must-not-settle-an-index) | Pending proofs must block settlement and leastness advancement | Proposed; owner's decision | The repo-wide discovery protocol (CONVENTIONS.md) records a find that passes its three screening legs and lists any value whose certificate did not land as UNPROVED for the owner to certify by hand; making such a find a pending state instead changes that protocol for every project and is the owner's call, not an optimization session's. No code changed. Three such records now exist (a(66), a(78) and a(88) of A072942, 2026-10-24; RESULTS.md names the nine values): the protocol was followed as written — each find recorded with its unproved values listed, and nothing else in the campaign rests on them (A072942's indices are independent lines); the nine values were proved prime by APR-CL on 2026-10-25 (RESULTS.md) |
| [CYL-005](2026-10-23-static-review.md#cyl-005-a233512-needs-its-own-strict-floor) | Conditional A233512 rider with its own strict predecessor | **Implemented 2026-10-23** | `launch.also_settles` settles the rider at the first index a find settles, only above the previous term and only while the primary chain from a(5) is known and strictly increasing; a plateau's later indices stay open. `_rider_drill` (selftest) runs the plateau, the equal-term, the gap, the below-from_n and the published-prefix cases; `_rediscovery_run_drill` still expects the rider at a rediscovered a(n) |
| [CYL-006](2026-10-23-static-review.md#cyl-006-preserve-per-index-identity-and-requested-scope) | Equal-x ledger identity and explicit-index completion scope | **Implemented 2026-10-23** | A072942 ledger rows are keyed by (index, x) (`ledger_key` = index x 10^41 + x), so two indices at one x both survive; `--index` names that index alone and the campaign stops when it closes (launch.main). Project-local; the shared helper is untouched |
| [CYL-007](2026-10-23-static-review.md#cyl-007-capped-runs-and-coverage-migration) | Resolve capped pending runs; reconcile partial accounting on migration | **Cap fixed 2026-10-23**; migration pending | At a segment's end every pending value at or past the cap the segment was swept under is re-read uncapped by the oracle before it is classified (a drill reads no further than its bound), so a later cap-hit is never demoted to census by a find before it (launch.Campaign.run). **Migration implemented 2026-10-24** (round 2, at the owner's word): a cursor written under an older plan at an index whose wheel moved is ADOPTED by `launch.Campaign.adopt_cursor` — only the swept boundary carries over, re-denominated onto the new W with flooring (no gap), the partial work cursor is dropped and that segment is swept again (its census counted twice, as counts), finds / pending / rungs / counts carried; `--status` says what the next start will do; drilled in the selftest and checked on a copy of the live n = 60 cursor (period 475, launch 0), and **run live at the owner's restart of n = 60**, which found a(60) under p3 on 2026-10-25 (RESULTS.md). A reconciliation that CARRIES partial launches across decompositions was not built: the launches of one wheel are not a prefix of another's |
| [CYL-008](2026-10-23-static-review.md#cyl-008-freeze-the-workload-before-comparing-speed) | Freeze complete benchmark work, independently establish expectations | **Implemented 2026-10-23** | Every score.py shape is frozen (FROZEN) with its launch decomposition and width pinned (SHAPE_TCHUNK: tchunk, nu, pb) over 16 launches of the segment at its height, so a planner or guard change cannot move the workload; the engine-v1 readings of the same shapes are in BENCHMARKS.md; every round-1 A/B compared survivor streams exactly on every round, and G9 pins the stream to the CPU engine |
| [CYL-009](2026-10-23-static-review.md#cyl-009-condition-the-model-and-qualify-its-calibration) | Condition model floors and qualify calibration, tails and costs | Proposed, not built | Dependence/selection argument and stored-data discrepancies stand; the model was not changed in round 1 (its predictions are historical); BENCHMARKS.md's clocks use the measured engine-v2 rates |
| [CYL-010](2026-10-23-static-review.md#cyl-010-price-shared-divisor-searches-before-building-them) | Shared 60/90 sieve only after a convincing measured cost case | Deferred | Existing idea; forced-class duplicate fraction 1/3984 before further sieving; coupled runtime benefit unknown |
| [CYL-011](2026-10-24-long-index-followup.md#cyl-011--choose-wheel-primes-using-the-cyclotomic-root-counts) | Admit strong primes above 89 and consider period-constrained wheel exchanges | **Measured 2026-10-24; shipped at n = 60, 72, 84, 96 (planner p3)**; declined at n = 90 | All nine rows and six planner picks with the universe raised measured paired and interleaved at the campaign's own configuration, every survivor re-derived on the CPU and the sieve stream proved identical to the CPU engine's launch for launch (OPTIMIZATION_LOG.md round 2). The arithmetic held exactly (w(q, n) = gcd(n, q − 1), every density and period to four decimals); the runtime did not follow the candidate count: x/s 1.06–1.10 at x = 3 and 1.04–1.07 at the median for the 72 / 84 / 96 rows (the sieve kernel's 10–16%; the tail and Fermat stage are per survivor per x), 0.97–1.00 for every n = 90 exchange (the tail behind a wheel holding 181 and 271 runs 1.5x slower per unit of line), 1.07–1.09 at n = 60 (shipped too, the live cursor adopted — see CYL-007). The four shipped wheels are a per-filter table (`cyclotomic_gpu.MEASURED_WHEELS`); raising `WHEEL_TOP` was declined because the planner's cost model overpredicted every row 1.2–1.6x and would pick a 29x segment at n = 72 and the 1.00x wheel at n = 90. Shapes D72/D84/D96 re-frozen at the new wheels beside the p2 workloads (BENCHMARKS.md) |
| [CYL-012](2026-10-24-long-index-followup.md#cyl-012--separate-useful-wheel-size-from-coverage-completion-size) | Complete bounded numerical intervals independently of a huge wheel period | Not pursued (round 2, 2026-10-24) | The round-2 profiles put the sieve kernel at 45–52% of the device at every day-long index and a wheel's whole density gain at 10–16% of it; the other half (generated tail, Fermat stage) is per survivor per unit of line and no wheel-side representation reaches it, so the 6.5–11x the hardest medians need is not on this path. The exact interval-CRT join stands as mathematics; its cost case was not built |
| [CYL-013](2026-10-24-filter-pipeline-followup.md#cyl-013--a-sparse-cost-aware-sieve-prime-frontier) | Choose a sparse set of later sieve primes by rejection benefit and actual cost | Proposed, not built or timed | Exact root-count spikes above 8192; previous full-prefix depth sweeps did not test this membership change; tables, packs, exception floors and changed-stream fingerprints must be priced/validated |
| [CYL-014](2026-10-24-filter-pipeline-followup.md#cyl-014--interleave-cheap-fermat-rejection-with-the-sieve-tail) | Put the first one or two Fermat tests between sieve stages | Proposed, not built or timed | Same complete conjunction in a different order; exact conditional-cost criterion, earlier-buffer and fallback requirements; no gain inferred from the criterion alone |

The 2026-10-24 follow-up updates CYL-007's operational context: an n = 60
campaign now has a partial cursor, so the outstanding migration work is
material before any live wheel/decomposition change. The pre-campaign
statement in its historical round-1 disposition is no longer current.
CYL-009's model qualification remains open; the follow-up's clock tables
use stored-model scenarios and are not new conditioned forecasts.

**Experiment D** (the validation plan: the Fermat stage's forms in a
cost-aware order): built and measured in round 1 as PRP_BY_DEGREE — the
six forms tested by degree, a stable sort — 1.009 at A070737 n = 13 and
1.013 at A072942 n = 90, the same conjunction and stream (G23); shipped.
Experiments A (CYL-003), B and C (CYL-002) were not run, for the reasons in
the table.

A deferred or declined result should retain its rationale so the same
experiment is not repeated without new evidence. Discoveries and proof
records belong in the existing RESULTS.md and evidence/ workflow, never
in this review directory.
