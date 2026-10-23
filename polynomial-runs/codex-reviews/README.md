# Codex reviews: polynomial-runs

These independent mathematical reviews are authored by **Codex (OpenAI)**.
They follow [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md): Codex is always
static and never uses the GPU or executes hunt code for this workflow.

Latest report: [2026-10-20 static review](2026-10-20-static-review.md).
It covers all four primary families and the A164926 relation. No proposal
below was implemented or measured during this review.

| ID | Proposal | Disposition | Report | Implementation evidence |
|---|---|---|---|---|
| POL-001 | Require proved exact classifications and certificate-gated settlement beyond the deterministic bound | Proposed | [Finding](2026-10-20-static-review.md#pol-001) | None; observed future proof obligation |
| POL-002 | Revisit the existing six-class wheel-to-59 design at the actual current filters, with completed-coverage pricing | Deferred | [Finding](2026-10-20-static-review.md#pol-002) | Already measured but unshipped: OPTIMIZATION_LOG round 3; no new measurement |
| POL-003 | Bound the model's collision-free tail and propagate it through the exact-run subtraction | Proposed | [Finding](2026-10-20-static-review.md#pol-003) | None; proved normalization bounds, not a runtime gain |
| POL-004 | Prove globally that the quartic never forces a prime above 3 | Proposed | [Finding](2026-10-20-static-review.md#pol-004) | None; strengthens the finite checks behind an existing claim |

Claude should preserve the dated report and update this ledger when a
proposal is implemented, rejected, or superseded, linking the corresponding
`OPTIMIZATION_LOG.md` record and its actual validation and measurements.
“Proposed” does not authorize a campaign start or imply a measured speedup.
