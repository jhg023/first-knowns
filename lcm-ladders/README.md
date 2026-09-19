# lcm-ladders — A078502, A074200, A093554, A093553

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of four OEIS sequences that ask the same
question twice, with the sign flipped: **what is the smallest N for which
every one of (N ± k)/k, k = 1..n, is prime?** All four frontiers were last
moved between 2003 and 2004, by Jens Kruse Andersen; none carries a bound of
any kind at any open index, and none has a b-file. The substitution that
makes them tractable is that N must be a multiple of L = lcm(1..n), so
N = L·x and the conditions become **(L/k)·x ± 1 prime for k = 1..n** — one
unknown, a list of multipliers, a fixed sign: the linear ladder this
repository has hunted four times, with a wheel that behaves nothing like the
others. **The standing result: a(15) through a(19) of A078502 and a(15),
a(16) of A074200, found and verified 2026-09-06 — seven terms on six
integers, each proved prime value by value — and with them a(15)–a(19) of
A093554 and a(15), a(16) of A093553: fourteen new terms in all**
([RESULTS.md](RESULTS.md)).

**Status: PAUSED — open to others** — A078502 stands at a(18) = a(19) =
52,270,101,840,951,834,355,676,160,000 with a(20) open and priced at most of
a year; A074200 at a(16) = 10,316,338,205,727,668,643,809,280 with no
a(17) below N = 2.4017e27 and **a(17) about 43 minutes of device away at the
median** — it was stopped early, not exhausted. Both campaigns resume from
their checkpoints with no flags.

## The problem

| entry | definition | terms | frontier | last moved |
|---|---|---|---|---|
| [A078502](https://oeis.org/A078502) | least N with (N − k)/k prime for k = 1..n | 14 | a(13) = a(14) = 7,272,877,497,848,202,240 | Jens Kruse Andersen, Jan 2003 |
| [A074200](https://oeis.org/A074200) | least m with (m + k)/k prime for k = 1..n | 14 | a(14) = 2,918,756,139,031,688,155,200 | Jens Kruse Andersen, Feb 2004 |
| [A093554](https://oeis.org/A093554) | least m with (m − k + 1)/k prime for k = 1..n | 14 | = A078502 − 1 | never extended |
| [A093553](https://oeis.org/A093553) | least m with (m + k − 1)/k prime for k = 1..n | 14 | = A074200 + 1 | never extended |

The last two are riders: Sloane's own comment on each says it is the first
one shifted by one, and `lcml_reference`'s G2d re-derives that from the bare
definition on every published term and on every find. **So a single find
settles two entries, and the two hunted families settle four.**

**Notation, and which number goes in the OEIS.** A078502 calls its term
**N** and A074200 calls its term **m**; this project's prose and code write
both as N, with N = lcm(1..n)·x and x the variable the engine sweeps. An
evidence file follows its own entry — the term is the field `N` in an
A078502 file and the field `m` in an A074200 file, `x` is there too and is
**never** what gets submitted — and `oeis_terms` is literally what to
submit: `{"18": v, "19": v}` reads "a(18) and a(19) are both v". The riders'
integers (A093554 = A078502 − 1, A093553 = A074200 + 1) are in
`also_settles` (CONVENTIONS.md "Naming in an evidence file").

a(15) was open on all four when the project started (the table above is the
frontier as this project found it); a(20) is open on A078502 / A093554 now
and a(17) on A074200 / A093553. The conditions nest in N — anything satisfying
filter n satisfies filter n − 1 — so a(n) is non-decreasing and the previous
term is a free floor; nothing below it has to be swept at all.

## The mathematics of the engine

**The substitution.** (N + s·k)/k is an integer for every k ≤ n exactly when
L(n) | N. Write N = L·x; the k-th condition is (L/k)·x + s prime. The
multipliers are the same for both families and only the sign differs, so the
two share every killed-set size, the whole survival curve and one singular
series.

**The killed set.** For a prime q and a multiplier m, the form m·x + s is
divisible by q only when x ≡ −s·m⁻¹ (mod q), and never at all when q | m.
So q kills exactly

    K(q,n) = { −s·m⁻¹ mod q : m ∈ {L/1, …, L/n}, q ∤ m }

and its size has a closed form, proved in `lcml_reference` and gated three
ways (closed form vs distinct-residue count vs direct divisibility, G2b):

    w(q,n) = n                        for q > n
    w(q,n) = floor(n / q^e)           for q ≤ n, q^e the largest power ≤ n

**This is the whole difference from the linear ladders, and it is a large
one.** There w(q,n) = min(n, q−1) for every q, so every small prime is a
maximal killer. Here the small primes are nearly blind — w(3,15) = 1,
w(5,15) = 3, w(7,15) = 2 — because L/k is divisible by q for all but a
handful of k. The wheel is about **2,400× weaker** at n = 15, and the
compensation is the singular series, which is about **4,600× larger**
(1.34e8 against 2.9e4). Fewer x are killed per unit of line, and each
survivor is far likelier to be a hit. Every engine constant in this project
was re-swept for that regime; none was inherited (OPTIMIZATION_LOG.md).

**Forced divisibility, and why nothing may be cached across filters.** When
w(q,n) = q − 1 only x ≡ 0 (mod q) survives. q = 2 is forced at *every* n,
which is the published observation that A078502(n) ≡ 0 (mod 2L). Above that
the forcing is **sporadic and not monotone**: q = n + 1 is forced whenever
n + 1 is prime, so the forced unit is

| n | 15 | 16 | 17 | 18 | 19 | 20 | 22 |
|---|---|---|---|---|---|---|---|
| unit | 2 | 34 | 2 | 114 | 6 | 30 | 690 |

A campaign therefore changes its unit, its wheel, its sieve depth, its
period and its window width at **every** filter, in both directions. There
is no constant to carry: `plan_for` derives the whole configuration per
filter and the launcher stores none of it (G8, G13, G18 check the planned
configuration at every filter n = 15..20 of both families).

**The wheel is a SUBSET of the primes, not a prefix.** This follows from the
same fact and is worth more than everything else in the engine put together.
Each prime in the wheel multiplies the *period* by q and the candidate
density by keep(q) = (q − w(q,n))/q — and here those two are wildly out of
step. At n = 17, 11, 13 and 17 keep 0.909, 0.923 and 0.941 of the line
between them (they kill almost nothing) while costing a factor of 2,431 in
period, where 47 and 53 keep 0.638 and 0.679 for a factor of 2,491. A prefix
wheel must take the useless three to reach 19, and then the period bound
stops it before 47. Choosing the subset by value density is **1.82× fewer
candidates per unit of line at n = 17, and 1.49× end to end**; the primes
the wheel declines are sieved instead, so the coverage claim is unchanged.

**And every filter is a different line.** N = L(n)·x, so an x at filter n
and an x at filter n + 1 are not the same number. When a find moves the
frontier the campaign rebuilds the engine *and restarts the line* at the new
filter's floor — which is the term just found, so nothing is skipped and
nothing is re-swept. That is the one structural difference from every other
project here, and `_promotion_drill` is the gate for it.

**The engine.** Candidates are carried as (x, off) pairs, so no machine word
bounds the search. The GPU never materialises the x line: it generates the
residues of a three-level wheel and sieves them a SEGMENT of 224 wheel
periods at a time, testing each sieve prime against a periodic bit pattern
(one window is a handful of shared loads and funnel shifts for 192
candidates), then compacts the survivors through in-block rounds and global
tail rounds. The CPU engine marks arithmetic progressions into a dense array
and uses no wheel at all; the parity gate (G9) pins the two streams bit for
bit on 20 populated windows from x = 2e9 up to the 1e40 ceiling.

**The ceiling is 1e40 on x, and certificates are this project's best case.**
Value i is N/i + s, so (N/i + s) − s = N/i, and N = L(n)·x with L(n)
n-smooth: **one factorization of x proves the entire run**, by BLS75
Theorem 1 on V − 1 for A074200 and Theorem 15 (a Lucas sequence per prime)
on V + 1 for A078502. The proof crossing — where a *classification* stops
being a deterministic proof — is low here, x = 9.2e18 at n = 15 and 2.7e17
at n = 17, because the largest value is the published term itself. So the
certificate is the normal path in this project rather than an edge case, and
the ceiling is where its *cost* was measured (`huntlib.ceiling`), not where
the arithmetic runs out.

## The odds model

Bateman–Horn over the n linear forms, with the singular series computed from
the same w(q,n) the sieve is built from — so a wrong w would move the model
and the engine together, and the validation would catch it.

**Validation (G11), stated before the run.** E — the expected number of hits
the model puts between the previous term and the one that actually occurred
— must scatter around 1 on the knowns. Over the 12 independently-searched
terms (riders excluded: one vote per condition) the mean is **1.12**, spread
0.09–3.08: A078502 1.28 over 5 draws, A074200 1.00 over 7.

**Predictions, in x at each filter** (`model_results.json`; multiply by L(n)
for N). Read them as a floor: the ladder projects before this one landed
their finds at about 1.9–2.5× their medians while every census showed the
intensity right to a percent or two.

| term | Q1 | median | Q3 | P90 | L(n) | unit |
|---|---|---|---|---|---|---|
| a(15) A078502 | 3.31e16 | **1.18e17** | 3.19e17 | 6.59e17 | 360360 | 2 |
| a(15) A074200 | 5.28e16 | **1.46e17** | 3.56e17 | 7.03e17 | 360360 | 2 |
| a(16) both | 6.1e18 | **2.13e19** | 5.66e19 | 1.15e20 | 720720 | 34 |
| a(17) both | 2.68e19 | **9.28e19** | 2.45e20 | 4.97e20 | 12252240 | 2 |
| a(18) both | 8.49e21 | **2.89e22** | 7.52e22 | 1.51e23 | 12252240 | 114 |

At the measured rates (BENCHMARKS.md) the median for a(15) is **2 seconds**
of device, a(16) about **55 seconds**, a(17) about **24 minutes** and a(18)
about **12 hours** — per family. So a night reaches a(15), a(16) and a(17) on
both — about 51 minutes of device at the medians, about 2 hours at the 2.5×
this repository's optimism factor suggests budgeting — with a(18) a
multi-day proposition.

**How the finds scored.** Everything above this line was written before
either campaign ran. A078502 then landed a(15) at 21 seconds, a(16) at 8.6
minutes, a(17) at 25.6 minutes and — the draw the table did not price —
a(18) at 2.1 hours, a seventh of its median, as a run of **19**, so a(19)
came with it. A074200 landed a(15) and a(16) inside three minutes and then
swept 47 minutes at n = 17, past twice the median, without an a(17): a 32%
event. Over the six searched draws **E averages 1.26** (A078502 1.33 over 4,
A074200 1.12 over 2) against G11's 1.12 on a disjoint set, and x / median
runs 0.145 to 7.6, geometric mean 1.32. Every timed phase ran inside 11% of
its benchmark. Term by term: [RESULTS.md](RESULTS.md).

| open term | searched empty below | median from there | what it costs |
|---|---|---|---|
| a(17) A074200 (and A093553) | N = 2.4017e27 | x = 3.73e20 at n = 17 | **43 min** at 6.9e16 x/s; 61% inside an hour, 92% inside three |
| a(20) A078502 (and A093554) | — (a(19) only) | x = 1.48e25 at n = 20, N = 3.4e33 | most of a year at the n = 18 rate; n = 20 never measured |

The singular series is **not monotone in n**, and G12 asserts the mechanism
rather than the numbers: it jumps ×44.8 at n = 17 and ×67.0 at n = 19 (when
n is prime it enters L(n) and q = n's kill count collapses from n − 1 to 1),
and *falls* ×0.996 at n = 18, where q = 3 becomes forced.

## Running it

```bash
python launch.py --selftest     # the full battery -- must end ALL GREEN (~3 min)
python score.py                 # gates x seven fingerprinted benchmarks (~3.5 min)
python launch.py --status       # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py                        # A078502, indefinite, resumable
python launch.py --family A074200       # the other family
python launch.py --family A093554       # a rider spelling: opens A078502
python launch.py --to 1e20              # stop at a chosen depth in x
python launch.py --stop-on-discovery    # stop when THIS RUN finds something
```

One campaign per family, each with its own checkpoint and ledger. Runs
indefinitely by default, to the 1e40 ceiling. Requires CuPy and a CUDA GPU;
sympy and numpy for the oracle and the CPU engine.

The project is paused, so whoever resumes it runs the first two commands
before anything else (CLAUDE.md rule 2). A campaign started without this
project's checkpoints begins again from the published a(14); the seven finds
are in `lcml_reference.FOUND`, re-checked from the bare definition by G1b on
every battery, and the bound on A074200's a(17) is in
[RESULTS.md](RESULTS.md).

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md). Specific to this project:

* **The substitution is gated, not assumed.** G2 re-derives the small terms
  *twice* — once by walking N itself with the divisibility test the OEIS
  definition states, once by walking x over N = L(n)·x — and requires them to
  agree.
* **The wheel is re-derived at every filter and refused at the wrong one.**
  `assert_unit` raises on a unit whose primes are not forced at that filter,
  `wheel()` calls it, and G7 requires the n = 16 unit to be *rejected* at
  n = 15 and n = 17.
* **Four wheels, one stream.** G17 sweeps one whole production period with
  the planned wheel, the same primes split at a different level, a coarser
  wheel that covers the window in 43 of its own periods (so 43 moves from
  the wheel into the sieve), and an x-space wheel — and requires the
  identical survivor set.
* **A bug the parity gate caught while this project was being built:** the
  kernel unpacked a queue entry's period index with `qi & (PB - 1)`, a mask
  that is only correct when the window width is a power of two. At the
  measured optimum, 192, it silently over-emitted. The linear ladders never
  saw it because 64 and 128 were the only widths they ran.
