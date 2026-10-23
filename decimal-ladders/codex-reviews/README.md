# Codex mathematical reviews: decimal-ladders

These reviews are authored by **Codex (OpenAI)**. They supplement the existing
Claude-authored project documentation; they do not change that documentation's
authorship or imply that Codex implemented the engines.

Codex's role here is **always static mathematical and algorithmic analysis**.
Codex does not use the GPU, import or execute the hunt engines, run oracles,
tests, benchmarks or campaigns, or implement the proposed optimizations. The
reports distinguish proofs from repository observations and unmeasured
performance hypotheses. See the repository policy in
[CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

## Review index

| Review | Families reviewed | Main result |
|---|---|---|
| [2026-10-20 static review](2026-10-20-static-review.md) | A305740 and A153431 | A settled sibling term permits removing one of A153431's four remaining classes modulo 10 below an exact endpoint. The existing odds model also needs to condition on that excluded class before its median is used to predict time. |

## Finding register

The statuses below are the current handoff state, not new measurements.

| ID | Finding | Status | Implementation or measurement record |
|---|---|---|---|
| [DEL-001](2026-10-20-static-review.md#del-001) | Exclude A153431 candidates divisible by 10 below 10 times A305740 a(18), and handle the valid endpoint explicitly | **Proposed; not implemented.** The pruning theorem is proved in the review, conditional on the repository's recorded least-term claim. The opportunity was already identified in the project's optimization log. | Existing proposal: [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), “Priced and declined,” item 5, updated 2026-09-29. No implementation or measured result is recorded for this proposal. |
| [DEL-002](2026-10-20-static-review.md#del-002) | Condition A153431's forecast on the sibling's now-known empty residue class and guaranteed endpoint | **Proposed; not implemented.** Algebraic relation between the model intensities is derived in the review; the probability interpretation remains a model. | No implementation or measured result. Keep this separate from DEL-001's exact reduction in candidate work. |

Claude should update this register when an implementation, rejection or
measurement exists, citing the dated entry in
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md). Do not mark a finding implemented
because its proof is complete, or measured because a donor project or a paper
work count suggests a gain. Keep the dated review as the historical record;
append a dated correction if a premise or conclusion changes.

Both families were inspected. The review also records why already-implemented
forcing, sibling floors and plateau handling are not additional discoveries,
and why it does not propose a new large speedup for the current A305740 a(19)
search.
