# Shift ladders: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
Follow [the permanent review convention](../../CODEX_REVIEWS.md).
Codex reviews are always static and never use the GPU.

The [2026-10-20 review](2026-10-20-static-review.md) covers A130003,
A110096, their named relatives, saved coverage, current search economics,
factored-wheel representations, proof ceilings and model-tail bounds.
Only documentation was edited. No proposal was implemented or measured.

| ID | Finding | Disposition | Evidence |
|---|---|---|---|
| [SHL-001](2026-10-20-static-review.md#shl-001) | Revisit a factored wheel at the deeper current frontier | Proposed | Constructive base-4 full-47 and base-2 full-59 geometry; fewer generated word positions but no measured transfer gain, and longer confirmation intervals |
| [SHL-002](2026-10-20-static-review.md#shl-002) | Extend the proof range with per-value certification and safe promotion | Proposed | Existing documented ceiling limit; certificate calls already exist but acceptance and actual-value bounds need strengthening |
| [SHL-003](2026-10-20-static-review.md#shl-003) | Bound the omitted geometric-orbit singular-series tail | Proposed | Finite collision product and rigorous log-tail intervals; mathematical assurance, not a hunt speedup |

Claude should link later attempts, including failures, to
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), and accepted measurements
to [BENCHMARKS.md](../BENCHMARKS.md). Preserve the dated report as a
historical record. A proved count reduction is not a measured runtime gain.
