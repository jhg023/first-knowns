# Codex mathematical reviews: factorial-ladders

Static mathematical analysis by Codex (OpenAI), following
[CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). No GPU use, project execution,
tests or benchmarks form part of this review. Claude implements and
validates selected proposals later.

| Report | Scope | Assessment |
|---|---|---|
| [2026-10-20](2026-10-20-static-review.md) | A177013, A177014 and rider A226935 | The major known work reductions are already present. A new finite-collision argument bounds the model's truncation error; a more complete wheel planner remains an unmeasured investigation. No substantial new speedup or one-day median is established. |

| Finding | Proposal | Disposition | Implementation evidence |
|---|---|---|---|
| [FAC-001](2026-10-20-static-review.md#fac-001) | Bound the singular-series tail using the finite factorial-collision product | Proposed; proved error bound, no sweep speedup | None |
| [FAC-002](2026-10-20-static-review.md#fac-002) | Distinguish density-prefix wheel selection from a complete constrained subset search | Proposed investigation; no better current plan demonstrated | None |
| [FAC-003](2026-10-20-static-review.md#fac-003) | Price shorter confirmation segments against actual n=19 throughput | Already documented, unbuilt; mathematical coverage handoff clarified | Existing optimization-log item 5, no new measurement |
| [FAC-004](2026-10-20-static-review.md#fac-004) | Reuse period-coordinate patterns in later in-block rounds | Proposed donor transfer; modest wide-record gain measured only in clique-ladders | None in factorial-ladders |

Keep the dated report as the analysis snapshot. Record later attempts and
their results in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), then update
this ledger with links to the accepted or rejected evidence.
