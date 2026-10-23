# Codex mathematical reviews: dickson-ladders

These are Codex-authored static mathematical reviews under
[CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex does not use the GPU,
execute project code, run tests or benchmarks, or implement these proposals.
Claude owns any later implementation and authorized validation.

| Report | Scope | Assessment |
|---|---|---|
| [2026-10-20 static review](2026-10-20-static-review.md) | A247965, current a(14) search | Shared fold patterns remove a mathematical source of table duplication; the current filter also favors a different single fold by candidate count. A larger factored-wheel redesign is plausible but unmeasured. No one-day speedup is established. |

| Finding | Proposal | Disposition | Implementation / validation evidence |
|---|---|---|---|
| [DKL-001](2026-10-20-static-review.md#dkl-001) | Share canonical sieve patterns across fold offsets using a modular phase | Proposed; exact equivalence proved, runtime unmeasured | None |
| [DKL-002](2026-10-20-static-review.md#dkl-002) | Reconsider the automatic fold at n = 14: prime 19 versus 17 | Proposed; 19/17 candidate-rate ratio, not a measured speedup | None |
| [DKL-003](2026-10-20-static-review.md#dkl-003) | Extend to factored CRT generation and period windows without copying linear-form root limits | Proposed; structural investigation, no chosen production plan | None |
| [DKL-004](2026-10-20-static-review.md#dkl-004) | Omit empty kill sets and order equal-cost rejection tests by selectivity | Proposed; modest secondary opportunity | None |
| [DKL-005](2026-10-20-static-review.md#dkl-005) | Repair the singular-series tail claim and condition forecasts on saved coverage | Proposed; model correctness and optional arithmetic acceleration | None |
| [DKL-006](2026-10-20-static-review.md#dkl-006) | Replace large sparse bit rows with a small mask plus an exact root list | Proposed; exact representation, unmeasured transfer | None |

Keep the dated report as the historical analysis. Record later attempts,
including failures, in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), and
link accepted measurements in [BENCHMARKS.md](../BENCHMARKS.md) from this
ledger. A proved candidate reduction is not a measured runtime improvement.
