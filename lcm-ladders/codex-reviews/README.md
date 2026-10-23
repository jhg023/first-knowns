# Codex reviews: lcm-ladders

These independent mathematical reviews are authored by **Codex (OpenAI)**.
They follow [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md): always static, never
GPU work, project execution, benchmarks or campaigns.

Latest report: [2026-10-20 static review](2026-10-20-static-review.md).
It covers A078502, A074200 and their derived entries A093554 and A093553.
The proposals below have not been implemented or measured by this review.

| ID | Proposal | Disposition | Report | Implementation evidence |
|---|---|---|---|---|
| LCM-001 | Replace exact residue-list confirmation with an equivalent scaled-interval predicate | Proposed | [Proof and handoff](2026-10-20-static-review.md#lcm-001) | None; destination performance unmeasured |
| LCM-002 | Express total forced divisibility monotonically and safely carry fully resolved published-term coverage | Deferred | [Proof and prerequisites](2026-10-20-static-review.md#lcm-002) | Carrying coverage was already unbuilt in OPTIMIZATION_LOG.md, lines 930–933 |
| LCM-003 | Preserve period coordinates in later in-block rounds | Proposed | [Donor transfer](2026-10-20-static-review.md#lcm-003) | Donor measurements only; no LCM implementation |
| LCM-004 | Bound the omitted singular-series tail and independently relate it to the linear-family series | Proposed | [Model assurance](2026-10-20-static-review.md#lcm-004) | Mathematical proof in the report; model output unchanged |
| LCM-005 | Explicit wheel-67 decomposition under relaxed first-level and partition limits | Proposed | [Constructive refinement](2026-10-20-static-review.md#lcm-005) | Candidate-count arithmetic only; existing open idea in OPTIMIZATION_LOG.md |
| LCM-006 | Reject repeated prime factors in an explicitly supplied unit | Proposed | [Correctness prerequisite](2026-10-20-static-review.md#lcm-006) | Source and existing-term counterexample; current default units remain squarefree |

Claude should update dispositions here after any separately authorized
implementation, with links to the corresponding attempts and measurements
in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) and
[BENCHMARKS.md](../BENCHMARKS.md). Preserve this dated report as the original
analysis; subsequent measurements do not retroactively become its evidence.
