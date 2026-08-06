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
4. **Oracles stay slow and boring.** sympy only. No optimization, ever.
5. **Discoveries are records, not announcements.** The pipeline writes
   evidence JSONs; humans decide what happens next. Never auto-submit
   to OEIS or anywhere else.
6. **New projects** copy the skeleton, import huntlib for
   infrastructure, keep all mathematics in-project, and add a row to the
   top-level README's project table. Only projects with verified
   results get published here.
7. ASCII-only log output (Windows consoles); LF line endings in the
   repo; no references to unpublished work.

## Quick commands (any project directory)

```
python launch.py --selftest   # full gate battery -- must end ALL GREEN
python launch.py              # the hunt (resumable)
python score.py               # gates x fingerprinted benchmark
```
