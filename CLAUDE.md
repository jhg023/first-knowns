# CLAUDE.md

Guidance for AI agents (and humans) working in this repository.

## What this repo is

Published, verified results from GPU hunts for open problems in
computational number theory, plus the machinery that produced them.
Every line of code here was authored by Claude at the repository owner's
direction; keep that audit trail honest — the disclaimer at the top of
each README stays.

## Rules

0. **No command an agent runs may take longer than 5 minutes**, and
   aim for under two. This is a hard cap, not a guideline. It applies to
   everything — gate batteries, A/B harnesses, sweeps, benchmarks — and
   it applies to the *whole* invocation, not to each step inside it.
   If a measurement does not fit, **cut it up**: fewer rounds, a
   narrower window, one configuration per invocation, results
   accumulated across several short runs rather than one long one.
   Long runs are also bad measurements: a 40-minute A/B in this repo
   straddled a GPU clock-regime change and had to be thrown away
   (OPTIMIZATION.md Rule 3). Short paired runs are both faster to
   supervise and more trustworthy.

   The production hunt itself (`python launch.py`) is the one exception:
   it is meant to run for days, it checkpoints every segment, and the
   owner starts it deliberately. Agents do not launch it.

1. **Read `CONVENTIONS.md` before touching any project.** The five-file
   skeleton (oracle / CPU engine / GPU engine / launcher / score) and
   the gate discipline are binding.
2. **Gates green before and after every change — for the ACTIVE project
   only.** Run `python score.py` in the project being worked on (today:
   dickson-ladders); commit only with that project's SCORE in the
   message. If a deliberate coverage change alters the benchmark
   fingerprint, update the fingerprint in the same commit and log it in
   that project's OPTIMIZATION_LOG.md.

   **Do not run another project's gates or benchmarks**, even when a
   change to `huntlib/` or a repo-wide convention touches its files. A
   paused or complete project (status in the top-level table) is not
   being advanced, its GPU time is the owner's, and every battery run is
   minutes of a GPU that may well be busy with the active hunt. Make the
   shared
   change, edit the paused project's files to match, and say in the
   commit message that its gates were NOT run. **Whoever resumes a paused
   project runs `python launch.py --selftest` and `python score.py`
   there FIRST**, before any new work — that is where a shared change is
   proved on that project, and it is a checklist item of resuming.
   The one exception: the owner asks for it.
3. **Never let the two engine implementations converge.** The CPU engine
   uses plain `%`; the GPU engine uses Barrett arithmetic. One must
   never call the other; parity gates depend on their independence.
   Superseded engine versions stay in the tree as parity references —
   they are how "the fast engine returns the identical stream" remains a
   checkable claim — but they must never be reachable from the campaign.
   One engine hunts; the others only ever appear in gates.
3a. **Before optimizing anything, read `OPTIMIZATION.md`.** Throughput
   sets the frontier, so every project here needs it; that file holds the
   process and the catalogue of what has actually paid, with measured
   numbers and the rejected attempts. The rules broken most often, stated
   here so they are unmissable:
   - **Measure the phase split first.** The one time this was skipped,
     work was aimed at a stale comment naming the wrong bottleneck (it
     said 80% cold; it was 83% hot). Two minutes of timers beat it.
   - **Interleave every A/B and re-check the fingerprint on every run.**
     Ambient GPU load swings absolute rates ~30%, and sequential sweeps
     invent cliffs that are not there. The ratio is the stable quantity.
   - **Re-sweep tuning constants after any structural change** — optima
     move; a constant tuned against the old design is now wrong.
   - **Never treat the cost model as evidence.** Use it to generate
     candidates and to price what you decline. It has mispredicted by 4x
     in both directions here.
   - **Do not grow a second engine at the machine-word boundary.** Carry
     candidates as `(k, off)` from the start so one engine spans the
     whole range (OPTIMIZATION.md §2.7).
   - **Price what you decline, and record the failures.** The rejects are
     what stop the next agent re-running a dead end.
4. **Oracles stay slow and boring.** sympy only. No optimization, ever.
5. **Discoveries are records, not announcements.** The pipeline writes
   evidence JSONs; humans decide what happens next. Never auto-submit
   to OEIS or anywhere else.
5a. **A discovery is a first occurrence, logged once; the census is
   counted, not narrated.** The launcher's frontier promotes itself at
   runtime when a longer run is verified and is stored in the checkpoint
   (saved at the end of that segment). Only discoveries are evidenced:
   **the evidence directory holds first occurrences only.** Every other
   value is census, and there are two kinds — a run **one short of an open
   term** (run 10 while a(11) is open) gets one `[NEAR]` line with its
   ordinal, verified but not evidenced; a run whose successor is already
   settled (run-7, run-8, run-9 once a(10) has landed, run-10 once a(11)
   has landed, and so on) is **counted only** — it appears in the census
   counts of the 30-second `[STATUS]` heartbeat and nowhere else: no line,
   no file, no near-miss record. Every launcher's `[STATUS]` carries those
   counts per run length (`census 7:280 8:71 9:28 10:8`, from
   `huntlib.hlog.census_str`). **`[STATUS]` is logged every 30 seconds of
   wall clock, from `huntlib.hlog.Heartbeat` on its own thread — never
   from inside the segment loop**, which goes silent for as long as a
   segment, a classification or a verification takes; when nothing has
   moved the line says what the launcher is doing and for how long, and
   no verification step may run unbounded (bounded rho then ECM for the
   factor witness; `[NEAR]` values skip witness and certificates). Notable
   events (decade and model-odds crossings, one-short values, new bests,
   first-of-a-length) each get a log line in the CONVENTIONS taxonomy so a
   human can follow the hunt from the log alone. See CONVENTIONS.md "The
   discovery protocol".
5b. **Campaigns run indefinitely by default.** No default depth cap; a
   launcher stops on its own only at the end of the last rung (the
   engine's enforced ceiling). Progress is read off rungs — named depths
   from the odds model's predictions, logged `[RUNG]` as passed and shown
   with an ETA in `[STATUS]`. `--to` and `--stop-on-discovery` are the
   only stops and both are opt-in. If a find changes what should be
   sieved for, the launcher moves itself (and logs it) rather than
   crawling at a stale setting. A rung retires with its term: the moment
   a term is found, its unreached quartiles leave the ladder and the
   `[STATUS]` line aims at the next OPEN term -- both the rung and the
   live odds. dickson-ladders found a(12) and then advertised
   `next a(12) P90` for hours while it hunted a(13); derive the ladder
   from the live frontier on every use so the retirement cannot be
   forgotten. See CONVENTIONS.md.
5c. **Optimize the campaign, not just the engine.** A hunt's rate is
   `max(device, host/workers)` over the k-line it covers, and the biggest
   lever in this repo has never once been the kernel: it was which filter
   the sieve asks for (which sets the wheel, and cost 13x), how deep it
   sieves (which decides *which side binds*, and therefore how many host
   processes the hunt demands), and how much of each survivor's
   classification is actually needed. Before touching a kernel, measure
   **device seconds and host core-seconds per unit of the thing the hunt
   is paid in**, for the configuration the campaign is actually running.
   A 913x engine sitting in a configuration 25x off its own optimum is
   the failure mode this rule exists to prevent.

5d. **A crash must cost one segment, not the campaign.** Checkpoints are
   `fsync`ed before the atomic replace and keep a `.bak` (a rename is
   atomic for the directory entry, not for the data -- a process or
   machine that stops in that window leaves a right-sized file of NUL,
   and once did); a present-but-unreadable checkpoint raises rather than
   reading as absent. See CONVENTIONS.md.

5e. **Ctrl+C is a normal exit, not a crash.** Every program in this repo
   -- launchers, `score.py`, gate scripts, the oracle -- ends on an
   interrupt with a checkpoint at the LAST SEGMENT BOUNDARY (never the
   live cursor: counters are per candidate, so a mid-segment save
   double-counts the census when the segment is redone), one `[STAGE]`
   line, exit code 130, and **no traceback -- ever**. `huntlib.shutdown`
   is the only place a `KeyboardInterrupt` is caught: `graceful(main)`
   wraps the entry point, `on_interrupt(cb)` registers what to save, pool
   initializers call `ignore_in_worker()`. The shutdown goes deaf
   (`SIGINT`/`SIGBREAK` to `SIG_IGN`) BEFORE it writes anything, because
   the second Ctrl+C -- pressed when the first appears to do nothing -- is
   the one that prints the chained traceback and can land inside the
   checkpoint write. Drilled in every selftest. See CONVENTIONS.md
   "Stopping a run".

5f. **A hunt is designed not to destabilize the machine it runs on.**
   The load a campaign places is a DESIGN INPUT, budgeted like any other
   requirement -- not a number that falls out of tuning. Measure device
   seconds and host core-seconds per unit of the thing the hunt is paid
   in; size the pool from that requirement with margin, never from
   `cpu_count`; when two settings tie on throughput take the one that
   asks for less machine; ramp the pool instead of stamping it; balance
   the two sides so the pipeline does not square-wave; ship priced
   throttles (`--workers`, `--gpu-yield-ms`, `--gentle`); never change a
   machine setting on the owner's behalf; and assume the process can stop
   at any instant. The full procedure, in order, is CONVENTIONS.md
   "Sizing a hunt so it leaves the machine usable" -- read it before
   choosing any default that scales with the host. The two failure modes
   it exists to prevent are a default sized to the machine rather than to
   the work, and a tuning pass that raises the load while optimizing the
   rate.

6. **New projects** copy the skeleton, import huntlib for
   infrastructure, keep all mathematics in-project, and add a row to the
   top-level README's project table. Only projects with verified
   results get published here.

   Checklist when adding a project (all binding):
   - [ ] five-file skeleton per CONVENTIONS.md; huntlib for
         infrastructure only; oracle stays sympy-pure
   - [ ] README/RESULTS/BENCHMARKS/OPTIMIZATION_LOG following the
         Documentation template section of CONVENTIONS.md EXACTLY
         (disclaimer first, then headline, status, problem, engine,
         model, usage, trust)
   - [ ] status word (ACTIVE / COMPLETE / PAUSED — open to others)
         identical in the project README and the top-level table row
   - [ ] evidence/ directory with verifiable JSONs (exact integers +
         factor witnesses) for FIRST OCCURRENCES ONLY -- census is counts
         in the checkpoint and the log, never files; runtime checkpoints
         gitignored
   - [ ] campaign configuration priced the way 5c says (device s and
         host core-s per unit k-line, per candidate setting), not just a
         fast kernel
   - [ ] checkpoints fsynced + `.bak` rotated, corrupt-file path drilled
   - [ ] every entry point wrapped in `huntlib.shutdown.graceful`, the
         boundary save registered with `on_interrupt`, pool initializers
         calling `ignore_in_worker`, and the graceful-shutdown drill in
         the selftest (Ctrl+C: boundary checkpoint, one line, exit 130,
         no traceback even on a second Ctrl+C)
   - [ ] host pool sized from the measurement, RAMPED not stamped, and
         the drill proves the workers come up one at a time; the load
         budget followed end to end (CONVENTIONS.md "Sizing a hunt so it
         leaves the machine usable"), with priced throttles and no
         machine setting changed on the owner's behalf
   - [ ] a 30-second WALL-CLOCK `[STATUS]` heartbeat on its own thread
         (huntlib.hlog.Heartbeat: mark() at segment boundaries, doing()
         around long steps, checkpoint saves from the main loop only)
         carrying the census counts per run length
         (huntlib.hlog.census_str), and `event_kind` drilled in the
         selftest (DISCOVERY / NEAR one-short / CENSUS counted)
   - [ ] self-contained: no references to unpublished work, no personal
         or machine-specific information (scan before committing:
         usernames, local paths, emails, OS details)
   - [ ] full gate battery green and benchmark fingerprint reproduced
         in the published copy before the first push
7. ASCII-only log output (legacy console code pages exist); LF line
   endings in the repo; no references to unpublished work and no
   personal or machine-specific information anywhere in the repo.

## Quick commands (run them in the ACTIVE project only -- Rule 2)

```
python launch.py --selftest   # full gate battery -- must end ALL GREEN
python launch.py              # the hunt (resumable; owner-started, days)
python score.py               # gates x fingerprinted benchmarks
```

Wall-clock, so Rule 0 can be planned against: `score.py` ~2.5 min,
`launch.py --selftest` ~3 min. Both are per project, and both are minutes
of the owner's GPU: run them where the work is, not everywhere. Anything you write yourself gets budgeted
the same way — measure one short run first, then size the sweep to fit
under 5 minutes.
