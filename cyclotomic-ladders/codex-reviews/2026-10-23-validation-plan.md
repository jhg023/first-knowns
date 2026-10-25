# Cyclotomic-ladders: Claude implementation and validation plan

> **Authorship:** Codex (OpenAI), 2026-10-23. Companion to the
> [static review](2026-10-23-static-review.md), for a later authorized
> Claude implementation session. Nothing in this document has been run.
> No proposal is implemented or validated by its presence in this plan.

Use the [finding ledger](README.md) for dispositions. The dated review
contains mathematical proofs, source links, snapshot hashes and limits.
Recheck its assumptions against current source and any new evidence before
starting: this snapshot has no campaign data and no frozen scoring baseline.

## Scope and order

Use the regular Python installation; do not create or use a virtual
environment. Follow the repository's short-invocation, interleaved A/B,
independent-oracle and active-project rules. Scratch harnesses belong
outside the public project surface. Only the owner starts a real campaign;
a bounded campaign invocation is still a campaign. Runtime measurements
should call the engine on specified windows. Tests of campaign state
transitions should use isolated temporary state and controlled doubles.

Recommended order:

1. CYL-004 through CYL-007: repair proof settlement, derived claims,
   per-index identity/scope and coverage handling.
2. CYL-008: establish an independent, invariant baseline and record the
   actual phase split at the provisional long filters.
3. CYL-003: known-factor-first certificates, as an independent change.
4. CYL-002: subgroup construction and generic-tail negation folding,
   as separate changes; measure before trying the generated-table variant.
5. CYL-001 and CYL-009: provenance-bearing floors, conditioned planning,
   and honest calibration metadata.
6. CYL-010: leave a coupled 60/90 search deferred unless measured costs
   justify the larger implementation.

Do not combine workload, sieve representation, device predicate and
certificate changes into one A/B result.

## Required correctness cases before optimization acceptance

| Finding | Bounded test | Required result / rejection condition |
|---|---|---|
| CYL-004 | After all screening legs pass, inject one required certificate failure | No settlement/close/promotion/rider requiring the unproved condition; a certified prefix may settle only its justified indices; unresolved indices retain the leastness barrier |
| CYL-004 | Restart pending-proof state, then supply a valid certificate | Exactly one eventual settlement; no lost candidate or duplicate evidence |
| CYL-004 | Strip or alter a large-prime subproof and test every mandatory project route | Independent verification rejects corruption; optional skipped cases cannot satisfy the ceiling claim |
| CYL-005 | A mocked new primary value settles two or more successive A070737 indices | At most the first justified strict rider is emitted; remaining A233512 indices stay open |
| CYL-005 | Known strict prefix, missing rider predecessor, later rejoining case | Derivation occurs only with the rider's proved predecessor and strict inequality |
| CYL-006 | Two A072942 indices share one x; each record is replayed | Both index claims survive; replay remains idempotent |
| CYL-006 | Interrupt between evidence file, ledger and checkpoint updates | Recovery retains every index and neither duplicates nor erases a discovery |
| CYL-006 | Explicit --index closes successfully; separate default TARGETS run | Explicit selection exits; default mode advances in the intended order |
| CYL-007 | At filter 11/cap 17, first pending value extends to run 18 and a later one to run 19 | Both primary first occurrences are processed; later cap-hit is not demoted to census |
| CYL-007 | True lengths cap-1, cap, cap+1, maximum; mark only lengths at or above cap as capped; split and resume | Same settled-index vector and census policy as independent complete classification; PRP overstatement tested separately as rejection |
| CYL-007 | Change width/chunks/ordered wheel with partial u, pending values and counters | Exact transformation or rollback/replay from committed boundary; no gaps or double counts |
| CYL-008 | Change planner wheel and nu while keeping a baseline row fixed | Manifest remains fixed or comparison is explicitly rejected as a different workload |

A synthetic state-machine counterexample suffices for cap, ledger, scope
and rider tests; do not search for a new term to obtain that fixture.
Keep primality/certificate fixtures separate and independently supported.

## Baseline protocol — CYL-008

Record one manifest per benchmark shape:

- Source revision/hashes, hardware/software versions, regular Python
  executable, active-project status and load conditions.
- Family/filter, exact mathematical interval or enumeration slice,
  ordered wheel levels, unit/class, q2, window/live periods, record width,
  decomposition and device-tested form set.
- Expected count/checksum with independent derivation provenance; keep
  the complete sorted vector for small fixtures.
- Device time by window, in-block rounds, generated tail, generic tail
  and Fermat stages; host core-seconds, survivor rate and peak memory.
- Complete work-unit time, classification drain, closure latency and
  proof cost, separately from initialization and compilation.

Freeze all eight campaign shapes and all three fixed anchors. Add compact
opening checks for A072942 48, 66, 78, 80 and 88: their absence from the
headline shape list does not waive opening correctness or cliff checks.
Use fixed absolute workloads for planner comparisons. A partial residue
slice's density-equivalent line is not certified contiguous coverage.
Where independent dense enumeration is too large, use an independently
derived exact decomposition rather than copying the GPU's count into
its own expectation.

Provisional performance targets are A070737 n = 13 and A072942 n = 60,
72, 84, 90, 96. Check A070737 opening 11 and promotion 12 too. The model's
proxy clock does not establish the eventual measured priorities.

Later acceptance requires both public entry points:

```text
python launch.py --selftest
python score.py
```

The score battery omits launcher drills, and a headline score can print
before later shapes finish. Require all gates, every frozen fingerprint,
and successful exit. Respect the repository invocation cap; if compilation
or a battery does not fit, partition prescribed validation into recorded
short runs rather than silently omitting cases.

## Experiment A — known-factor-first proofs (CYL-003)

**Hypothesis:** available factored parts avoid optional Phi_4/Phi_12
factorization when certifying Phi_13/Phi_26 in the n = 78 run. No expected
numerical speedup is assigned.

1. Independently multiply the review's identities. Check exact
   inequalities and gcd hypotheses at endpoints and admissible values.
2. Build F from proved factors of x and earlier proved run values.
   Try the existing witness/checker route before optional factorization.
3. Reuse x's factorization and verified subproofs through the evidence
   transaction. Cache repeated partial factorizations by exact integer.
4. Count calls, routes and failures. A successful early Phi_13/Phi_26
   proof should make no Phi_4/Phi_12 factoring call.
5. Compare complete certificate bundles and independent verification
   with the baseline. Interleave timings on identical existing inputs;
   report total confirmation cost and factor-call reduction separately.

Reject if an unproved factor is admitted, a malformed subproof passes,
verification changes, or the total confirmation path worsens without a
justified benefit. Bounded witness failure falls back safely or remains
pending under CYL-004. Do not claim all n = 78 forms or n = 66/88 hard
cases are solved.

## Experiment B — subgroup construction (CYL-002)

**Hypothesis:** gcd counts and direct subgroup generation remove redundant
setup/model work for A072942.

Leave the reference polynomial walk unchanged. Compare the new table
construction with the original definition for every residue over a bounded
prime set, including q dividing n, q = 2, forced primes and all ten targets.
Check x space and scaled class space; zero must survive. Compare exact
raw engine survivors before timing. Record cold construction, cached
construction, model-table preparation and complete work separately.
Reject if there is no useful benefit or independence is compromised.

## Experiment C — generic-tail negation fold (CYL-002)

**Hypothesis:** for even A072942 indices, canonical masks eliminate rare
root-list scans in the generic final tail and overflow paths at depth 8192.

Keep q2, wheel, window, launch decomposition and device predicate fixed.
Initially change only generic remainder testing and mask construction.
Fold the normalized remainder after the period/base contribution. Enable
the path only under the proved symmetry assumptions.

Parity cases: every target; residues 0/1/q-1 and both sides of q/2;
primes around 4096/8192; deeper q2 with exact canonical-list fallback;
wide/narrow records; relevant limb boundaries; deliberately forced queue
overflow. Use populated CPU/GPU windows at multiple heights, including
the supported ceiling. Raw survivors and frozen fingerprints must match.

Measure generic-tail-only and complete-engine time, including the generic
tail's share of total time. Decline if canonicalization costs more than
the rare scans it removes. Only then consider the separate generated
[0,2q) table fold, which saves bits but adds correction arithmetic, or
direct subgroup powering for deeper large-root cases.

Do not broaden n_max here. A later extension must check the uint32 unit,
limb sizes, coefficient restrictions, record arithmetic and proof coverage
as well as root capacity. The report establishes no current unit overflow.

## Experiment D — reorder the same Fermat prefix

This secondary idea is in the review's alternatives. Log it under
CYL-002's algorithm work, or give it a new stable finding if substantial.
It changes execution order only.

For A070737 and divisor filter 60, compare 1,2,3,4,5,6 with 1,2,3,4,6,5.
At divisor filter 90, move Phi_6 before Phi_5 while retaining the identical
original six-form set. Record limb widths, per-stage cost and conditional
survivor counts. Degree alone does not establish the best order; the
approximate two-test criterion is c_A/(1-s_A) <= c_B/(1-s_B), with costs
and pass fractions measured on the same entering set and launch overhead
priced separately.

G23 should compare against the independent CPU conjunction in definition
order; the host reads runs in definition order. Require identical device
survivors/fingerprints. Adding a seventh or later form changes the
predicate and may change census; keep it a separate experiment.

## Floors, model and planner — CYL-001 / CYL-009

Implement floor provenance before changing starting points. Use the
review's ten-row table as expected metadata, and independently check
inclusion and the source of each least claim. Exercise inclusive plateaus,
a newly confirmed 48 feeding 96, and a no-hit divisor interval with an
unresolved candidate preventing transfer. Reconcile clipped wheel
boundaries; distinguish inherited exclusions from observed census.

Preserve historical model predictions. A new record names its floor,
coverage, selection policy, cutoff, conditioning assumptions and rate
source. Remove the unsupported independent-Gamma interpretation or
justify a joint calibration respecting nested/shared solution sets and
outcome-based selection. Cutoff sensitivity is diagnostic, not a proof
of truncation error.

Evaluate plans against full-segment closure, not just encounter time.
Recompute remaining distance from committed coverage. Version plan inputs
and adoption so resume cannot silently change cursor meaning. Reject gains
caused solely by a changed workload, stale median, omitted forced prime,
lost census semantics or uncertified conditioning floor.

## Recording outcomes

Update [README.md](README.md) with the appropriate disposition and links
to implementation revision, exact test evidence, paired timings and
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md). Accepted measurements also
belong in [BENCHMARKS.md](../BENCHMARKS.md).

Record failures as carefully as wins. Preserve the dated Codex report;
later corrections/conclusions are addenda or linked follow-ups. No
optimization result authorizes a campaign start, constitutes discovery
evidence, or supplies a new OEIS term.
