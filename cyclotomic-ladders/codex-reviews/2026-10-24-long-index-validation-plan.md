# Long A072942 indices: Claude experiment plan

> **Authorship:** Codex (OpenAI), 2026-10-24. Companion to the
> [static follow-up](2026-10-24-long-index-followup.md). This is future
> work, not an executed benchmark or permission to alter a running hunt.
> The source, proofs, configurations, limits, and hashes are in that report.

## Objective and success criteria

Find a real improvement in the time to a **confirmed least value** at
n = 60, 72, 84, 96, and 90. Do not equate fewer wheel candidates with
an identical overall speedup. A 1.2x improvement is still useful if
measured, but it does not satisfy the owner's wish to avoid days at the
hardest indices. Keep those two conclusions separate in the result.

Start with CYL-011: explicit replacements for weak wheel primes using
strong cyclotomic primes above 89. Defer CYL-012's larger representation
work until there is an operation-count and memory argument that can beat
the current engine at an actual campaign shape.

Use the regular Python installation. Do not create or borrow a virtual
environment. The project retains its five public Python roles, independent
oracle, proof route, checkpoint/evidence protocol, and frozen score.
Scratch harnesses belong outside the public project surface.

This report is not an instruction to start a campaign. Only the owner
does that. A later implementation session should follow the active-project
rules and short invocation limits in [CLAUDE.md](../../CLAUDE.md) and the
paired measurement rules in [OPTIMIZATION.md](../../OPTIMIZATION.md).
GPU timing cannot be meaningfully compared while the owner's live hunt
is competing for the same device; preserve that run and schedule tests
appropriately rather than silently disrupting it.

## Experiment 1 — explicit wheel alternatives

Use the exact level triples and constraints from CYL-011. Preserve the
old configuration as an explicit control. Suggested order:

| Priority | Configuration | Why it is worth the first test |
|---|---|---|
| 1 | n = 72 balanced | 1.5272x candidate-count reduction at 0.9959x period; no existing checkpoint at review time |
| 1 | n = 84 balanced | 1.3676x count reduction at 0.2085x period; much smaller completion interval |
| 2 | n = 96 balanced | 1.5632x count reduction at 0.1951x period |
| 2 | n = 90 balanced and short | 2.0101x at 0.6985x period versus 1.7736x at 0.0411x period; compare rate and completion granularity |
| 3 | n = 60 balanced and short | 1.4008x at 0.8595x period versus 1.1774x at 0.2714x period; evaluate off the active checkpoint |
| Conditional | Aggressive 96 and 90 | Larger count factors but expensive completion units; require a positive completion-time case |

Initially keep q2 = 8192, the same six-form device predicate, the same
exception policy, and pb = 256. Allow necessary derived table/window
depth and launch decomposition to follow the explicit wheel, recording
every resulting change. These are part of the cost of the wheel. Do not
hide an unfavorable table cost by separately changing the predicate.

### Correctness before timing acceptance

1. Independently establish each prime's forbidden roots and count
   gcd(n,q-1), including zero, q dividing n, and unit transformation.
   Check the explicit noncontiguous level partitions, not just the
   partition returned by a heuristic.
2. Verify no duplicate wheel primes, no overlap with the forced unit,
   and no missing prime in the union of wheel and non-wheel sieve.
   Every removed wheel prime returns to the latter; every added prime
   remains represented exactly once mathematically.
3. Compare complete sorted survivors on identical absolute half-open
   intervals with the original CPU engine/oracle. Include populated
   fixtures, no-hit fixtures, the exception boundary, period boundaries,
   known rediscoveries, and representative high campaign bases.
4. Exercise integer limits, queues and overflow handling, independent
   certificate checks, and the launcher gates applicable to the final
   change. No performance result excuses changed acceptance semantics.

Changing a wheel changes the meaning of a launch index. The existing
score's first 16 launches cannot become the common workload for two
different wheels. Preserve its existing frozen shapes and fingerprints;
add a separately documented absolute-interval comparison with independent
expectations. Do not regenerate a fingerprint from a changed engine and
treat agreement with itself as parity. Keep any sampled-slice throughput
explicitly separate from completed contiguous coverage.

### Record the cost that determines the decision

For each arm record source hashes, filter/base, unit, ordered wheel,
q2, pb/live periods, record representation, launch decomposition, and
exact common workload. Use paired interleaved rounds with an A/A control
and sufficient repetitions to distinguish the ambient noise already
observed at n = 60. Keep each invocation under the repository cap.

Record setup/table memory, generated-candidate count, window depth,
window/in-block time, generated-tail time, Fermat time, survivor rate,
host core-seconds, launches per full segment, and full completion cost.
Use bounded chunks and aggregate when a complete production segment
cannot fit one invocation. State whether completion cost is measured or
extrapolated; sampled launch time alone does not establish it.

Reject a candidate configuration if it changes the survivor predicate,
fails a representation bound, expands work outside the stated interval
without pricing it, or improves a density-normalized kernel score while
worsening the relevant time to confirmed coverage. A result inside A/A
noise is inconclusive. Record a valid slower result as rejected, including
the stage that paid for the theoretically attractive count reduction.

## Experiment 2 — choose from a bounded set of useful wheels

Only after explicit alternatives have an implementation and timing case,
extend the planner's prime universe and consider a bounded set of
exchanges. Raising `WHEEL_TOP` alone leaves the current nested-prefix
heuristic in place. Keep a small set of plans that trade candidate density,
table/decomposition cost, and numerical segment size; retain the present
plan and the named alternatives as candidates.

Measure the per-filter cost model instead of assuming a donor's width
curve or the old window-prime count still applies. In particular, moving
a strong prime into the wheel removes it from the window's best-killer
list. Compare pb = 128/160/256 where relevant; consider shorter widths
only with measurements at that filter. The extra aggressive 90 wheel is
a latency-sensitive research arm, not the default merely because it
generates fewer candidates per x.

Recompute completion cost using the actual half-open intervals. At a
known first candidate X, the containing segment ends at
`B + S*(floor((X-B)/S)+1)`. For planning, integrate or sample the stored
distribution with explicit model limitations, and condition only on
committed no-hit coverage. Record the 24-hour and 6-hour coverage cases
separately from the average completion objective. Do not call a median
scenario a deadline guarantee.

## Experiment 3 — price the interval CRT join before building it

The follow-up gives an exact two-factor CRT interval join: sort
`A^(-1)*b mod B`, then use one or two circular ranges for each allowed
residue modulo A. A successful design must avoid generating all pairs
outside the requested numerical tile.

Before device implementation, provide for at least n = 90 and n = 96:

- Explicit factor groups, allowed-residue counts, all table/index sizes,
  build time estimate, and memory budget including duplicates and queues.
- Work per tile: scanned first-level residues, range searches, expected
  and worst-case emitted pairs, and any third-factor work.
- How a tile spans CRT periods, how every candidate appears exactly once,
  and how original x is reconstructed without overflow.
- The amount of work removed relative to the best measured CYL-011 arm,
  and the additional memory traffic/control work introduced.
- A common numerical completion boundary across all class streams, plus
  a checkpoint/replay design that can prove the next boundary is complete.

Reject a design that needs to enumerate the whole huge wheel and clip
afterward, materializes an infeasible Cartesian residue product, or
assumes multiplicative subgroup order is a shorter additive period.
An identity demonstrating completeness alone does not demonstrate speed.

If a design survives this paper analysis, test a small independent exact
fixture before a bounded device prototype. Its results remain a new
representation experiment; do not combine them with unmeasured primality
changes or use a tiny fixture's ratio as the campaign prediction.

## Rollout and reporting

The n = 60 campaign was active at review time. The current launcher
rejects changed W and has an outstanding partial-accounting migration
issue under CYL-007. Work on isolated temporary state for migration tests.
Preserve the committed absolute boundary and evidence; replay or reconcile
all uncommitted pending candidates, counters and census consistently.
Interrupt/restart cases must produce the same coverage and discoveries
as an uninterrupted controlled fixture. A fraction of a completed launch
list cannot be converted to an equally sized numerical prefix.

For a final code change, complete the applicable public
`python launch.py --selftest` and `python score.py` validation, with the repository's bounded
invocation procedure where required. This static review ran neither.

Update the finding ledger with each tested configuration, source revision,
correctness evidence, paired ratios, measured versus extrapolated completion
cost, and kept/rejected/inconclusive outcome. Keep the original dated
reports immutable. Report plainly whether the result offers a moderate
improvement or actually reaches the scale required to avoid days. No
candidate-count calculation in this plan establishes the latter.
