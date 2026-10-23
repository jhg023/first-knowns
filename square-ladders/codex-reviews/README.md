# Codex reviews of square-ladders

These are Codex-authored static mathematical and algorithmic reviews. They
are separate from the Claude-authored implementation and its measured
optimization history. Follow the repository's
[Codex review workflow](../../CODEX_REVIEWS.md).

**Codex reviews remain static: no GPU use, profiling, benchmarks, campaign
runs, or execution of the project's oracle or tests.** Implementation and
any later dynamic validation belong to Claude in an authorized development
session. A proposal here is not a measured speedup.

| Report | Reviewed source revision | Scope | State |
|---|---|---|---|
| [2026-10-20 static review](2026-10-20-static-review.md) | `f8fdb200c56a54aa5e207c146882f7d2d7b87224`; source hashes recorded in the report | A089761 at the current a(19) frontier; period-window sieve, representation and coverage constraints, host and proof-bound caveats | Static review complete; no implementation or measurements |

The dated report is the historical record of what Codex saw and proposed.
Claude should update the disposition table below as work proceeds, citing
the implementation commit, relevant tests, and a specific section of
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md). Preserve the original
report's distinction between mathematical deductions, historical
measurements, and unmeasured proposals.

| ID | Proposal or implementation prerequisite | Current disposition | Implementation / validation evidence |
|---|---|---|---|
| [SQR-001](2026-10-20-static-review.md#sqr-001-amortize-the-sieve-across-wheel-periods) | Replace repeated candidate prefix tests with a period-window sieve | Proposed; highest priority algorithmic investigation | None yet |
| [SQR-002](2026-10-20-static-review.md#sqr-002-separate-period-and-residue-with-explicit-bounds) | Carry the period separately from the within-period residue; price complete-segment coverage | Proposed; prerequisite for useful wide windows | None yet |
| [SQR-003](2026-10-20-static-review.md#sqr-003-preserve-the-coverage-claim-when-enumeration-changes) | Migrate the saved partial-period cursor without gaps or duplicate census | Proposed; required if SQR-001 or SQR-002 is implemented | None yet |
| [SQR-004](2026-10-20-static-review.md#sqr-004-cache-the-model-by-frontier-and-audit-the-actual-host-path) | Cache the model by frontier and preserve the existing host/device overlap | Proposed; secondary observation, no large speedup claimed | None yet |
| [SQR-005](2026-10-20-static-review.md#sqr-005-keep-proof-ceiling-work-separate-from-the-one-day-target) | Treat a future certificate-based ceiling extension separately | Deferred; current ceiling does not block the a(19) target | None yet |

No finding is implemented merely because its mechanism exists in a sibling
project. Mark an item implemented only after the square-specific
mathematics, coverage behavior, and validation are documented. A negative
result should also receive a linked disposition so the same experiment is
not proposed again without new evidence.
