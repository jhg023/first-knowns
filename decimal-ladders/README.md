# decimal-ladders — A305740, A153431

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of two OEIS sequences that ask one question
with the ladder shifted by a rung, in opposite letters: **A305740, the
smallest k such that 10^m·k + 1 is prime for all m in 1..n** (frontier
a(12) = 54,717,848,613,610, Giovanni Resta, June 2018), and **A153431, the
smallest m such that all n + 1 numbers m·10^k + 1, k = 0..n, are prime**
(frontier a(13) = 43,000,687,652,274,618, Don Reble, July 2022). Neither
had moved since. The engine is the repository's window sieve
(clique-ladders' kernel) with the form list swapped to powers of ten, taken
through a round of optimization here: the pattern windows read as
overlapping vector tuples, the per-block setup spread over every thread,
the sieve depth rebalanced, and the plan at every filter chosen by
measurement on exact candidate counts — and, mid-hunt, eight t-blocks per
block setup and five blocks per SM (OPTIMIZATION_LOG.md Measurements 16 and
17): **about 1.4× (A153431 n = 17) and 1.5× (A305740 n = 18) over the
inherited engine at the filters where the days are**. **The standing
result: a(13) through a(18) of A305740 and a(14) through a(16) of A153431,
found and verified 2026-09-24/29 — nine terms, every value of every run
proved prime by certificate** ([RESULTS.md](RESULTS.md)).

**Status: PAUSED — open to others** — A305740 stands at a(18) =
1,705,184,924,533,540,483,774,741 with no run of 19 below k = 1.7633e24;
A153431 at a(16) = 76,993,117,812,161,143,387,438 with no run of 17 below
m = 7.7996e22, and its a(17) bounded above by 10·A305740(18) =
1.7052e25. a(19) and a(17) are open; both campaigns resume from their
checkpoints with no flags.

## The problem

| entry | OEIS name (%N) | term | exponent | offset | frontier | last moved |
|---|---|---|---|---|---|---|
| [A305740](https://oeis.org/A305740) (`hard`) | a(n) is the smallest **k** such that 10^m*k + 1 is prime for all m in 1..n | **k** | m | 1 | a(12) = 54,717,848,613,610 | Jon E. Schoenfield 2018; a(12) by Giovanni Resta, Jun 2018 |
| [A153431](https://oeis.org/A153431) | a(n) is the smallest number **m** such that all n+1 numbers m*10^k+1 k=0,1,...,n are prime | **m** | k | 0 | a(13) = 43,000,687,652,274,618 | Farideh Firoozbakht 2009; a(11)–a(13) by Don Reble, Jul 2022 |

**Notation, and which number goes in the OEIS.** The siblings use OPPOSITE
letters: A305740's term is k and its exponent m; A153431's term is m and its
exponent k. This README, RESULTS.md, every evidence file, every
`[DISCOVERY]` / `[NEAR]` / `[STATUS]` / `[STAGE]` line and `--status` use
each entry's own letters and say which entry they mean; a statement about
both is made in words ("the term", "the exponent") or once in each entry's
letters, never in a notation of this project's own (CONVENTIONS.md "Naming
in an evidence file"). `oeis_terms` in an evidence file is literally what
to submit, `{"18": <integer>}`. What the engines call their variables stays
in the code.

**The two entries nest, and a find can settle both.** At index n,
A153431's forms m·10^k + 1 for k = 1..n are A305740's 10^m·k + 1 for
m = 1..n with the term renamed, and A153431 adds one more, m + 1 (k = 0).
So A305740(n) ≤ A153431(n), with equality exactly when A305740(n) + 1 is
prime (it was, at n = 1, 2, 3 and 7): an A305740 find k with k + 1 prime is
also A153431's term at that index, if A153431 has not reached it — the
evidence file records it under `also_settles`. **And the shift:** A153431's
m = 10·A305740(n) turns m·10^k + 1, k = 0..n − 1, into
10^(k+1)·A305740(n) + 1 — A305740's forms for exponents 1..n — so
A153431(n − 1) ≤ 10·A305740(n). `decl_reference` G2d checks all three
statements on every published index.

## The mathematics of the engine

**The killed set.** For a prime q other than 2 and 5, A305740's form
10^m·k + 1 is divisible by q exactly when k ≡ −10^(−m) (mod q), and
A153431's m·10^k + 1 exactly when m ≡ −10^(−k) (mod q). So at index n, q
kills K(q,n): one residue of the term per exponent (m = 1..n for A305740,
k = 0..n for A153431), as many distinct ones as the smaller of the number of
exponents and ord_q(10). Primes with 10 as a primitive root kill one residue
per exponent — the linear ladders' law — while the small-order primes are
weak and saturate at their order (3: one residue, 11: two, 37: three, 101:
four, 41: five, 13: six, 73: eight, 53: thirteen, 31: fifteen). 2 and 5
never divide 10^m·k + 1 for m ≥ 1; A153431's extra form m + 1 makes 2 forced
and 5 a one-residue prime.

**Forcing follows primitive roots, so the unit grows with the filter.** q is
forced — the term ≡ 0 (mod q), the one residue no form can kill — exactly
when 10 is a primitive root of q and there are at least q − 1 exponents: 7
from six forms, 17 from sixteen, 19 from eighteen. The engine therefore
sweeps only multiples of a unit: k in multiples of 7, 7·17 = 119 and
7·17·19 = 2261 for A305740 (n = 13–15, 16–17, 18–19), and m in multiples of
14, 238 and 4522 for A153431 (n = 14, 15–16, 17–18) — derived per filter and
refused if not forced (`assert_unit`), because a unit is a coverage claim.

**One line, a filter that grows.** The engine sweeps the published term
itself (A305740's k, A153431's m), so a find at filter n is the floor of
filter n + 1 on the same line. K(q,n) is a
subset of K(q,n+1), so every survivor of the filter-(n+1) sieve is a
survivor at filter n, and every survivor of a closed segment was classified
to run n + 8: the launcher CARRIES the classified line across a promotion
and resumes the new filter at its end (`follow_frontier`). A find whose run
passes the filter is a rider and settles every index it reaches
(A305740's a(4) = a(5), A153431's a(6) = a(7)).

**The engine.** Candidates are carried as pairs — a wheel period and an
offset inside it — so no machine word bounds the search. The GPU never forms the line: it generates the
residues of a three-level CRT wheel (a SUBSET of the small primes, planned
per filter) and sieves a segment of up to 256 wheel periods of each residue
at once — for a fixed residue the periods form an arithmetic progression mod
every sieve prime, so "which periods does q kill" is a window into a
periodic bit pattern. Here those patterns are stored as **overlapping
2-word tuples**, so a thread's window of eight words is four aligned 64-bit
shared loads at the base plus the word index (1.08–1.14× over the scalar
layout; OPTIMIZATION_LOG.md Measurement 6). The window's survivors go
through in-block compaction rounds of single-prime Barrett tests and then
global tail rounds to a sieve depth of 2^17–2^20. The CPU engine marks
arithmetic progressions into a dense array with no wheel at all; the parity
gate (G9) pins the two streams bit for bit on 27 populated windows from 2e9
to the 1e40 ceiling, at every stage of the forced unit.

**The plan is measured, per filter.** At every filter a campaign opens at or
promotes into, the wheel and the window are the measured best of the odds
model's shortlist (the Pareto frontier of period against density, times
windows of 128–256 periods), each run steady-state, counted on the EXACT
candidates each launch covers, and ranked by expected clock to a confirmed
find (`decl_gpu.MEASURED_PLANS`; OPTIMIZATION_LOG.md Measurements 8 and 12 —
the first table was ranked on a rate that overcounted partial launches, and
re-ranked honestly it moved seven filters by 1.03–1.13×). The survivor
record — a u64 offset, or (offset, period) where the wheel's period admits
no u64 window — is the engine's own choice from the plan: WIDE at A305740
n = 18 and 19 and A153431 n = 18, narrow elsewhere.

**Certificates are this project's best case, and the ceiling is 1e40.**
A305740's value 10^m·k + 1, less one, is 2^m·5^m·k, completely factored the
moment k is — and A153431's m·10^k + 1, less one, is 2^k·5^k·m — so ONE
factorization of the term proves the whole run by BLS75 Theorem 1
(A153431's m + 1 included), with a subproof for any prime factor of the
term past the deterministic bound. The proof crossing — where a
classification stops being a deterministic proof — is a term of 3.3e11 at
n = 13 and 3.3e6 at n = 18, below both frontiers, so every discovery here is
a certificate; the ceiling is `huntlib.ceiling.K_CEIL` = 1e40 on the term,
where that certificate's worst case was measured to cost seconds.

## The odds model

Bateman–Horn over each entry's forms (10^m·k + 1 for m = 1..n; m·10^k + 1
for k = 0..n), with the singular series from the same kill counts w(q,n) —
the smaller of the number of exponents and ord_q(10) — the sieve is built
from, so a wrong w would move the model and the engine together.

**Validation (G11), stated before the run.** E — the expected number of hits
the model puts between the previous term and the one that occurred — over
the knowns from n = 6 that were separately searched (a rider scores
nothing): **mean 1.63 over 14 draws** (A305740 2.06 over 7, A153431 1.20 over
7), spread 0.00–5.38, against the Exp(1) mean of 1. A305740's a(12) sits at
E = 5.4 (the 99.5th percentile): the entry's last term landed late. The
repository's ladder projects have landed their finds at 1.9–2.5× their
medians while every census showed the intensity right; read every depth
below as a floor.

**Predictions, stated before the run** (`model_results.json`; each term from
the previous term's MEDIAN, the published frontier for the first; times at
the measured steady rates of this engine; P over a day / a week of device
from reaching the filter):

| term | Q1 | median | Q3 | P90 | rate (k/s; m/s) | to the median | cumulative | P(day) / P(week) |
|---|---|---|---|---|---|---|---|---|
| A305740 a(13) | 1.3e14 | **2.6e14** | 5.3e14 | 9.6e14 | 5.01e15 | < 1 s | < 1 s | 100% / 100% |
| A305740 a(14) | 3.4e15 | **9.9e15** | 2.4e16 | 4.8e16 | 1.86e16 | 1 s | 1 s | 100% / 100% |
| A305740 a(15) | 2.5e17 | **7.8e17** | 1.9e18 | 3.8e18 | 7.64e16 | 10 s | 11 s | 100% / 100% |
| A305740 a(16) | 3.4e19 | **1.0e20** | 2.6e20 | 5.1e20 | 4.02e17 | 4 min | 4 min | 100% / 100% |
| A305740 a(17) | 2.5e21 | **7.5e21** | 1.8e22 | 3.5e22 | 1.19e18 | 1.7 h | 1.8 h | 99% / 100% |
| **A305740 a(18)** | 2.8e23 | **8.6e23** | 2.1e24 | 4.1e24 | 5.11e18 | **46 h** | 48 h | 34% / 85% |
| A305740 a(19) | 1.6e25 | **4.7e25** | 1.1e26 | 2.2e26 | 9.44e18 | 57 days | 59 days | 2% / 12% |
| A153431 a(14) | 4.4e17 | **1.3e18** | 3.0e18 | 5.9e18 | 1.61e17 | 8 s | 8 s | 100% / 100% |
| A153431 a(15) | 5.1e19 | **1.6e20** | 4.0e20 | 7.9e20 | 8.65e17 | 3 min | 3 min | 100% / 100% |
| A153431 a(16) | 3.8e21 | **1.2e22** | 2.9e22 | 5.6e22 | 2.65e18 | 72 min | 76 min | 100% / 100% |
| **A153431 a(17)** | 4.4e23 | **1.4e24** | 3.3e24 | 6.5e24 | 1.05e19 | **36 h** | 37 h | 40% / 90% |
| A153431 a(18) | 2.6e25 | **7.5e25** | 1.8e26 | 3.5e26 | 2.04e19 | 42 days | 43 days | 3% / 15% |

So the early terms — A305740 a(13) through a(17), A153431 a(14) through
a(16) — are minutes to two hours of device; **the hunt proper is A305740
a(18) and A153431 a(17)**, about two days and a day and a half at their
medians, and roughly twice that at the optimism factor the earlier ladders
suggest. a(19) and a(18) respectively are months.

**How the finds scored.** Everything above this line was written before
either campaign ran. A153431 ran first and found a(14), a(15) and a(16) in
8.4 hours; A305740 then found a(13) and, within two minutes of it, a(14)
through a(16) on the sibling's floors, a(17) 3.6 hours later and **a(18)
after about 90 hours of campaign clock, at 1.99× the median stated above**
— the "roughly twice" this section budgeted. A305740's a(16) is A153431's
a(15) divided by 10 (an A153431 term that ends in 0 is one, by the shift),
so it is one draw, not two. Over the eight searched draws, each scored from
the floor its sweep started at, **E averages 1.65** — next to the 1.63 of
G11's disjoint validation set — and term / median has geometric mean 2.45. The split is the news: A305740's
five draws average E = 1.17, near right, while A153431's three all landed
late (the 88th–94th percentiles, 4.3–5.9× their medians; about a 2% event
under the model), so A153431's intensity at these n looks about twice too
high. Term by term: [RESULTS.md](RESULTS.md).

| open term | searched empty below | median from the bound | device time at the median | P(found) in a day / a week / 30 days |
|---|---|---|---|---|
| A305740 a(19) | k = 1.7633e24 | 4.9e25 | 51 days at ~1.07e19 k/s | 2% / 13% / 36% |
| A153431 a(17) (≤ 1.7052e25) | m = 7.7996e22 | 1.5e24 | 1.4 days at ~1.16e19 m/s | 40% / 91% / 99.9% |

(Discount the A153431 row by the late landings above; the upper bound caps
its leg at 17 days of device whatever the model says.)

## Running it

```bash
python launch.py --selftest     # the full gate battery -- must end ALL GREEN (~5 min)
python score.py                 # gates times seven fingerprinted benchmarks (~2.5 min)
python launch.py --status --family A305740   # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py --family A305740       # indefinite, resumable, to the 1e40 ceiling
python launch.py --family A153431       # the other family
python launch.py --family A305740 --stop-on-discovery   # stop when THIS RUN finds something
python launch.py --family A153431 --to 1e24             # stop at a chosen depth in m
```

One campaign per family, each with its own checkpoint and ledger; run them
one at a time (each takes the whole GPU). The classification pool is sized
at runtime from a measurement at the filter being run (one to four workers;
0.1–0.3 core-seconds per second at the long legs), and `--workers`,
`--gpu-yield-ms` and `--gentle` are the throttles. Requires CuPy and a CUDA
GPU; sympy and numpy for the oracle and the CPU engine.

**Hunt A153431 first** — and it was. A305740(n) ≥ ⌈A153431(n − 1)/10⌉ (a
k with an A305740 run of n makes m = 10k meet A153431's condition at index
n − 1), and the launcher starts A305740's sweep there by itself as soon as
A153431's term is settled — published, in `FOUND`, or a verified first
occurrence in `evidence/` (OPTIMIZATION_LOG.md Measurement 15). Run in that
order, this project's A153431 terms gave A305740 its floors for a(15)
through a(17) (a(14)'s came from the published a(13)), and a(16) outright:
A153431's a(15) ends in 0, and a(15)/10 — the floor itself — is A305740's
a(16). The relation, read the other way, bounds A153431 from above, and now
it binds: A305740's a(18) caps A153431's a(17) at 10·A305740(18) =
1.7052e25 and rules out every m that is a multiple of 10 below that (the
class-0 lever, OPTIMIZATION_LOG.md "Priced and declined" 5,
priced at 1.33× on the leg and not built). **Next, by price: A153431 a(17)**
— about a day and a half of device at the model's median. A305740's a(19)
gets a sibling floor only once A153431's a(18) is settled.

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md) and
[INNOVATION.md](../INNOVATION.md). Specific to this project:

* **The nesting and the shift are gated, not quoted** (`decl_reference`
  G2d): A305740(n) ≤ A153431(n) with equality exactly where A305740(n) + 1
  is prime, and m = 10k carries k's A305740 run, less one, into A153431, on
  every published index. The protocol drill checks that an A305740 find k
  settles A153431 only with k + 1 prime and only at an unpublished index.
* **The unit is derived and refused.** `assert_unit` raises on a unit with a
  prime that is not forced at the filter — 119 one filter early, 14 for
  A305740 (2 kills nothing there), 6 (3 is never forced) — or that is not
  squarefree; G3, G7 and the ceiling drill require the refusals.
* **The window layout is pinned three ways.** G14 checks every bit the
  kernel would read (the `x0` table, the per-block offsets, the borrow and the tuple
  word) against `killed_residues`; G21 runs the scalar, 2-tuple and 4-tuple
  layouts against the CPU engine at windows of 160, 224 and 256 periods on
  both records; and the anchors SCORE2L / SCORE1L / SCORE9 reproduced their
  fingerprints unchanged through the change.
* **Every rate is counted, not multiplied.** The launches of a segment are
  not equal — the last first-level chunk of each unit is partial — and a
  rate taken as launches × a full launch overcounted by 1.12–1.30×,
  differently per launch geometry, which is enough to pick the wrong plan
  (it did, at seven filters). The engine carries the exact per-launch
  candidate counts (`launch_cum`), and `score.py`, the launcher's
  calibration and its heartbeat all read the line from them
  (OPTIMIZATION_LOG.md Measurement 12).
* **A hazard the gates caught while this project was built.** The inherited
  engine decided whether a wheel level exists with `p2 > p1`, which compares
  list-valued levels lexicographically: a level whose smallest prime sat
  below level 1's would have been dropped from the wheel and — the sieve
  being the complement of the named wheel — from the sieve. The engine now
  refuses any wheel whose built prime set is not the named one.
