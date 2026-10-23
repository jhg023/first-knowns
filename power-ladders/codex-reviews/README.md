# Power-ladders: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
These are historical static analyses under [the repository review convention](../../CODEX_REVIEWS.md).
Codex does not run the GPU, hunt code, models, or validation experiments.

| Report | Scope | Status |
|---|---|---|
| [2026-10-20 static review](2026-10-20-static-review.md) | All four power families; current evidence and coverage, semiprime domain sieve and model, proof safeguards, one-day planning | Reviewed; proposals below are not implemented by this review |

| ID / report | Finding | Disposition | Basis / implementation evidence |
|---|---|---|---|
| [POW-001](2026-10-20-static-review.md#pow-001-extend-the-semiprime-factor-state-beyond-the-wheel) | Carry an at-most-one-small-factor state through the zero-free branch's remaining sieve | Proposed | New mathematical pruning proposal; runtime unmeasured |
| [POW-002](2026-10-20-static-review.md#pow-002-plan-for-the-semiprime-domain-and-for-a-deadline) | Domain-aware wheel objective and complete-prefix deadline planning | Proposed | New planner analysis; no winning replacement measured |
| [POW-003](2026-10-20-static-review.md#pow-003-condition-the-semiprime-model-on-its-smaller-factor) | Replace independent semiprime density with smaller-factor branch local factors | Proposed | Heuristic model repair; no new forecast computed |
| [POW-004](2026-10-20-static-review.md#pow-004-preserve-unresolved-domain-and-primality-claims) | Unresolved large prime cofactor can be rejected; failed certificates still settle terms | Proposed | Correctness handoff; current evidence does not demonstrate a missing term |
| [POW-005](2026-10-20-static-review.md#pow-005-global-forcing-and-family-relations) | Complete forcing witnesses, admissibility, and limits of cross-family reuse | Proposed | Mathematical assurance; no additional density reduction |

Claude should update dispositions here with links to implementation and
`OPTIMIZATION_LOG.md` evidence, preserving the dated report. A proposed count
reduction is not a measured speedup. Only the owner starts campaigns.
