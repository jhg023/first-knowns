# Codex reviews: plus-two-cliques

These independent mathematical reviews are authored by **Codex (OpenAI)**.
They follow [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md): always static, never
GPU work, project execution, benchmarks or campaigns.

Latest report: [2026-10-20 static review](2026-10-20-static-review.md).
It covers A083518 and A083519. Neither has a derived entry in this project.
No proposal below was implemented or measured by this review.

| ID | Proposal | Disposition | Report | Implementation evidence |
|---|---|---|---|---|
| PTC-001 | Optimize the completed numerical boundary at a one-day deadline, with explicit shorter-segment and migration requirements | Proposed | [Deadline analysis](2026-10-20-static-review.md#ptc-001) | Current rates and exact thresholds; proposed widths unmeasured at the real prefix |
| PTC-002 | Bound the singular-series tail using coefficient divisors and pairwise differences | Proposed | [Model bound](2026-10-20-static-review.md#ptc-002) | New proof; no model execution or changed forecasts |
| PTC-003 | Give a complete all-prime proof that no prime above 3 can become forced | Proposed | [Proof assurance](2026-10-20-static-review.md#ptc-003) | Strengthens an existing documented claim; no additional candidate thinning |
| PTC-004 | Reuse a completed segment's full-run suffix after testing each newly appended form | Deferred | [Known idea and refinement](2026-10-20-static-review.md#ptc-004) | Already priced and declined in OPTIMIZATION_LOG.md, lines 513–518 |

Claude should update dispositions after separately authorized implementation,
linking attempts and measurements in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md)
and [BENCHMARKS.md](../BENCHMARKS.md). Preserve this report as the original
analysis; later measurements do not retroactively become its evidence.
