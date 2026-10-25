# first-knowns

> **Authorship and roles:** This project is developed with **Claude
> (Anthropic)** and **ChatGPT (OpenAI), through Codex**, working at my
> direction. None of the code was written by me. I set the goals, provide
> the hardware, and decide which campaigns to run.
>
> - **Claude designs and implements the hunts:** algorithms, Python
>   engines, CUDA kernels, verification machinery, and project
>   documentation. Claude optimizes the code and performs authorized
>   correctness checks and benchmarks. The existing hunt implementations
>   and original documentation were authored by Claude.
> - **ChatGPT, through Codex, independently reviews the mathematics:**
>   missed search-space reductions, equivalent formulations, stronger
>   bounds, and algorithmic ways to avoid repeated work. These reviews
>   are always static: no GPU use or execution of project code. Codex
>   writes the analysis reports and review-workflow documentation;
>   Claude implements and validates selected proposals.

Computational mathematics hunts and exact computations, accelerated by
CPUs, GPUs or both — new terms of long-stale OEIS sequences, first-known
objects, exact counts of combinatorial families, and the paranoid
verification machinery that makes the results trustworthy.

Everything here runs on one desktop — a consumer GPU (an RTX 4090) for
the prime hunts, its CPU cores for the exact counts — and one principle:
**an engine is only as good as the independent checks that police it.**
Every project in this repo ships with a slow trustworthy oracle that
implements the original definition, an independent fast implementation
pinned against it (a CPU and a GPU engine bit-for-bit on populated windows
for the prime hunts; the literal oracle and the optimized counter, family
by family and category by category, for an exact count), canaries —
known values a production stream must rediscover, or specified nodes a
counting campaign must reach and close with the expected count — that
must fire before production is trusted, and a verification protocol that
every result must survive before it is recorded.

## Independent mathematical reviews

[**CODEX_REVIEWS.md**](CODEX_REVIEWS.md) is the entry point for the
ChatGPT/Codex-to-Claude review workflow, including the report index and a reusable
request for reviewing a newly added project. **Codex reviews are always
static and never use the GPU.** They identify missed mathematical and
algorithmic optimizations; Claude implements and validates selected
proposals in a later task.

Reports and finding dispositions live in each reviewed project's
`codex-reviews/` directory. Use the
[central review index](CODEX_REVIEWS.md#review-index) to find a project's
report and implementation status. Reviews of multiple projects proceed
one project at a time, with all reviewers focused on that project before
moving to the next.

The initial review inventory was completed on **2026-10-20** for all
**17 populated hunt projects**. Each report records its source snapshot,
proofs, limitations, and implementation proposals; the local finding
ledger distinguishes proposals from later implemented and validated work.

## Projects

| project | problem | status |
|---------|---------|--------|
| [clique-ladders](clique-ladders/) | [A093483](https://oeis.org/A093483) and five siblings ([A103828](https://oeis.org/A103828), [A037100](https://oeis.org/A037100), [A119752](https://oeis.org/A119752), [A119751](https://oeis.org/A119751), [A133761](https://oeis.org/A133761)), with five derived entries riding on them: the greedy set in which every pair sums to a prime less one — a(n) is the least integer > a(n−1) such that a(n) + a(i) + 1 is prime for every 1 ≤ i ≤ n − 1, so the conditions for the next term do not exist until this one does | **PAUSED — open to others** — twenty-six terms found & verified 2026-09-19/20 across all six families, the first advance on A093483 since 2012 and on A119751 and A119752 since 2008, with twenty-two terms of the five derived entries settled alongside. Paused just above each last find, with a(22) of A093483, A103828 and A037100 and a(21) of A119752, A119751 and A133761 open. |
| [cyclotomic-ladders](cyclotomic-ladders/) | [A070737](https://oeis.org/A070737), [A072942](https://oeis.org/A072942) and [A233512](https://oeis.org/A233512): the smallest number x such that the first n cyclotomic polynomials evaluated at x are primes (A070737), the least x such that the cyclotomic polynomial values Phi(d,x) are prime for all d dividing n (A072942), and A070737 restated with the arguments strictly increasing (A233512, which coincides with it from n = 5) — cyclotomic ladders, whose kill sets are the residues of each multiplicative order the forms ask for, so a prime is forced exactly when every order dividing it less one is asked for | **PAUSED — open to others** — a(11) and a(12) of A070737 (and so of A233512) and a(48), a(60), a(66), a(78), a(80) and a(88) of A072942 found & verified 2026-10-23 to 10-25, the first advance on A070737 since 2002 and on A072942 since 2014, with nine values at a(66), a(78) and a(88) proved prime by APR-CL rather than by a certificate. Paused at x = 1.86×10²² on A070737 with a(13) open, and at x = 3 on A072942's a(72), with a(84), a(90) and a(96) unstarted. |
| [decimal-ladders](decimal-ladders/) | [A305740](https://oeis.org/A305740) and [A153431](https://oeis.org/A153431): the least k such that 10^m·k + 1 is prime for every m = 1..n (A305740), and the least m such that m·10^k + 1 is prime for every k = 0..n (A153431) — decimal ladders, whose kill sets are the orbits of 10 modulo each prime, so a prime is forced exactly when 10 is a primitive root of it | **PAUSED — open to others** — a(13) through a(18) of A305740 and a(14) through a(16) of A153431 found & verified 2026-09-24/29, the first advance on either since 2018 and 2022. Paused at k = 1.76×10²⁴ on A305740 with a(19) open, and at m = 7.80×10²² on A153431 with a(17) open. |
| [dickson-ladders](dickson-ladders/) | [A247965](https://oeis.org/A247965): the least k such that m·k²+1 is prime for every m = 1..n — a Dickson ladder whose n = 1 case is Landau's k²+1 problem | **PAUSED — open to others** — a(10) through a(13) found & verified 2026-08-18/19, the first advance since 2014, each with a primality certificate for every one of its values. Paused at k = 1.57×10²², with a(14) open. |
| [euler-prime-runs](euler-prime-runs/) | [A164926](https://oeis.org/A164926): the least prime p whose Euler-form polynomial x²+x+p is prime for exactly n consecutive x — extending the direct lineage of Euler's famous x²+x+41 | **PAUSED — open to others** — a(17), a(18) and a(19) found & verified 2026-08-05/18, the first new terms since 2009, and a(21) settled by exhaustive sweep. Paused at p = 3.744×10²¹, with a(20) open. |
| [factorial-ladders](factorial-ladders/) | [A177013](https://oeis.org/A177013) and [A177014](https://oeis.org/A177014) (with [A226935](https://oeis.org/A226935) riding on the second): the least m such that all of 1!·m ∓ 1, 2!·m ∓ 1, …, n!·m ∓ 1 are prime — factorial ladders, whose multipliers vanish modulo every prime they pass, so the wheel grows with n and only 2 and 3 are ever forced | **PAUSED — open to others** — a(11) through a(18) of both A177013 and A177014 found & verified 2026-09-16/18, the first advance on either since 2010, with a(11) through a(18) of A226935 settled alongside. Paused at m = 5.41×10²¹ on A177013 and m = 3.15×10²² on A177014, with a(19) open on each. |
| [lcm-ladders](lcm-ladders/) | [A078502](https://oeis.org/A078502) and [A074200](https://oeis.org/A074200) (with [A093554](https://oeis.org/A093554) and [A093553](https://oeis.org/A093553) riding on them): the least N such that (N − k)/k is prime for every k = 1..n (A078502), and the least m such that (m + k)/k is prime for every k = 1..n (A074200) — lcm ladders, whose multipliers are lcm(1..n)/k, so the small primes are nearly blind where every other ladder here has them maximal | **PAUSED — open to others** — a(15) through a(19) of A078502 and a(15) through a(18) of A074200 found & verified 2026-09-06/19, the first advance on either since 2003 and 2004, with A093554 and A093553 settled alongside. Paused at a(19) on A078502 with a(20) open, and at m = 5.11×10²⁹ on A074200 with a(19) open. |
| [linear-ladders](linear-ladders/) | [A088250](https://oeis.org/A088250) and six siblings ([A173750](https://oeis.org/A173750), [A125838](https://oeis.org/A125838), [A125839](https://oeis.org/A125839), [A164325](https://oeis.org/A164325), [A164326](https://oeis.org/A164326), [A088651](https://oeis.org/A088651)): the least k such that r·k ± 1 is prime for every r = 1..n (A088250, A088651), and the least m such that k·m ± 1 is prime for every k = 2..n (A173750, A125838) or k = 3..n (A125839), or (2k − 1)·m ± 1 for every k = 1..n (A164325, A164326) — linear ladders, whose consecutive multipliers force divisibility by every prime up to n + 1 | **PAUSED — open to others** — twenty-eight terms found & verified 2026-09-03/05 across all seven families, the first advance on any since 2017 and the first bounds of any kind at an open index, with A202778, A071576 and A202779 settled alongside. Paused with each family's term swept to between 4.3×10²⁴ and 2.1×10²⁶ and its next term open above that bound, about 10% likely under a night's sweep. |
| [plus-two-cliques](plus-two-cliques/) | [A083518](https://oeis.org/A083518) and [A083519](https://oeis.org/A083519): beginning with 3 (A083518) or with 1 (A083519), a(i)·a(j) + 2 is prime for all i ≠ j, each term the least integer above the one before — the product cliques with the constant two, so the conditions for the next term do not exist until this one does, and every term from the fourth is 3 (mod 6) | **PAUSED — open to others** — a(14) through a(19) of A083518 and a(11) through a(18) of A083519 found & verified 2026-10-02, the first advance on either since 2004 and 2008. Paused just above each last find, with a(20) of A083518 and a(19) of A083519 open. |
| [polynomial-runs](polynomial-runs/) | [A165234](https://oeis.org/A165234), [A230663](https://oeis.org/A230663), [A092120](https://oeis.org/A092120) and [A347537](https://oeis.org/A347537): the least prime p such that 2x² + p is prime for x = 0..n−1 and composite for x = n (A165234), and the same with x² + 3x + p (A230663), with p + 4m² for m = 0..n and composite at m = n+1 (A092120), and with k⁴ + k³ + k² + k + p (A347537) — exact-run polynomial ladders, the siblings of euler-prime-runs' A164926, whose strong wheel makes the hunt pay for line rather than candidates | **PAUSED — open to others** — a(16) through a(21) of A165234, a(16) through a(20) of A230663, a(16) through a(18) of A092120 and a(17) through a(21) of A347537 found & verified 2026-10-08 to 10-15, the first advance on A092120 since 2008, on A165234 and A230663 since 2024 and on A347537 since May 2026. Paused at p = 4.22×10²² on A165234 with a(22) open, p = 1.59×10²¹ on A230663 with a(21) open, p = 2.66×10²⁰ on A092120 with a(20) open, and p = 5.51×10²³ on A347537 with a(22) open. |
| [power-ladders](power-ladders/) | [A229626](https://oeis.org/A229626), [A229627](https://oeis.org/A229627), [A229630](https://oeis.org/A229630) and [A229902](https://oeis.org/A229902): the smallest m such that 2·m^k − 1 is prime for k = 1..n (A229626), the smallest prime q such that 2·q^k − 1 is prime for k = 1..n (A229627), the smallest semiprime m such that 2·m^k − 1 is prime for k = 1..n (A229630), and the smallest m such that 19·m^k + 1 is prime for k = 1..n (A229902) — power ladders, whose survivors are Fermat-tested on the device | **PAUSED — open to others** — a(10) and a(11) of A229626, and a(9) through a(11) of A229627, A229630 and A229902 found & verified 2026-10-15 to 10-23, the first advance on A229630 since 2013 and on the other three since January 2023, with A229902's a(9) its listed a(8) repeated. Paused at m = 2.70×10¹⁹ on A229626, q = 2.86×10²¹ on A229627, m = 7.32×10²⁰ on A229630 and m = 2.43×10²⁰ on A229902, each with a(12) open. |
| [prime-ladders](prime-ladders/) | [A084700](https://oeis.org/A084700) and [A084701](https://oeis.org/A084701): the least k such that k·prime(i) ± 1 is prime for every i = 1..n — prime ladders, whose rungs are the primes themselves and whose small-prime wheel collapses to forced divisibility | **PAUSED — open to others** — a(14) through a(18) of A084700 and a(12) through a(18) of A084701 found & verified 2026-09-02/03, the first advance on either since 2004 and 2003. Paused at k = 4.16×10²³ on A084700 with a(19) open, 22% likely under the engine's proof ceiling, and at A084701's own ceiling, k = 4.95×10²², with its a(19) open above it. |
| [primorial-ap](primorial-ap/) | [A053647](https://oeis.org/A053647): the first term of the first arithmetic progression of n primes whose common difference is the n-th primorial — the smallest difference such a progression can have | **PAUSED — open to others** — a(16), a(17) and a(18) found & verified 2026-08-20/21, the first advance since 2009 and the first values of any kind on an open term of this sequence. Paused at the floor of the a(19) sweep. |
| [primorial-ladders](primorial-ladders/) | [A115785](https://oeis.org/A115785) and [A115786](https://oeis.org/A115786) (with [A145743](https://oeis.org/A145743) riding the engine): the smallest prime p such that p − prime(k)# is prime for every k = 1..n (A115785), the smallest prime p such that p + prime(k)# is prime for every k = 1..n (A115786), and the smallest composite number m such that m + 4·k² is prime for every k = 1..n (A145743) — shift ladders whose constants are the primorials, so the small primes are nearly blind and each index of A115785 is its own short line from prime(n)# | **PAUSED — open to others** — a(16) through a(19) of A115785, a(17) through a(20) of A115786 and a(14) through a(20) of A145743 found & verified 2026-10-02/05, the first advance on the first two since 2006 and on the third since 2008. Paused at the floor of the a(20) sweep on A115785, at p = 3.74×10²⁰ on A115786 with a(21) open, and at m = 8.90×10²² on A145743 with a(21) open. |
| [primorial-runs](primorial-runs/) | [A257466](https://oeis.org/A257466), [A257467](https://oeis.org/A257467) and [A258035](https://oeis.org/A258035): the smallest prime p such that p + pps(1), …, p + pps(n) are all prime but p + pps(n+1) is not, pps(n) the partial primorial sum (A257466), and the same with psq(n), the square of the primorial (A257467), and with pssq(n), the partial sums of those squares (A258035) — exact-run shift ladders, which are not monotone, so one sweep from the bottom of the line settles the first prime of every run length at once | **PAUSED — open to others** — a(16) through a(20) of A257466, a(15) through a(19) of A257467 and a(11) through a(18) of A258035 found & verified 2026-10-05 to 10-08, the first advance on any of the three since 2015, with A258035's listed a(11) and a(12) corrected to its a(12) and a(13). Paused at p = 1.04×10²⁰ on A257466 with a(21) open, p = 4.61×10²⁰ on A257467 with a(20) open, and p = 4.41×10²⁰ on A258035 with a(19) open. |
| [product-cliques](product-cliques/) | [A034881](https://oeis.org/A034881) and [A219761](https://oeis.org/A219761): a(1) = 1, and a(n) is the smallest integer > a(n−1) such that a(n)·a(i) + 1 is prime for all 1 ≤ i ≤ n − 1 (A034881), or such that a(n)·a(n−i) + 1 is prime for all 0 ≤ i ≤ n − 1 (A219761, so a(n)² + 1 as well) — the multiplicative twin of the clique ladders, so the conditions for the next term do not exist until this one does | **PAUSED — open to others** — a(16) through a(19) of A034881 and a(12) through a(18) of A219761 found & verified 2026-09-29 to 2026-10-01, the first advance on either since 2012. Paused just above each last find, with a(20) of A034881 and a(19) of A219761 open. |
| [shift-ladders](shift-ladders/) | [A130003](https://oeis.org/A130003) and [A110096](https://oeis.org/A110096): the least m such that 4^k + m is prime for every k = 1..n (A130003), and the least positive integer that, added to each of 2^1, …, 2^n, yields all primes (A110096) — shift ladders, whose killed set is a geometric orbit rather than a quadratic one | **PAUSED — open to others** — six terms found & verified 2026-08-23/09-01: a(19), a(20) and a(21) of A130003, the first advance there since 2007, and a(17), a(18), a(19) of A110096. Paused at m = 2.86×10²⁰ on A130003 with a(22) open, and at 5.64×10²³ on A110096, where a(20) is only 13% likely to sit under the engine's proof ceiling. |
| [square-ladders](square-ladders/) | [A089761](https://oeis.org/A089761): the least k such that k·i²+1 is prime for every i = 1..n — a Dickson ladder whose rungs are the squares | **PAUSED — open to others** — a(16), a(17) and a(18) found & verified 2026-08-21/23, the first terms anyone has found since 2008 and the first break in a five-term plateau. Paused at k = 1.10×10²⁰, with a(19) open. |

Project documentation follows a fixed template (see
[CONVENTIONS.md](CONVENTIONS.md) § Documentation template): every
project README opens with the authorship disclaimer, then headline,
status (`ACTIVE` / `COMPLETE` / `PAUSED — open to others`), problem,
engine mathematics, the model (an odds model for a search, a deterministic
workload model for an exact count), usage, and trust; verified finds live
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

- [`CONVENTIONS.md`](CONVENTIONS.md) — the project template every
  project follows: oracle / CPU engine / GPU engine (an explicitly
  unsupported stub in a CPU-only project) / checkpointed launcher /
  fingerprinted benchmark, the gate discipline, the discovery protocol
  of a search and the exact-count protocol of a counting project, how a
  run stops, and how a campaign is sized so that a machine running one
  for days stays usable for everything else.
- [`OPTIMIZATION.md`](OPTIMIZATION.md) — how to make a hunt fast without
  making it wrong: the measurement process (measure the phase split
  first, interleave every A/B, separate engine changes from
  benchmark-shape changes, price what you decline) and the catalogue of
  optimizations that have paid, with numbers — plus the ones that
  didn't. A hunt's frontier is set by throughput, so this is not
  optional polish; two of its rules are design decisions best made
  before the first engine is written.
- [`INNOVATION.md`](INNOVATION.md) — finding the optimizations the checklist
  cannot: the representation hunt and the instruction-level pass every inner
  loop gets before its verdict is written; the experiment ladder; the rule
  that the default command is the fastest engine
- [`CODEX_REVIEWS.md`](CODEX_REVIEWS.md) — the independent, always-static
  mathematical review process: project reports in `codex-reviews/`,
  explicit proofs and assumptions, and implementation handoffs to Claude.
- [`huntlib/`](huntlib/) — the shared code: deterministic Miller-Rabin and
  BLS75 primality certificates (the N−1 routes and the N+1 Lucas route,
  with subproofs for factors past the deterministic bound), **the
  measured ceiling every new hunt starts from** (`huntlib.ceiling`:
  10⁴⁰ on both signs, because a discovery is proved by certificate on its
  own structure and the only thing a height costs is one factorization of
  k per find — CLAUDE.md rule 5h), Barrett reciprocal helpers for CUDA
  kernels, crash-durable checkpoints, tagged logging and the wall-clock
  heartbeat, the ramped classification pool, frontier and census
  bookkeeping, the progress ladder, first-occurrence evidence files,
  graceful shutdown, the un-gameable SCORE runner — and the repo-wide
  selftest drills every project owes. A project directory holds the hunt
  and its specified documentation, including `codex-reviews/` (CLAUDE.md
  rule 9): harnesses stay in the scratchpad and their measurements go in
  the log.

## Reproducing results

Each project's README has exact commands. The pattern is always:

```
python launch.py --selftest    # full gate battery -- must print ALL GREEN
python launch.py               # the hunt (checkpointed, resumable)
python score.py                # correctness gates x benchmark
```

Requirements are per backend, stated in each project's README: the prime
hunts need Python 3.12+, numpy, sympy, and CuPy with a CUDA GPU (every
GPU engine also has a slower CPU fallback: `--engine cpu`). Nothing is a
universal requirement.

**Every program here stops cleanly on Ctrl+C.** These campaigns run for
days and a human decides when they end, so the interrupt is a supported
exit: the launcher checkpoints **at its last committed work unit** — the
last fully classified segment of a sieve (never mid-segment: the counters
are per candidate and would double-count on resume), the last durable
commit of a counting campaign (staged quanta that have not reached disk
are discarded and redone) — logs one `[STAGE]` line saying where it
stopped, and exits `130`. No program in this repository prints a stack
trace on Ctrl+C, including when a second Ctrl+C arrives while the
checkpoint is being written — the shutdown goes deaf until the file is on
disk. Resuming redoes at most the unit that was in flight. See
[CONVENTIONS.md](CONVENTIONS.md) § Stopping a run.

## Verification philosophy

A result you cannot re-verify is not a result. Every discovery file of a
prime hunt in this repo (`*/evidence/`) contains the exact integers plus
a factor witness for the claim-breaking composite, so anyone can confirm
the find with a few lines of any bignum system — no trust in this codebase
required. An exact count has no witness of that kind: its record carries
the exact integer, the manifest digest of the partition, the receipt-chain
head, the per-task vector digest and the canary results, and states which
of the three obligations — algorithm correctness, partition coverage,
exact aggregation — support it and by what evidence; a count is labelled
"independently reproduced" only when a genuinely separate full
computation has been recorded. A checksum, or the same program run in a
different worker order, is neither.

**Evidence is for first occurrences only.** A hunt meets many values
that are *not* new terms — run-7s and run-8s in a hunt for a(11), run-17s
in a hunt for a(20). Those are the campaign's **census**, and the census
is counted, not narrated: the launcher keeps a count per run length in
its checkpoint and prints it in every 30-second `[STATUS]` line
(`census 7:280 8:71 9:28 10:8`); a value one short of an open term gets a
single `[NEAR]` line; anything shorter gets no line and no file. What you
will find in `evidence/` is one JSON per verified discovery and the
ledger — plus, where an OEIS editor has asked for one, the entry's b-file
built from those JSONs (`lcm-ladders/evidence/b078502.txt`). A counting
project additionally keeps its known-term reproduction records under
`evidence/validation/`: a published term recomputed end to end by the
production machinery is a validation record, never a discovery, and a
new-term campaign may not start without them. The full rules are in
[CONVENTIONS.md](CONVENTIONS.md) § The discovery protocol and § The
exact-count protocol.
