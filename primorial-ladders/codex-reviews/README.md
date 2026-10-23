# Primorial ladders: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
Follow [the permanent review convention](../../CODEX_REVIEWS.md).
Codex reviews are always static and never use the GPU.

The [2026-10-20 review](2026-10-20-static-review.md) covers A115785,
A115786 and A145743, their recorded discoveries and actual open filters,
mathematical work sharing, model corrections and proof-safe coverage.
Only documentation was edited; no proposal was implemented or measured.

| ID | Finding | Disposition | Evidence |
|---|---|---|---|
| [PML-001](2026-10-20-static-review.md#pml-001-share-the-square-shift-sieve-with-the-prime-start-sibling) | Common square-shift sieve for A145743 and A092120 | Deferred | Exact shared forms and approximately 1.54× aggregate wheel-candidate saving; substantial catch-up interval and no runtime measurement |
| [PML-002](2026-10-20-static-review.md#pml-002-model-the-composite-start-domain) | Subtract prime-start intensity from the A145743 model | Proposed | Exact local-factor ratio; conditional BH intensity correction of approximately 7.5–8.2% at the saved cursor |
| [PML-003](2026-10-20-static-review.md#pml-003-proof-safe-settlement-domain-tests-and-carried-coverage) | Proof-gated settlement, composite-domain decisions, capped-run carry and cursor adoption | Proposed | Source-level correctness obligations; historical evidence has no unproved required values |
| [PML-004](2026-10-20-static-review.md#pml-004-bound-model-tails-and-complete-the-admissibility-argument) | Finite-collision tail bounds and composite-domain admissibility | Proposed | Mathematical assurance; no additional candidate pruning or measured speedup |
| [PML-005](2026-10-20-static-review.md#pml-005-a-bounded-larger-wheel-option-and-a-conditioned-planner) | Full-53 wheel construction, eight-class alternative and actual-floor planning | Deferred | Exact 53/38 candidate reduction; larger tables or multiple classes and much longer confirmation intervals; no measured better plan |

Claude should link implementation attempts, including failures, from this
ledger to [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md). Accepted
measurements belong in [BENCHMARKS.md](../BENCHMARKS.md). Preserve the dated
report as historical analysis; equivalence proofs alone do not establish
runtime improvement or completed validation.
