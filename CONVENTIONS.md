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
| `launch.py` | **The campaign.** Checkpointed (atomic writes, config-keyed cursors, resume redoes at most one segment), canary-alarmed (the stream must rediscover designated known values in-flight or halt), with a discovery protocol (below), timestamped dopamine logging, graceful Ctrl+C — and **indefinite by default**: it runs until the last rung (the enforced ceiling), never stopping on its own before that (below). |
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
evidence JSON is checkable by anyone with a calculator. Verified first
occurrences are recorded in `evidence/` (and nothing else is — see the
census rule below); any disagreement between the three legs is an engine
bug by definition and halts the campaign (exit 2). Discoveries are never
announced from inside the pipeline — a human reviews the evidence first.

**A discovery is a FIRST OCCURRENCE, and it is logged once (repo-wide).**
Every hunt has a *frontier*: the largest run length (or term index)
settled so far, seeded from the literature and from the launcher's table
of terms found in earlier campaigns, and **promoted at runtime** the
moment a longer run is verified — the launcher stores the promotion in
the checkpoint (and saves the checkpoint at the end of that segment, so
the promotion never lives only in memory) and needs no hand edit. Only the
first value beyond the frontier is a `[DISCOVERY]`; it is a(r') for every
unsettled r' up to its run (a run of 12 settles a(11) and a(12) at once,
each logged once). Only discoveries are evidenced.

**The census is counted, not narrated (repo-wide).** Every other value
with a run at or above the project's census floor is a *census* event,
and there are exactly two kinds:

- **One value short of an open term** — a run r with a(r+1) still open
  (in a monotone hunt, r equal to the frontier; in a per-length hunt like
  euler-prime-runs, any r whose successor is unsettled). It gets one
  `[NEAR]` line with its census ordinal (`run 10 at k = K (run-10 #7 of
  the campaign; a(10) settled at K0; verified 3-way) -- ONE value short of
  a(11)!`), is verified by the cheap legs of the protocol as a running
  engine health check, and is **not evidenced**.
- **Everything below that** — a run r with a(r+1) already settled (run-7,
  run-8, and run-9 once a(10) has landed, run-10 once a(11) has landed,
  and so on) — is noise as an individual: it is **counted** in the
  checkpoint's per-length table and appears **only** in the census counts
  of the `[STATUS]` heartbeat and `[MILESTONE]` lines. No log line of its
  own, no evidence file, no near-miss record. The moment a term lands, the
  classification follows: run-9 values stop being logged the instant a(10)
  is verified.

The **evidence directory holds first occurrences only** — one JSON per
verified discovery plus the ledger. Census values are counts, and the
counts live in the checkpoint and the log. (Per-value census files and
near-miss `.jsonl` records written before this convention were retired
from the tree on 2026-08-18; they remain in the git history before commit
`3d01f95` for anyone who wants them.) Where this rule lives in code is one
function per project (`event_kind`), and each selftest drills it: beyond
the frontier → DISCOVERY, one short → NEAR, below → CENSUS, under the
floor → nothing.

**The 30-second heartbeat is mandatory (repo-wide).** Every launcher
logs a `[STATUS]` line every 30 s by default (`--heartbeat`), and that
line carries the census counts per run length from the floor to the
frontier in the shared format produced by `huntlib.hlog.census_str`
(`census 7:280 8:71 9:28 10:8`) — the one place a human reads how many
run-7s, run-8s, run-9s the campaign has met. `--status` prints the same
counts from the checkpoint.

**Campaigns run indefinitely; rungs mark progress (repo-wide).** A
launcher started with no arguments runs until it reaches the end of the
*last rung* and never stops on its own before that. There is no default
depth cap: the only natural end is the engine's enforced ceiling (the
numeric-hygiene constant), which is the last rung. Every launcher carries
a ladder of **rungs** — depths with names, taken from the odds model's
predictions stated before the run (Q1 / median / Q3 / P90 of every open
term) with the ceiling appended — logs a `[RUNG]` line as each is passed
("passed rung 5/17: a(11) median (7.18e16) — next: a(11) Q3 at 1.88e17"),
persists the passed rungs in the checkpoint, and shows the next rung with
its ETA in every `[STATUS]`. Rungs are for reading progress off the log,
not for stopping. The two deliberate stops are `--to` (a depth cap the
operator chose) and `--stop-on-discovery`; both are opt-in and neither is
a default. When a find changes what the campaign should be sieving for
(here: the filter follows the frontier, and a wider wheel re-denominates
the cursor by floor so coverage overlaps and never gaps), the launcher
makes that move itself and logs it as a `[STAGE]` line, so an unattended
run keeps hunting the next open term instead of crawling at a stale
setting.

**The stop-on-discovery convention (repo-wide).** Every launcher
accepts `--stop-on-discovery`: once the discovery protocol confirms a
*frontier-extending* find — a first occurrence, in the sense above — the
campaign checkpoints, writes the evidence, logs a `[STAGE]` line, and
exits cleanly so a human can react before more GPU time is spent. It is
opt-in; without it the campaign records the find and keeps running.
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

`[STAGE]` phases; `[STATUS]` the 30-second heartbeat with position, rate,
survivor count, **the census counts per run length from the floor to the
current frontier** (`census 7:280 8:71 9:28 10:8`, via
`huntlib.hlog.census_str`), the number of finds, live model odds, the next
rung and ETA; `[MILESTONE]` decade crossings *and* model-odds crossings
(the hunt has passed the point where the model put the next term with
25/50/75/90% probability — "past the median" is worth a line), also
carrying the census counts; `[RUNG]` a rung of the progress ladder passed,
with the next rung named; `[NEAR]` a value **one short of an open term**,
individually logged with its campaign ordinal (`run-10 #7 of the
campaign`), flagged as a new campaign best or the first of its length —
and *nothing shorter*: runs below that are counted in `[STATUS]` and never
get a line; `[CANARY-GOLD]` expected rediscoveries; `[DISCOVERY]` verified
first occurrences, once each; `[ALARM]` halts. The point of the taxonomy
is that a human reading the log while the hunt runs can see every notable
event without a debugger and is not buried under the ones that are not:
add a line for anything a person would want to know happened, keep it in
one of these categories, never let a category fire twice for the same
fact, and never narrate what the census counts already say. Timestamps on
everything; ASCII only.

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
file path, and the least-claim basis. The census as **counts per run
length** (from the checkpoint / `[STATUS]`), with caveats — never as
per-value listings. Ends with an "In progress" or "Final state" section.

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
