# Codex mathematical reviews

> **Authorship:** This workflow and the independent reports in
> `codex-reviews/` are authored by Codex (OpenAI) at the repository owner's
> direction. Introduced 2026-10-20. Existing hunt implementations and their
> historical optimization records retain their stated authorship.

## Purpose and permanent scope

Claude designs and implements the hunts, then optimizes their code. Codex
provides a separate mathematical review: read the complete project, work
through its search mathematics — or, for a counting project, its exact
partition, aggregation identities and CPU algorithms — and identify
algorithmic improvements that the implementation process may have missed.
Claude can then implement and validate the supported proposals in a later
implementation task.

Codex may also author a **pre-implementation design and research
package** for a new project. Such a package is recorded in the project's
`codex-reviews/`
as a design — attributed, dated, with a disposition table for its
proposals that Claude keeps current — and the local index says plainly
that a static review of the implemented code has not been performed. A
design of future code is not a review of code that did not yet exist.

**Codex reviews are always static. Codex does not use the GPU for this
workflow, even when no hunt is running.** A report is a mathematical
analysis and implementation handoff, not an optimization experiment.

The primary questions are:

- Can a theorem exclude more of the search space?
- Can a known least term, exhausted interval, or sibling sequence impose
  a stronger bound or eliminate an entire residue class?
- Is there an exact change of variables, symmetry, factorization, or
  equivalent formulation that makes the search smaller or simpler?
- Can necessary conditions be applied earlier, or redundant searches
  combined without losing the first-occurrence claim?
- Can a different sieve or candidate representation amortize or eliminate
  repeated mathematical work?
- Does a newer project already contain an algorithm applicable here, and
  which hypotheses make that transfer valid?
- For an exact count: can an identity replace an enumeration level
  without losing an element of the counted family, is the partition
  provably disjoint and complete, and does the operation bound survive
  the representation at the sizes the campaign will run?

Kernel launch tuning, occupancy tuning, instruction profiling, and
benchmark sweeps are not the purpose of this review. An incidental
implementation issue may be recorded if it affects the proposed
mathematics, coverage, or handoff, but it does not substitute for the
mathematical analysis.

### What static means

Codex may read source, documentation, existing measurements, evidence,
model data, and checkpoint data; compare files; derive proofs and bounds;
and perform lightweight arithmetic on those data. Checking documentation
links and source hashes is also allowed.

Codex does **not** import or execute project engines, oracles, models,
launchers, or test batteries. It does not run searches, primality
experiments, self-tests, benchmarks, profilers, CUDA compilation, or GPU
queries. It does not change a running campaign, checkpoints, evidence,
engine code, or machine settings as part of a review.

Existing measurements may be cited with their source, date, family,
filter, height, and relevant limitations. Recomputing a time from a stored
rate is arithmetic, not a new speed measurement. A mathematical reduction
in candidate count is not automatically an equal reduction in runtime.

The measurement requirements in [OPTIMIZATION.md](OPTIMIZATION.md) and
[INNOVATION.md](INNOVATION.md) apply to a later implementation and
validation phase. They do not require a static reviewer to run anything.
No instruction or checklist in a report authorizes a campaign start;
only the owner starts hunts.

## Location and navigation

Every new project includes this documentation directory:

```text
<project>/
    codex-reviews/
        README.md
        YYYY-MM-DD-static-review.md
```

`README.md` is the local review index and finding-status ledger. A new
project with no completed review starts with that index saying **Not yet
reviewed**; it must not contain an empty report presented as an analysis.
The first report is created when Codex has actually reviewed the project.

Existing projects receive their directories as they are reviewed. The
initial batch was Euler, square, and decimal; the index below records
subsequent reviews. The earlier repository-wide triage is not a substitute
for a project's full report.

**Multi-project reviews proceed one project at a time** (owner directive
2026-10-20). All active reviewers focus on that project, with complementary
mathematical, implementation, and evidence checks. Finish and reconcile its
report before advancing to the next project. Reading a sibling algorithm
as a relevant reference is permitted; starting another project's review
in parallel is not.

Use a dated report name. If there are two reviews on the same day, append
a descriptive suffix, for example `2026-10-20-pruning-followup.md`.
Keep earlier reports as historical records and link follow-ups from the
index. Do not overwrite a proposal's original evidence with the outcome
of an experiment that occurred later.

The directory holds Markdown analysis and indexes only. Source copies,
executable prototypes, timing harnesses, raw profiler output, checkpoints,
and discovery evidence do not belong here. This is an explicit addition
to the project skeleton, not an exception for miscellaneous files.

## Review index

| Project | Local index | Initial report | Review scope |
|---|---|---|---|
| clique-ladders | [Findings and disposition](clique-ladders/codex-reviews/README.md) | [2026-10-20](clique-ladders/codex-reviews/2026-10-20-static-review.md) | Six primary families and five derived entries; admissibility theorem, coverage and reuse limits |
| decimal-ladders | [Findings and disposition](decimal-ladders/codex-reviews/README.md) | [2026-10-20](decimal-ladders/codex-reviews/2026-10-20-static-review.md) | A305740 and A153431; cross-family least-term pruning |
| dickson-ladders | [Findings and disposition](dickson-ladders/codex-reviews/README.md) | [2026-10-20](dickson-ladders/codex-reviews/2026-10-20-static-review.md) | A247965; shared fold patterns, quadratic root capacities and model-tail correction |
| euler-prime-runs | [Findings and disposition](euler-prime-runs/codex-reviews/README.md) | [2026-10-20](euler-prime-runs/codex-reviews/2026-10-20-static-review.md) | A164926; shifted-polynomial reduction and necessary filters |
| factorial-ladders | [Findings and disposition](factorial-ladders/codex-reviews/README.md) | [2026-10-20](factorial-ladders/codex-reviews/2026-10-20-static-review.md) | Two primary families and A226935; finite-collision tail bound, wheel-plan scope and confirmation latency |
| lcm-ladders | [Findings and disposition](lcm-ladders/codex-reviews/README.md) | [2026-10-20](lcm-ladders/codex-reviews/2026-10-20-static-review.md) | Two primary families and two riders; interval residue tests, monotone total forcing, wheel construction and coverage reuse |
| linear-ladders | [Findings and disposition](linear-ladders/codex-reviews/README.md) | [2026-10-20](linear-ladders/codex-reviews/2026-10-20-static-review.md) | Seven primary families and three derived entries; maximal forced units, constructive larger wheels and shared survivor unions |
| plus-two-cliques | [Findings and disposition](plus-two-cliques/codex-reviews/README.md) | [2026-10-20](plus-two-cliques/codex-reviews/2026-10-20-static-review.md) | A083518 and A083519; deadline-aware completed coverage, finite-collision model bounds and a complete nonforcing proof |
| polynomial-runs | [Findings and disposition](polynomial-runs/codex-reviews/README.md) | [2026-10-20](polynomial-runs/codex-reviews/2026-10-20-static-review.md) | Four primary families and the Euler relation; exact-run proof barriers, existing six-class wheel, correlated model-tail bounds and quartic nonforcing theorem |
| power-ladders | [Findings and disposition](power-ladders/codex-reviews/README.md) | [2026-10-20](power-ladders/codex-reviews/2026-10-20-static-review.md) | Four power families; semiprime factor-state sieve and wheel counts, deadline coverage, conditioned model and domain-proof safeguards |
| prime-ladders | [Findings and disposition](prime-ladders/codex-reviews/README.md) | [2026-10-20](prime-ladders/codex-reviews/2026-10-20-static-review.md) | Both sign families; periodic-window transfer, constructive wheel, forced-divisor proof ceiling, available N+1 certificates and coverage safeguards |
| primorial-ap | [Findings and disposition](primorial-ap/codex-reviews/README.md) | [2026-10-20](primorial-ap/codex-reviews/2026-10-20-static-review.md) | A053647; compacted live-word sieving, exact interval tail, per-term low-pass coverage and prescribed-difference/model clarification |
| primorial-ladders | [Findings and disposition](primorial-ladders/codex-reviews/README.md) | [2026-10-20](primorial-ladders/codex-reviews/2026-10-20-static-review.md) | Three additive families; shared quadratic sieve, composite-domain model correction, proof and coverage safeguards, larger-wheel costs and model-tail bounds |
| primorial-runs | [Findings and disposition](primorial-runs/codex-reviews/README.md) | [2026-10-20](primorial-runs/codex-reviews/2026-10-20-static-review.md) | Three exact-run families; deadline-aware completed coverage, proof-safe exact-index exclusions, cap handling and finite-collision model bounds |
| product-cliques | [Findings and disposition](product-cliques/codex-reviews/README.md) | [2026-10-20](product-cliques/codex-reviews/2026-10-20-static-review.md) | Both greedy product families; periodic reuse, concrete larger wheels, completed-suffix refiltering, quadratic model tails and global nonforcing proof |
| shift-ladders | [Findings and disposition](shift-ladders/codex-reviews/README.md) | [2026-10-20](shift-ladders/codex-reviews/2026-10-20-static-review.md) | Both geometric-shift families and named relatives; constructive factored wheels, affine forcing, proof-range and coverage migration, finite-collision tails and derived evidence |
| square-ladders | [Findings and disposition](square-ladders/codex-reviews/README.md) | [2026-10-20](square-ladders/codex-reviews/2026-10-20-static-review.md) | A089761; period-window sieving and representation bounds |

Update this table when a report is added to another project. The local
index is the authority for the current disposition of its findings.
An entry here means a report exists, not that an optimization has been
implemented or measured.

**Inventory completed 2026-10-20:** all 17 populated hunt projects have
an initial report and local finding ledger. The shared `huntlib/` library
was inspected where it supports those hunts; it is not a separate search
family. `prime-power-sums/` was empty at review time, so there was no
algorithm or evidence to assess. Once it or another new project is
populated, use the request below and add its report to this index.

## Starting a review of a new or changed project

Give Codex the following request, substituting the project directory:

> Follow CODEX_REVIEWS.md and perform a thorough static mathematical
> review of `<project>`. Read its definitions, oracle, CPU and GPU source,
> launcher, verification and checkpoint logic, odds model, evidence,
> benchmark history, optimization history, and any earlier Codex reports.
> Look for missed search-space reductions, equivalent formulations,
> stronger bounds, redundant work, and applicable algorithms elsewhere in
> first-knowns. Do not use the GPU or execute project code. Create a dated
> report and update the local and top-level review indexes. Give Claude
> mathematical arguments, implementation requirements, and a future
> validation plan; distinguish proved facts from unmeasured hypotheses.

For a repeat review, name the previous report and the changes to examine.
A changed frontier, new sibling result, altered representation, or newly
available algorithm in another project is a reason to revisit an earlier
conclusion. The absence of a new large optimization is an acceptable
result when supported by the analysis.

## Required analysis

### 1. Establish what is actually being searched

Read `CONVENTIONS.md`, `CLAUDE.md`, `OPTIMIZATION.md`, `INNOVATION.md`,
the project documents, and any applicable instructions before reviewing.
Read all five public Python roles, the mathematical model, and relevant
shared helpers. Follow calls into verification and checkpoint code rather
than inferring their behavior from a README.

For every family, record:

- The definition, using the OEIS entry's own notation; domain restrictions;
  whether runs are exact or at least a given length; and the actual open
  indices. Distinguish an OEIS index from an internal run counter.
- The current filter, candidate representation, wheel, sieve, exceptional
  small-value zone, numerical ceiling, and proof crossing — or, for a
  counting project, the partition and its proof, the work unit, the tail
  evaluators with their validated routes, the manifest and commit
  protocol, and the measured cost table the policy rests on.
- The certified coverage floor separately from work in an unfinished
  segment. A fraction of residue classes processed is not an equally
  sized contiguous searched interval.
- The source and age of the frontier, measurements, and model assumptions.
  Checkpoint and evidence data may be newer than a status paragraph.

Record the repository revision and whether the worktree was dirty.
Include source-file hashes or another precise snapshot description for
the code that materially supports the findings. A Git revision alone is
not enough when the reviewed files include uncommitted changes.
Use relative file links plus function/class names and snapshot line
numbers; symbols remain useful when lines later move. Do not put local
machine paths or personal information in reports.

### 2. Look for mathematical reductions before tuning costs

Work through the forbidden residue sets, forced factors/classes,
polynomial identities, monotonicity, domain restrictions, and sibling
relations. Ask which expensive conditions are only needed for the rare
survivors, and which conditions already follow from others.

Inspect newer algorithms in related projects. State why a transfer
applies to this family's mathematics and where its assumptions fail.
Do not infer transferability merely from a shared function name or the
fact that both programs use a GPU.

Read every relevant rejected attempt in the optimization log. Classify
each proposal as a new finding, a known unfinished idea, a transfer from
another project, or a reconsideration enabled by a specific new fact.
Explain why an earlier rejection does or does not still apply.

### 3. Prove that a reduction cannot lose a first occurrence (or an element of a counted family)

For each proposed exclusion or transformation, supply the implication or
bijection that justifies it, including its range of validity. For an
exact count, a reduction must preserve the family counted — every
permanently excluded value, every alternative recipe for one value, zero
and negatives — and a proposed formula is a candidate until the
implementation gates it category by category. Explicitly cover:

- Small-prime equality exceptions, endpoints, strict versus inclusive
  bounds, and integer overflow/representation limits.
- Exact-run stopping composites, plateau terms, prime/semiprime domain
  conditions, and off-by-one changes of index.
- Which previously established least claim is used and where its evidence
  lives. Reading that evidence is not a fresh independent verification.
- The distinction between preserving all raw sieve survivors and
  preserving all mathematically eligible discoveries. A valid additional
  filter can deliberately change the former.
- Whether a stronger filter changes the census or removes a designated
  canary from the production stream. The implementation must account for
  that change explicitly.
- How old contiguous coverage is carried, how a new wheel overlaps the
  old floor without gaps, and how partial work, counts, and pending
  discoveries are handled.

Keep the reference oracle slow, direct, and independent. A proposed
optimized CPU sieve may independently express a proved restriction, but
the oracle must still test the original definition. Do not obtain parity
by making the oracle call the new optimized helper.

### 4. Price the opportunity honestly

Use these evidence labels in the report:

| Label | Meaning |
|---|---|
| Proved | A mathematical argument establishes a stated implication or count, within explicit assumptions and bounds. |
| Observed in source/data | The reviewed files contain this behavior or stored value; no execution confirmed it in this review. |
| Previously measured here | An existing project record measured this configuration; give its provenance and limitations. |
| Measured in a related project | A donor project measured it; the destination's gain is still unknown. |
| Unmeasured hypothesis | A proposed runtime benefit or design choice requires later implementation and measurement. |
| Model-derived estimate | Arithmetic from a stated probabilistic model and rate, not a discovery guarantee or measured runtime. |

Report candidate-count reductions separately from speedup estimates.
Do not multiply donor speedups that remove the same work. State when the
source measurement used another filter, another height, an older
primality chain, a hypothetical greedy prefix, or a different load regime.

When a time budget matters, use the current certified coverage and the
model conditional on that coverage where available. Also condition on any
new mathematical information used to prune the search: knowing that an
entire class contains no solution can change the forecast as well as the
work. Dividing an old median clock by a candidate-reduction factor does
not establish a new conditional median. Label an unchanged target-depth
calculation as a fixed-distance scenario until the model is reconciled.
Include the time to close the coverage unit and confirm leastness, not
just time to encounter a candidate. State model bias and rate uncertainty.
Engineering time is separate from estimated hunt time.

### 5. Leave a concrete handoff for Claude

Give each finding a stable project-specific ID, such as `EUL-001`,
`SQR-001`, or `DEL-001`. IDs are unique within a project's review history;
follow-ups refer to an existing ID or allocate a new one.

Each actionable finding contains:

1. Priority, mathematical claim, classification of evidence, and whether
   the idea is new or already documented.
2. Source references and the proof or derivation.
3. Expected work reduction, possible runtime benefit, and limitations.
4. A bounded implementation sequence naming affected components.
5. Correctness obligations: independent oracle, optimized CPU/GPU parity,
   relevant exceptions and ceilings, coverage migration, evidence and
   census semantics.
6. Future tests and measurements for Claude, including the conditions
   that would reject the idea. These are instructions for a later
   authorized implementation phase, not actions performed by Codex.

A report should cover every family in its project, including families
with no supported improvement. Finish with the areas examined, ideas
declined or already implemented, unresolved questions, and an explicit
statement of what was and was not executed.

## Report and index template

The report may use additional subsections, but keep these roles:

```text
# <Project>: static mathematical review
Authorship, date, static-only scope, source snapshot
1. Executive assessment and target families
2. Current mathematics and certified search state
3. Findings (stable IDs, evidence labels, proofs, source references)
4. Implementation handoff and future validation obligations
5. Work-count and conditional-time estimates
6. Alternatives examined, prior rejections, and unresolved questions
7. Sources and execution record
```

The local `codex-reviews/README.md` contains:

```text
# Codex reviews: <project>
Link to ../../CODEX_REVIEWS.md
Latest report and any superseded reports
Finding table: ID (linked to report section) | Finding | Disposition | Evidence
```

An unreviewed project's index says **Not yet reviewed**, contains no
finding rows, and links to the workflow above.
The evidence column initially states the proposal's basis and limits;
Claude later adds links to implementation and validation records there.

## How Claude records the outcome

Before implementing a report, Claude rechecks its source assumptions
against the current code, frontier, and evidence. A static report is an
input to engineering judgment, not an instruction to ship every idea.
Any runtime work belongs to that later implementation task and follows
the owner's current resource constraints and the repository's gate,
measurement, and campaign-ownership rules.

The local index tracks one of these dispositions for each finding:

- **Proposed**: analyzed, not implemented or measured.
- **In progress**: implementation work has begun; this does not imply
  correctness or a speedup.
- **Implemented, awaiting validation**: code exists, but required checks
  or measurements have not established the claimed result.
- **Implemented and validated**: required correctness checks and relevant
  measurements are recorded.
- **Declined**: an argument or measurement supports rejection; link it.
- **Deferred**: still plausible, postponed for a stated reason.
- **Superseded**: replaced by a linked finding or report.

Claude updates the index and records attempts, including failures, in the
project's existing `OPTIMIZATION_LOG.md`; accepted measurements also go
into `BENCHMARKS.md` under the existing scoring rules. Link those records
and any relevant commit from the finding's index row. Do not label an
implementation validated based solely on the static proof, successful
compilation, or a modified fingerprint.

The dated Codex report remains attributable to Codex and to its original
snapshot. A correction or later conclusion is a dated addendum or a
follow-up report, linked from the index. Discoveries remain in
`RESULTS.md` and `evidence/`; review reports never announce new terms or
stand in for the discovery protocol.
