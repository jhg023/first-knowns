# Product cliques: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
Follow [the permanent review convention](../../CODEX_REVIEWS.md).
Codex reviews are always static and never use the GPU.

The [2026-10-20 review](2026-10-20-static-review.md) covers A034881
and A219761, actual campaign state, mathematical reuse, newer periodic
representations, model tails and proof-safe greedy promotion.
Only documentation was edited. No proposal was implemented or measured.

| ID | Finding | Disposition | Evidence |
|---|---|---|---|
| [PRC-001](2026-10-20-static-review.md#prc-001-reuse-periodic-words-and-revisit-wide-round-storage) | Later periodic-word and folded-round representations | Proposed | Exact modular identities; 1.019× periodic donor result and separate wide donor results, all unmeasured on this project |
| [PRC-002](2026-10-20-static-review.md#prc-002-refilter-a-complete-segments-full-run-suffix) | Refilter a completed segment's full-run suffix after a find | Deferred | Monotone form inclusion proves discovery coverage; no pre-find gain and at most one old segment avoided |
| [PRC-003](2026-10-20-static-review.md#prc-003-separate-the-quadratic-character-from-the-model-tail) | Character extraction for the quadratic model; finite collision bounds | Proposed | Exact Euler-product identity and rigorous bounds on the accelerated remainder; no new forecast or hunt-rate claim |
| [PRC-004](2026-10-20-static-review.md#prc-004-proof-gated-promotion-and-optional-partial-factor-certificates) | Proof-gated promotion and partial-factor certificate option | Proposed | Source permits unproved settlement; partial known-factor inequality is sufficient but its cost benefit is unmeasured |
| [PRC-005](2026-10-20-static-review.md#prc-005-prove-that-no-further-prime-is-forced) | Global nonforcing theorem for every valid future prefix | Proposed | Explicit surviving classes, including the self-square condition and prime-equality exceptions; mathematical assurance only |

Claude should link later attempts, including failures, to
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), and accepted measurements
to [BENCHMARKS.md](../BENCHMARKS.md). Preserve this dated report as
historical analysis. A mathematical equivalence does not establish
runtime improvement or completed validation.
