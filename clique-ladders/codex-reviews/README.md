# Codex mathematical reviews: clique-ladders

These reports are authored by **Codex (OpenAI)**. They supplement the
Claude-authored implementation and its historical records. Codex's role is
**always static mathematical and algorithmic analysis**: no GPU use, hunt
execution, project imports, tests, benchmarks or implementation of the
proposals. See [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

## Review index

| Review | Scope | Main conclusion |
|---|---|---|
| [2026-10-20 static review](2026-10-20-static-review.md) | All six primary families and five affine-derived entries | All six families have a proof of local admissibility. No new substantial search speedup is established. A119752 has more saved contiguous coverage than the results document reports; current forecasts and benchmark shapes must use the actual prefixes and coverage. |

## Finding register

| ID | Finding | Disposition | Implementation or measurement evidence |
|---|---|---|---|
| [CLI-001](2026-10-20-static-review.md#cli-001) | Prove local admissibility for every valid prefix of all six families; treat a modular obstruction as an invariant failure | **Proposed.** The theorem is proved in the report; documentation and diagnostic changes are not implemented. It provides no new candidate restriction or measured speedup. | No implementation record. |
| [CLI-002](2026-10-20-static-review.md#cli-002) | Reconcile real prefixes, A119752's completed coverage, and current-filter forecast/score provenance | **Proposed.** Saved data and source establish the mismatch. The current-prefix model and new benchmark shapes remain future implementation work. | Existing related backlog: [RESULTS.md](../RESULTS.md), “In progress”; [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), “Open, priced, unbuilt,” items 1a and 3. No new measurement. |
| [CLI-003](2026-10-20-static-review.md#cli-003) | Retain and refilter a completed segment's candidates after a greedy promotion | **Deferred.** Sound in principle, already priced and declined in the project log. This review supplies the exact coverage argument and keeps the original small-benefit assessment. | [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 2 item 5: modeled saving of 0.1–0.7% of the following term's clock at the filters considered; not implemented. |

Claude should update this register when a proposal is implemented,
validated, declined or superseded, linking the dated
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) entry and any resulting
[BENCHMARKS.md](../BENCHMARKS.md) measurement. Keep the dated report as a
historical record; later corrections belong in a dated addendum or linked
follow-up. A proved theorem, a candidate-count argument, and a measured
runtime improvement are different evidence classes.
