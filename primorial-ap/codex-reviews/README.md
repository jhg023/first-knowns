# Primorial AP: Codex mathematical reviews

Authored by **Codex (OpenAI)** at the repository owner's direction.
Follow [the permanent review convention](../../CODEX_REVIEWS.md).
Codex reviews are always static and never use the GPU.

The [2026-10-20 static review](2026-10-20-static-review.md) covers A053647,
the recorded terms through a(18), the independent a(19) frontier, sieve
work, proof and coverage requirements, and the saved model.
Only documentation was edited; none of the proposals was implemented or
measured in this review.

| ID | Finding | Disposition | Evidence |
|---|---|---|---|
| [PAP-001](2026-10-20-static-review.md#pap-001-stop-sieving-dead-words-and-use-the-exact-interval-tail) | Dense prefix followed by live-word or live-candidate sieving, using normalized interval roots | Proposed | Exact residue and complete-period work arguments; no runtime measurement |
| [PAP-002](2026-10-20-static-review.md#pap-002-close-the-per-term-low-pass-and-alignment-gaps) | Per-term small-value coverage, aligned engine start, and low-pass discovery handling | Proposed | Source control-flow gap; no missed term demonstrated |
| [PAP-003](2026-10-20-static-review.md#pap-003-clarify-the-prescribed-difference-and-bound-the-model-tail) | Correct the minimum-difference explanation and bound the truncated singular series | Proposed | Mathematical counterexample and rigorous tail bound; no search speedup |

Claude should update these dispositions with links to implementation
commits and [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), including failed
attempts. Relevant accepted measurements also belong in
[BENCHMARKS.md](../BENCHMARKS.md). Preserve this dated report as the
historical static analysis; a proof of equivalence alone does not establish
runtime improvement or completed validation.
