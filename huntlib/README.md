# huntlib

> **Authorship disclaimer:** None of this code was written by me — it was
> entirely authored by **Claude (Anthropic's AI)** at my direction.

The shared library behind every hunt in this repository. Projects add
the repo root to `sys.path` and import:

```python
from huntlib.hlog import log, banner, census_str, Heartbeat
from huntlib import checkpoint
from huntlib.primes import (mr_is_prime, sprp_base2, factor_witness,
                            MR_VALID_BELOW)
from huntlib.certificate import prove, verify, factor_partial
from huntlib.gpu import barrett_magics, device_report
from huntlib.rungs import Ladder, eta_str
from huntlib import evidence, frontier, pool, scoring, shutdown, drills
```

| module | contents |
|--------|----------|
| `hlog` | timestamped tagged logging + the repo-wide tag taxonomy; `census_str` — the one format every `[STATUS]` line uses for the census counts per run length (`census 7:280 8:71 9:28 10:8`); `Heartbeat` — the wall-clock `[STATUS]` timer thread every launcher runs (mark positions at segment boundaries, `doing()` around long steps; it reports the end-to-end rate and, when nothing has moved, what the launcher is stuck on) |
| `checkpoint` | config-keyed JSON checkpoints that survive the MACHINE, not just the process: temp file, **`fsync`**, `os.replace`, and the previous file rotated to `.bak`. The fsync is not optional — a rename is atomic for the directory *entry* while the *data* may still be in the page cache, and an abrupt stop once left this repo a 785-byte checkpoint of pure NUL. `load` falls back to the `.bak` and otherwise raises `CheckpointCorrupt`, because "absent" and "corrupt" demand opposite responses from a live frontier |
| `primes` | deterministic 7-base Miller–Rabin (valid < 3.317×10²⁴, bound exported as a constant); `sprp_base2`, a single strong test to base 2 — worth having separately because its verdict is **asymmetric**: a failure is a *proof* of compositeness, so one modular exponentiation can rigorously bound a run length that seven would only pin down exactly; and factor witnesses (trial division, a bounded Brent rho, then sympy's ECM — never unbounded: a rho on a semiprime run breaker once stalled a live campaign for 105 s) |
| `certificate` | primality **proofs**, where a strong test is only evidence: BLS75 Theorem 1 (N−1 factored past √N) and Theorem 5 (past ∛N, with the `r² − 8s` side condition), a bounded partial factorization (trial division, bounded Brent rho, bounded ECM — then it gives up and *says so*), and bounded recursion for the large prime cofactor that is the usual reason F comes out too small. Every prime admitted into F is proved, so a certificate is a finite tree whose leaves are all deterministic Miller–Rabin. `verify` re-checks a proof from scratch and trusts nothing in it |
| `gpu` | Barrett magic-multiply reciprocals: the host-side helper and the canonical CUDA snippet that every kernel uses in place of hardware u64 division; `device_report`, the one line of machine state a days-long campaign owes its own log — **read-only**, it names levers and never pulls them |
| `pool` | the host classification pool, **ramped rather than stamped**: `ProcessPoolExecutor` spawns on submit only when no worker is idle, so a segment's worth of chunks starts every interpreter in the same instant — the largest and fastest load step a campaign makes, and one it has a whole segment of slack to avoid. `ramp` holds each worker busy while the next is asked for; `worker_init` goes deaf to Ctrl+C, drops its own priority and pays its imports inside the ramp |
| `frontier` | settledness bookkeeping over the literature table, earlier campaigns and the checkpoint's runtime table: `settled_at`, `next_open`, `top_settled`, the monotone and per-term settle policies, and the census counters. `event_kind` deliberately stays in each project — the rule is repo-wide, the mathematics is not |
| `rungs` | the progress ladder of an indefinite campaign. Nothing here stores a ladder: every method takes the LIVE frontier and derives the live rungs from it, so **a rung cannot fail to retire with its term** — the failure this module exists to make impossible, after a campaign spent hours advertising a depth belonging to a term it had already found |
| `evidence` | first-occurrence evidence files and their ledger, keyed by the value and upserted, so the segment redone after an interrupt rewrites its discovery instead of appending a second copy — and written through the same fsync-and-replace path as a checkpoint |
| `scoring` | the gates × fingerprinted-benchmark SCORE contract |
| `shutdown` | Ctrl+C as a **normal exit**: `graceful(main)` wraps every entry point and is the only place a `KeyboardInterrupt` is caught; `on_interrupt(cb)` registers what to save (LIFO, a returned string is logged as `[STAGE]`); `ignore_in_worker()` is the first line of every pool initializer, so workers stay quiet and the parent decides when the run ends. The shutdown sets `SIGINT`/`SIGBREAK` to `SIG_IGN` **before** any callback runs — the second Ctrl+C, pressed because the first appeared to do nothing, is the one that prints the chained traceback and can land inside the checkpoint write. `SIGTERM` routes into the same path. Exit code 130 |
| `drills` | the four repo-wide selftest drills every project owes (CONVENTIONS.md rule 6): the graceful shutdown, the 785-NUL checkpoint and its `.bak`, the pool ramp, and the evidence upsert — plus `event_kind_drill`, which makes a project exercise all four outcomes of the discovery-once taxonomy rather than only the happy one. `standard()` returns them all as `(ok, msg)` pairs. They mutate process state deliberately and put it back, so a selftest can run them mid-battery |

Design rule: huntlib holds only what is genuinely identical across
projects. Kernels, wheels, and problem mathematics stay in each project —
a reader auditing a hunt should find all of its *mathematics* in one
directory, and only *infrastructure* here.

Two deliberate exceptions to sharing. Each project's `*_reference.py`
oracle does **not** use huntlib's Miller–Rabin — oracles stick to sympy so
that the verification legs stay independent. And `event_kind`, the function
that turns a survivor into DISCOVERY / NEAR / CENSUS / nothing, stays in
each project even though the rule it implements is repo-wide: a monotone
ladder settles every shorter run at once, a per-length hunt settles exactly
one, and a hunt that re-sieves per term settles the term it is sieving for.
`huntlib.frontier` gives that function the facts it reasons from;
`huntlib.drills.event_kind_drill` makes each project prove it got them
right.
