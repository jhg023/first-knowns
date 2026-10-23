# Primorial runs: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
Follow [the permanent review convention](../../CODEX_REVIEWS.md).
Codex reviews are always static and never use the GPU.

The [2026-10-20 review](2026-10-20-static-review.md) covers all three
families, their exact-run definitions, historical evidence, current
checkpoint coverage, one-day confirmation economics and proof obligations.
Only documentation was edited. No proposal was implemented or measured.

| ID | Finding | Disposition | Evidence |
|---|---|---|---|
| [PMR-001](2026-10-20-static-review.md#pmr-001-plan-for-a-confirmed-result-before-the-deadline) | Plan for completed coverage within a day | Proposed | Current A257466 segment takes 55.7 hours at its stored rate; an already measured smaller wheel closes intervals in about 1.39 hours |
| [PMR-002](2026-10-20-static-review.md#pmr-002-prove-exact-index-exclusions-before-committing-coverage) | Proof-safe exact-run exclusions, settlement and cap handling | Proposed | Source-level gaps in PRP classification, failed-certificate settlement and dynamic cap handling; no historical missing term demonstrated |
| [PMR-003](2026-10-20-static-review.md#pmr-003-bound-the-model-tail-and-complete-exact-run-admissibility) | Finite-collision model bounds and exact-run admissibility | Proposed | Mathematical bounds for both terms of the intensity subtraction and a conditional exact-run infinitude argument; no new density reduction |

Claude should link later implementation attempts, including failures, to
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), and accepted measurements
to [BENCHMARKS.md](../BENCHMARKS.md). Keep this dated report as historical
analysis. A proof of equivalence does not constitute measured speedup or
completed implementation validation.
