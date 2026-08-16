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
| [euler-prime-runs](euler-prime-runs/) | [A164926](https://oeis.org/A164926): the least prime p whose Euler-form polynomial x²+x+p is prime for exactly n consecutive x — extending the direct lineage of Euler's famous x²+x+41 | **ACTIVE** — a(17) = 348,284,517,256,411,907 and a(18) = 8,461,068,614,861,832,371 found & verified (first new terms since 2009); a(21) = 234,505,015,943,235,329,417 settled by exhaustive sweep past the known bound; phase 2 hunting a(19), contiguous to 1.06×10²¹ with no run ≥ 19 (leg 2 running to 5×10²¹, ~94% of the conditional a(19) distribution; engine ~32x faster as of 2026-08-16) |

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
  fingerprinted benchmark, the gate discipline, and the discovery
  protocol.
- [`OPTIMIZATION.md`](OPTIMIZATION.md) — how to make a hunt fast without
  making it wrong: the measurement process (measure the phase split
  first, interleave every A/B, separate engine changes from
  benchmark-shape changes, price what you decline) and the catalogue of
  optimizations that have paid, with numbers — plus the ones that
  didn't. A hunt's frontier is set by throughput, so this is not
  optional polish; two of its rules are design decisions best made
  before the first engine is written.
- [`huntlib/`](huntlib/) — the shared code: deterministic Miller-Rabin,
  Barrett reciprocal helpers for CUDA kernels, atomic checkpoints,
  tagged logging, and the un-gameable SCORE runner.

## Reproducing results

Each project's README has exact commands. The pattern is always:

```
python launch.py --selftest    # full gate battery -- must print ALL GREEN
python launch.py               # the hunt (checkpointed, resumable)
python score.py                # correctness gates x benchmark
```

Requirements: Python 3.12+, numpy, sympy, and CuPy with a CUDA GPU
(every engine also has a slower CPU fallback: `--engine cpu`).

## Verification philosophy

A result you cannot re-verify is not a result. Every discovery file in
this repo (`*/evidence/`) contains the exact integers plus a factor
witness for the claim-breaking composite, so anyone can confirm the find
with a few lines of any bignum system — no trust in this codebase
required.
