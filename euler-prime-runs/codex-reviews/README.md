# Codex reviews: euler-prime-runs

These are Codex-authored static mathematical and algorithmic analysis reports
for Claude or a later implementer. Codex reviews always remain static: no GPU
use, engine or oracle execution, tests, benchmarks or hunts. They identify
missed mathematical reductions, necessary conditions and algorithmic changes;
they do not conduct kernel tuning. The workflow is
[CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

The dated report records what was known when it was written. Update this index
as work proceeds, keeping the report historical. A disposition should link to
the implementation and to the relevant entry in
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), including rejected experiments.
Do not turn a proposed speedup into a measured claim without destination
measurements, correctness gates and the appropriate frozen fingerprints.

| Finding | Proposal | Status | Analysis | Implementation | Measurement / disposition evidence |
|---|---|---|---|---|---|
| EUL-001 | Use the polynomial window sieve at A230663 index 19 as a dedicated A164926 a(20) candidate generator, with the exact shift and an independent Euler verifier | proposed | [2026-10-20 report](2026-10-20-static-review.md#eul-001-dedicated-polynomial-window-sieve-for-euler-a20) | None yet | None yet; donor measurements are identified in the report |
| EUL-002 | Use a one-sided compositeness screen below the census floor, retaining full independent verification where the result matters | proposed | [2026-10-20 report](2026-10-20-static-review.md#eul-002-one-sided-compositeness-screen) | None yet | None yet; an existing sibling implements the principle |
| EUL-003 | Make the legacy sieve filter follow the lowest open term, with a deliberate near-miss policy and configuration-aware migration | proposed | [2026-10-20 report](2026-10-20-static-review.md#eul-003-retire-the-fixed-filter-17-with-correct-migration) | None yet | None yet |
| EUL-004 | Incidental engineering observation: Euler still rebuilds its rung ladder despite unchanged inputs | proposed | [2026-10-20 report](2026-10-20-static-review.md#eul-004-incidental-observation-live-rung-ladder) | None yet | None yet; known repository pattern, not a mathematical finding |

The [2026-10-20 review](2026-10-20-static-review.md) was static only. It did not
run GPU work, import hunt modules, run tests or benchmarks, launch a campaign,
or change engines, checkpoints or evidence. Its one-day figures are conditional
model and rate-transfer calculations, not measured Euler performance.

Claude or the later implementer owns execution and validation. When
implementing, retain each finding ID in the optimization-log entry. Record
the tested filter, absolute window, survivor semantics, host workload, paired
ratio, fingerprint and outcome. If an idea is superseded, say by which finding
or implementation; if rejected, record why and whether the rejection is
measured or an unresolved assumption. Preserve the dated report's attribution:
it is Codex's analysis, not Claude's implementation record.
