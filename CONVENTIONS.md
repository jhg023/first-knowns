# CONVENTIONS — the project template every hunt follows

Every project in this repository is built to the same skeleton. The point
is not uniformity for its own sake: it is that **every claim rests on
machinery that has been made hard to fool**, and that a reader who has
understood one project can audit all of them.

## The five files

| file | role |
|------|------|
| `*_reference.py` | **The oracle.** A slow, obviously-correct implementation using only trusted library primitives (sympy). Holds the frozen table of known values from the literature. Never optimized, never clever. Gates G1/G2 live here: the oracle must reproduce every frozen known from scratch. |
| `*_search.py` | **The CPU engine.** An independent fast implementation (numpy). Gated against the oracle on windows where both can run (survivor sets must match exactly), and required to re-derive known values end-to-end. |
| `*_gpu.py` | **The GPU engine.** CuPy RawKernel(s) implementing the same mathematics a third time. Never trusted alone: a parity gate pins its output stream bit-for-bit against the CPU engine on *populated* windows at multiple heights (an empty-vs-empty comparison is vacuous and does not count), including the numeric-ceiling zone. The GPU proposes; the host verifies. |
| `launch.py` | **The campaign.** Checkpointed (atomic writes, config-keyed cursors, resume redoes at most one segment), canary-alarmed (the stream must rediscover designated known values in-flight or halt), with a discovery protocol (below), timestamped dopamine logging, and graceful Ctrl+C. |
| `score.py` | **The un-gameable benchmark.** Prints `SCORE` (end-to-end Mitems/s on a frozen workload) only if every gate is green AND the run reproduces a frozen work fingerprint — exact result count + checksum. An engine that skips work or breaks correctness scores 0. Optimize under the score, never around it. |

Plus documentation: `README.md` (problem, mathematics, model, usage),
`RESULTS.md` (verified finds + evidence pointers), `BENCHMARKS.md`
(score ledger), `OPTIMIZATION_LOG.md` (every attempt → measurement →
kept/rejected, including the failures).

## The gate discipline

- All gates green **before and after every change**. No exceptions for
  "obvious" changes; the log of caught regressions says otherwise.
- **Two independent implementations of the hot path**, never one calling
  the other, pinned by parity gates on populated windows.
- **Canaries**: production streams must organically rediscover known
  values placed in their path (and the launcher preludes with dedicated
  rediscovery mini-hunts). A stream that cannot find what is known is
  not allowed to report what is unknown.
- **Planted drills**: the comparator is itself tested with deliberately
  corrupted data (it must catch the plant), and the discovery protocol
  is tested with a fake claim (it must reject) and with a genuine known
  (it must accept) — both directions, every selftest.
- **Resume drill**: a split stream must equal the unsplit stream.

## The discovery protocol

A candidate find must survive **three independent confirmations**:

1. the engine-side primality chain (huntlib's deterministic Miller-Rabin,
   with its validity bound stated and checked against the value sizes);
2. an independent implementation (sympy's BPSW);
3. a from-scratch re-derivation by different machinery (typically an
   alternate-alignment re-sieve with a different wheel).

plus a **factor witness** for the composite that bounds the claim, so the
evidence JSON is checkable by anyone with a calculator. Verified finds
are recorded in `evidence/`; any disagreement between the three legs is
an engine bug by definition and halts the campaign (exit 2). Discoveries
are never announced from inside the pipeline — a human reviews the
evidence first.

## The odds model

Every hunt ships a quantitative expectation model (typically
Bateman-Horn-style with numerically computed singular series), gated by
validation against the known values it did not help find: their model
quantiles must scatter — a model whose knowns all sit at quantile ~0 or
~1 is wrong and may not be used to plan. Predictions (median locations,
probability-by-depth) are stated in the README *before* the run, and the
finds are scored against them after.

## Logging taxonomy

`[STAGE]` phases; `[STATUS]` heartbeat with position, rate, live model
odds, ETA; `[MILESTONE]` decade crossings; `[NEAR]` individually-logged
near misses with campaign ordinals; `[CANARY-GOLD]` expected
rediscoveries; `[DISCOVERY]` verified finds; `[ALARM]` halts. Timestamps
on everything; ASCII only.

## Numeric hygiene

State every ceiling (64-bit value caps, primality-test validity bounds)
as an enforced constant, not an assumption. Parity-gate at the ceiling.
Raising a ceiling is a new engine version: new gates, new fingerprint,
log entry.
