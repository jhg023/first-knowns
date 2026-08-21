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
| [euler-prime-runs](euler-prime-runs/) | [A164926](https://oeis.org/A164926): the least prime p whose Euler-form polynomial x²+x+p is prime for exactly n consecutive x — extending the direct lineage of Euler's famous x²+x+41 | **PAUSED — open to others** — a(17) = 348,284,517,256,411,907, a(18) = 8,461,068,614,861,832,371 and a(19) = 3,744,101,869,688,673,856,367 found & verified (the first new terms since 2009); a(21) = 234,505,015,943,235,329,417 settled by exhaustive sweep past the known bound. The sweep is contiguous to 3.744×10²¹, so the one term of this stretch still open — a(20) — exceeds that, and exceeds a(19) and a(21) with it. The hunt halted on the a(19) find 2026-08-18 and is left resumable: conditional a(20) median 1.75×10²², ~9 days on one 4090 |
| [dickson-ladders](dickson-ladders/) | [A247965](https://oeis.org/A247965): the least k such that m·k²+1 is prime for every m = 1..n — a Dickson ladder whose n = 1 case is Landau's k²+1 problem | **PAUSED — open to others** — a(10) = 9,328,409,578,841,430, a(11) = 433,871,469,806,557,860, a(12) = 55,119,263,286,518,170,740 (all 2026-08-18) and **a(13) = 12,094,123,415,384,869,458,600** (2026-08-19) found & verified — the first advance since 2014 — each with a primality certificate for all of its values and re-verified from its evidence before publication. Prior frontier: Hiroaki Yamanouchi's a(9) = 3,332,396,388,090, Oct 2014. a(13) landed 58 min after the v4 fold went in (a paired 2.39× on top of the 2026-08-18 27.9× re-configuration — **2.3×10¹⁷ k/s**, reach extended 17× to k = 2.04×10²⁴). All four finds landed late — model quantiles 0.915, 0.923, 0.787 and 0.916; the pooled optimism factor is 2.26× and its 95% interval [1.03, 8.31] excludes 1 for the first time, so the model now reads ~2× optimistic about depth. The campaign paused 2026-08-20 at k = 1.57×10²² and is left resumable: **a(14)** sits inside the remaining sweep at 98.6% model odds (≈85% adjusted), ~8.5 days to its median on one 4090 |
| [primorial-ap](primorial-ap/) | [A053647](https://oeis.org/A053647): the first term of the first arithmetic progression of n primes whose common difference is the n-th primorial — the smallest difference such a progression can have | **PAUSED — open to others** — a(16) = 116,781,362,669,989, a(17) = 2,097,209,048,106,247 and **a(18) = 14,042,451,608,819,603** found & verified 2026-08-20/21 in a single 23-hour campaign — the first advance since Oct 2009, and the first value of any kind ever put on an open term of this sequence, which had no published bounds at all. All 51 values are **proved** prime, sitting below the deterministic Miller-Rabin bound; each term was re-verified from its evidence file before publication and is re-checked by a gate on every run. a(17) is a bonus: its chain runs **19** deep, so it is also a 19-term AP. Prior frontier: Donovan Johnson's a(15) = 158,317,270,283, Oct 2009. The engine is a gated **v2** — pattern tables + shared-memory sub-segments, SCORE 5,163 → 44,533 with the stream pinned bit-for-bit — and the campaign came in at **1.93×10¹¹ p/s end-to-end, 93% of a rate measured on a run 2,500× shorter**. Model quantiles 0.87, 0.82, 0.43; pooled over all twelve scored terms the factor is 0.83, 95% interval [0.51, 1.60], so this model is **not** distinguishable from honest — the opposite of its sibling above. Paused at the floor of the **a(19)** sweep: median 4.12×10¹⁷, ~23 days on one 4090, and the first term whose values need BLS75 certificates |

Project documentation follows a fixed template (see
[CONVENTIONS.md](CONVENTIONS.md) § Documentation template): every
project README opens with the authorship disclaimer, then headline,
status (`ACTIVE` / `COMPLETE` / `PAUSED — open to others`), problem,
engine mathematics, odds model, usage, and trust; verified finds live
in each project's RESULTS.md with evidence files alongside.

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
