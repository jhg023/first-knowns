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

**Making it fast is a separate discipline with its own document.** See
[OPTIMIZATION.md](OPTIMIZATION.md) for the process (measure the phase
split before touching code; interleaved paired A/B or the numbers are
noise; separate engine changes from benchmark-shape changes; price what
you decline) and for the catalogue of optimizations that have paid here,
with measured numbers and the rejected attempts. Two of its design rules
belong at the *start* of a project rather than the end: carry candidates
as `(k, off)` pairs so one engine spans the whole range instead of
growing a second engine at the machine-word boundary, and choose the
wheel that fits at every parameter the gate battery runs, not just the
production one.

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

**A discovery is a FIRST OCCURRENCE, and it is logged once (repo-wide).**
Every hunt has a *frontier*: the largest run length (or term index)
settled so far, seeded from the literature and from the launcher's table
of terms found in earlier campaigns, and **promoted at runtime** the
moment a longer run is verified — the launcher stores the promotion in
the checkpoint, so it survives a resume and needs no hand edit. Only the
first value beyond the frontier is a `[DISCOVERY]`; it is a(r') for every
unsettled r' up to its run (a run of 12 settles a(11) and a(12) at once,
each logged once). Every later value whose run is at or below the frontier
is a **census** event: if it beats the literature it is still verified and
evidenced exactly like a find, but it is logged as `[NEAR]` with a running
count per run length (`run-10 census #7 (a(10) settled at K)`), never as a
discovery again. A campaign that finds a(10) in its first minutes and
keeps running reports one discovery and then counts run-10 values as it
meets them; the counts per length are the campaign's census and belong in
`[STATUS]` and `[MILESTONE]` lines. Where this rule lives in code is one
function (`event_kind` in dickson-ladders), and the selftest drills it.

**The stop-on-discovery convention (repo-wide).** Every launcher
accepts `--stop-on-discovery`: once the discovery protocol confirms a
*frontier-extending* find — a first occurrence, in the sense above — the
campaign checkpoints, writes the evidence, logs a `[STAGE]` line, and
exits cleanly so a human can react before more GPU time is spent.
Rediscoveries of known values (canaries) and census repeats never
trigger the stop.

## The odds model

Every hunt ships a quantitative expectation model (typically
Bateman-Horn-style with numerically computed singular series), gated by
validation against the known values it did not help find: their model
quantiles must scatter — a model whose knowns all sit at quantile ~0 or
~1 is wrong and may not be used to plan. Predictions (median locations,
probability-by-depth) are stated in the README *before* the run, and the
finds are scored against them after.

## Logging taxonomy

`[STAGE]` phases; `[STATUS]` heartbeat with position, rate, survivor
count, the census counts per run length from the near-miss floor to the
current frontier, the number of finds, live model odds, ETA;
`[MILESTONE]` decade crossings *and* model-odds crossings (the hunt has
passed the point where the model put the next term with 25/50/75/90%
probability — "past the median" is worth a line); `[NEAR]`
individually-logged near misses and census repeats with their campaign
ordinal (`run-9 #12 of the campaign`), flagged when they are one value
short of the next term, a new campaign best, or the first of their length;
`[CANARY-GOLD]` expected rediscoveries; `[DISCOVERY]` verified first
occurrences, once each; `[ALARM]` halts. The point of the taxonomy is that
a human reading the log while the hunt runs can see every notable event
without a debugger: add a line for anything a person would want to know
happened, keep it in one of these categories, and never let a category
fire twice for the same fact. Timestamps on everything; ASCII only.

## Numeric hygiene

State every ceiling (64-bit value caps, primality-test validity bounds)
as an enforced constant, not an assumption. Parity-gate at the ceiling.
Raising a ceiling is a new engine version: new gates, new fingerprint,
log entry.

## Documentation template (binding for every project)

Four documents per project, with fixed section order, so a reader who
has read one project can navigate all of them.

**`README.md`** — sections in this order:

1. *Authorship disclaimer* (blockquote, first thing on the page): all
   code authored by Claude at the repository owner's direction.
2. *One-paragraph headline*: what is being hunted, and the standing
   result if there is one.
3. *Status line*: one of
   - `Status: ACTIVE` — the hunt is running; expect updates.
   - `Status: COMPLETE` — the stated range is exhausted; results final.
   - `Status: PAUSED — open to others` — not currently running; anyone
     is welcome to extend it (say exactly where the frontier stands).
4. *The problem* — definition, history, why it is open, prior frontier
   with attribution.
5. *The mathematics of the engine* — how the search actually works.
6. *The odds model* — predictions stated BEFORE the run, validation
   evidence, and (once results exist) how the finds scored against it.
7. *Running it* — exact commands and requirements.
8. *Trust* — pointer to this file plus anything project-specific.

**`RESULTS.md`** — every verified find in discovery order: the exact
integers, the verification performed, the factor witness, the evidence
file path, and the least-claim basis. Near-miss/census data and its
caveats. Ends with an "In progress" or "Final state" section.

**`BENCHMARKS.md`** — the SCORE ledger (frozen fingerprint stated) and
wall-clock tables at the scored rate.

**`OPTIMIZATION_LOG.md`** — every optimization attempt: change,
measurement, kept/rejected. Failures included; they are the record that
stops the next person from retrying them.

The top-level README carries one table row per project:
`| project | problem (one line, linked OEIS/reference) | status + headline result |`.
Keep the row's status word identical to the project README's status line.

Repo-wide hygiene: no personal or machine-specific information (names,
paths, hardware serials, local configuration) anywhere; hardware model
names used for performance context are fine.
