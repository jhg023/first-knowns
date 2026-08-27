# first-knowns

> **Authorship disclaimer:** None of the code in this repository was written
> by me. Every line of it — the engines, the CUDA kernels, the verification
> machinery, the documentation, including this README — was authored by
> **Claude (Anthropic's AI)**, working at my direction. My contributions are
> the goals, the hardware, and the decisions between runs.

GPU-accelerated hunts for open computational problems in number theory —
new terms of long-stale OEIS sequences, first-known objects, and the
paranoid verification machinery that makes the results trustworthy.

Everything here runs on one consumer GPU (an RTX 4090) and one principle:
**an engine is only as good as the independent checks that police it.**
Every hunt in this repo ships with a slow trustworthy oracle, two
independent engine implementations pinned bit-for-bit against each other,
canary rediscoveries of known values that must fire before production is
trusted, and a multi-way verification protocol that every discovery must
survive before it is recorded.

## Projects

| project | problem | status |
|---------|---------|--------|
| [euler-prime-runs](euler-prime-runs/) | [A164926](https://oeis.org/A164926): the least prime p whose Euler-form polynomial x²+x+p is prime for exactly n consecutive x — extending the direct lineage of Euler's famous x²+x+41 | **PAUSED — open to others** — a(17), a(18) and a(19) found & verified 2026-08-05/18, the first new terms since 2009, and a(21) settled by exhaustive sweep. Paused at p = 3.744×10²¹, with a(20) open. |
| [dickson-ladders](dickson-ladders/) | [A247965](https://oeis.org/A247965): the least k such that m·k²+1 is prime for every m = 1..n — a Dickson ladder whose n = 1 case is Landau's k²+1 problem | **PAUSED — open to others** — a(10) through a(13) found & verified 2026-08-18/19, the first advance since 2014, each with a primality certificate for every one of its values. Paused at k = 1.57×10²², with a(14) open. |
| [primorial-ap](primorial-ap/) | [A053647](https://oeis.org/A053647): the first term of the first arithmetic progression of n primes whose common difference is the n-th primorial — the smallest difference such a progression can have | **PAUSED — open to others** — a(16), a(17) and a(18) found & verified 2026-08-20/21, the first advance since 2009 and the first values of any kind on an open term of this sequence. Paused at the floor of the a(19) sweep. |
| [square-ladders](square-ladders/) | [A089761](https://oeis.org/A089761): the least k such that k·i²+1 is prime for every i = 1..n — a Dickson ladder whose rungs are the squares | **PAUSED — open to others** — a(16), a(17) and a(18) found & verified 2026-08-21/23, the first terms anyone has found since 2008 and the first break in a five-term plateau. Paused at k = 1.10×10²⁰, with a(19) open. |
| [shift-ladders](shift-ladders/) | [A130003](https://oeis.org/A130003) and [A110096](https://oeis.org/A110096): the least m such that m + b^k is prime for every k = 1..n, at b = 4 and b = 2 — shift ladders, whose killed set is a geometric orbit rather than a quadratic one | **PAUSED — open to others** — a(19) and a(20) of A130003 and a(17) and a(18) of A110096 found & verified 2026-08-23/24, the first advance on A130003 since 2007 and four terms for eighteen hours of one GPU. Paused at m = 8.95×10¹⁸ and m = 3.62×10²¹, with a(21) and a(19) open. |

Project documentation follows a fixed template (see
[CONVENTIONS.md](CONVENTIONS.md) § Documentation template): every
project README opens with the authorship disclaimer, then headline,
status (`ACTIVE` / `COMPLETE` / `PAUSED — open to others`), problem,
engine mathematics, odds model, usage, and trust; verified finds live
in each project's RESULTS.md with evidence files alongside. The status
column above is deliberately three things — the status word, what was
found and when, and where the cursor sits — because a table is read
across; the exact integers, the engines and their throughput, and how
each find scored against its model are in the project READMEs.

More hunts will land here as they conclude. The pipeline behind them
(problem selection, odds modeling, engine construction) produces
candidates continuously; only projects with verified results get
published.

## Shared machinery

The projects share a skeleton and a library:

- [`CONVENTIONS.md`](CONVENTIONS.md) — the project template every hunt
  follows: oracle / CPU engine / GPU engine / checkpointed launcher /
  fingerprinted benchmark, the gate discipline, the discovery protocol,
  how a run stops, and how a hunt is sized so that a machine running one
  for days stays usable for everything else.
- [`OPTIMIZATION.md`](OPTIMIZATION.md) — how to make a hunt fast without
  making it wrong: the measurement process (measure the phase split
  first, interleave every A/B, separate engine changes from
  benchmark-shape changes, price what you decline) and the catalogue of
  optimizations that have paid, with numbers — plus the ones that
  didn't. A hunt's frontier is set by throughput, so this is not
  optional polish; two of its rules are design decisions best made
  before the first engine is written.
- [`huntlib/`](huntlib/) — the shared code: deterministic Miller-Rabin and
  BLS75 primality certificates, Barrett reciprocal helpers for CUDA
  kernels, crash-durable checkpoints, tagged logging and the wall-clock
  heartbeat, the ramped classification pool, frontier and census
  bookkeeping, the progress ladder, first-occurrence evidence files,
  graceful shutdown, the un-gameable SCORE runner — and the repo-wide
  selftest drills every project owes.

## Reproducing results

Each project's README has exact commands. The pattern is always:

```
python launch.py --selftest    # full gate battery -- must print ALL GREEN
python launch.py               # the hunt (checkpointed, resumable)
python score.py                # correctness gates x benchmark
```

Requirements: Python 3.12+, numpy, sympy, and CuPy with a CUDA GPU
(every engine also has a slower CPU fallback: `--engine cpu`).

**Every program here stops cleanly on Ctrl+C.** These campaigns run for
days and a human decides when they end, so the interrupt is a supported
exit: the launcher checkpoints **at the last fully classified segment**
(never mid-segment — the counters are per candidate and would double-count
on resume), logs one `[STAGE]` line saying where it stopped, and exits
`130`. No program in this repository prints a stack trace on Ctrl+C,
including when a second Ctrl+C arrives while the checkpoint is being
written — the shutdown goes deaf until the file is on disk. Resuming
redoes at most the segment that was in flight. See
[CONVENTIONS.md](CONVENTIONS.md) § Stopping a run.

## Verification philosophy

A result you cannot re-verify is not a result. Every discovery file in
this repo (`*/evidence/`) contains the exact integers plus a factor
witness for the claim-breaking composite, so anyone can confirm the find
with a few lines of any bignum system — no trust in this codebase
required.

**Evidence is for first occurrences only.** A hunt meets many values
that are *not* new terms — run-7s and run-8s in a hunt for a(11), run-17s
in a hunt for a(20). Those are the campaign's **census**, and the census
is counted, not narrated: the launcher keeps a count per run length in
its checkpoint and prints it in every 30-second `[STATUS]` line
(`census 7:280 8:71 9:28 10:8`); a value one short of an open term gets a
single `[NEAR]` line; anything shorter gets no line and no file. What you
will find in `evidence/` is one JSON per verified discovery and the
ledger — nothing else. The full rule is in
[CONVENTIONS.md](CONVENTIONS.md) § The discovery protocol.
