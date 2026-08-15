# CLAUDE.md

Guidance for AI agents (and humans) working in this repository.

## What this repo is

Published, verified results from GPU hunts for open problems in
computational number theory, plus the machinery that produced them.
Every line of code here was authored by Claude at the repository owner's
direction; keep that audit trail honest — the disclaimer at the top of
each README stays.

## Rules

1. **Read `CONVENTIONS.md` before touching any project.** The five-file
   skeleton (oracle / CPU engine / GPU engine / launcher / score) and
   the gate discipline are binding.
2. **Gates green before and after every change.** Run the project's
   `python score.py`; commit only with the SCORE in the message. If a
   deliberate coverage change alters the benchmark fingerprint, update
   the fingerprint in the same commit and log it in the project's
   OPTIMIZATION_LOG.md.
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
         factor witnesses); runtime checkpoints gitignored
   - [ ] self-contained: no references to unpublished work, no personal
         or machine-specific information (scan before committing:
         usernames, local paths, emails, OS details)
   - [ ] full gate battery green and benchmark fingerprint reproduced
         in the published copy before the first push
7. ASCII-only log output (legacy console code pages exist); LF line
   endings in the repo; no references to unpublished work and no
   personal or machine-specific information anywhere in the repo.

## Quick commands (any project directory)

```
python launch.py --selftest   # full gate battery -- must end ALL GREEN
python launch.py              # the hunt (resumable)
python score.py               # gates x fingerprinted benchmark
```
