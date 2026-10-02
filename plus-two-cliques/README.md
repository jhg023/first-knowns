# plus-two-cliques — A083518 and A083519

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of two OEIS sequences that are one object seen
twice: **join two integers when their product plus two is prime, and grow
the clique greedily** — a(n) is the least integer above a(n−1) for which
a(n)·a(i) + 2 is prime for every earlier term a(i). A083518 grows it from 3,
A083519 from 1. It is [product-cliques](../product-cliques/)' clique with
the constant one changed to two. A083518 has stood at a(13) since 2004 and
A083519 at a(10) since 2008.

**Status: PAUSED — open to others** — **14 terms found & verified
2026-10-02**: a(14)–a(19) of A083518 and a(11)–a(18) of A083519
([RESULTS.md](RESULTS.md)), the first advance on either since 2004 and
2008. Paused with each family's next term open just above its last find:
a(20) of A083518 above a(19) = 517,222,792,129,337,171,163, and a(19) of
A083519 above a(18) = 1,352,093,682,658,200,396,075. Each is about a week
of device at its median.

**In the OEIS** (checked against the 2026-10-02 export): none of the
fourteen is entered yet. A083518 still ends at a(13), with its comment
"Next term is > 266\*10^9", and A083519 at a(10).

## The problem

| entry | name (%N), verbatim | offset | published terms | published frontier | last moved |
|---|---|---|---|---|---|
| [A083518](https://oeis.org/A083518) `more` | Beginning with 3, a(i)*a(j) + 2 is prime for all i, j, i != j. | 1 | a(1)–a(13) | a(13) = 77,597,861,913 | David Wasserman, Nov 2004 |
| [A083519](https://oeis.org/A083519) `hard,more` | Beginning with 1, a(i)*a(j) + 2 is prime for all i, j, i != j. | **0** | a(0)–a(10) | a(10) = 8,403,613,179 | Donovan Johnson, Nov 2008 |

Both are Amarnath Murthy and Meenakshi Srikanth's (May 2003). A083518's
a(9)–a(13) are David Wasserman's, with his comment "Next term is >
266\*10^9" and the conjecture that the sequence is finite. A083519 was
corrected and extended by Stefan Steinerberger (June 2007), and its a(10) is
Donovan Johnson's. Both entries say the terms increase. A083519's own
comment (Chai Wah Wu, 2019) says the definition assumes a(i+1) > a(i). So
a(n) is the least integer above a(n−1) with a(n)·a(i) + 2 prime for every
earlier term: i = 1..n−1 in A083518 and i = 0..n−1 in A083519. **There is no
self condition**, since the name says i ≠ j: a(n)² + 2 need not be prime,
and A083518's a(2) = 5 has 5² + 2 = 27.

**The offset is the trap of this project.** A083519 starts at a(0) (%O 0,2),
so its published list is a(0)–a(10) and its open term is **a(11)**.
A083518 starts at a(1) and its open term is a(14). Every index anywhere in
this project is the OEIS index by the entry's own %O line: an evidence
file's `oeis_terms`, its name, every log line, `--status` and this page.
The entry's own %e line counts the other way. It says "a(4) = 9", where by
%O and %S, 9 is a(3). G1c and the offset drill rebuild every index from the
%S and %O lines, verbatim.

No derived entry rides on either: none is an affine map of them (checked
against the 2026-10-01 export).

**Which number goes in the OEIS.** Neither name gives the term a letter of
its own. Both write a(i)·a(j), and A083519's %C writes a(n). So an evidence
file carries the term under the field `a(n)`, and `forms` reads
"a(n)\*a(i) + 2, i = 1..n-1" (A083518) or "i = 0..n-1" (A083519).
`oeis_terms` is literally what to submit: `{"14": <integer>}` reads "a(14)
is this integer".

## The mathematics of the engine

**The form list is state.** At index n the conditions on the candidate a(n)
are its products with every earlier term, a(i)·a(n) + 2. The filter for
a(n+1) does not exist until a(n) does, so, exactly as in product-cliques:
one opening per family, a find restarts the sweep just above itself (the new
index has a condition the old filter never tested), no riders, and a find is
re-derived by the oracle from the bare definition against the whole prefix
before anything is written.

**The killed set.** A prime q kills, for each earlier term a(i), the one
residue of a(n) at which q divides a(i)·a(n) + 2: −2 times the inverse of
a(i) modulo q, and nothing when q divides a(i) (the value is then 2 modulo
q). The oracle walks every residue. The CPU engine builds the set with its
own modular inverses, and the GPU engine consumes the set and never sees a
form.

**Admissibility is a theorem, and the class is 3 (mod 6).** When a(n) is 0
modulo an odd prime q every value is 2 modulo q, so residue 0 survives every
odd prime at every index. Modulo 2 every value is a(n) itself (every term is
odd), so a(n) must be odd, and 2 kills only the even class. Modulo 3, −2 is
1 and each nonzero residue is its own inverse, so a term that is 1 (mod 3)
kills a(n) ≡ 1 and a term that is 2 kills a(n) ≡ 2. A083518's 5 and 7 are
one of each from a(4) on, and A083519's 1 and 5 from a(3) on. **The forced
class is a(n) ≡ 3 (mod 6)**, not product-cliques' 0, and every published
term from those indices is in it. Five is never forced. A083518 keeps
a(n) ≡ 0, 2, 3 (mod 5) and A083519 keeps 0 and 4. Those are the last digits
Pontus von Brömssen's comments on the two entries state (3, 5, 7 and, from
a(2), 5 or 9), and no later term can change them. No larger prime is ever
forced either. The map r → −2·r⁻¹ is an involution of the nonzero residues,
and two terms whose residues it swaps have a(i)·a(j) + 2 ≡ 0 (mod q), which
a prime value allows only by *being* q (3·5 + 2 = 17, 1·3 + 2 = 5, …, all
among the first few terms). A term may also sit on a fixed point,
a(i)² ≡ −2, because there is no self condition. So a prime kills at most
(q + 1)/2 of its classes plus one per such pair. `plus2_reference` G2c and
G2d check all of it at every index that exists.

**The engine** is product-cliques' engine v2 and planner p3, taken whole:
the window sieve read from overlapping word pairs, subset wheels, the 2⁶⁴
reduction bound, the narrow and wide survivor records, and the planner that
chooses wheel and window together to minimise the *expected clock to a
confirmed find*. The kernel sees killed residues, never a form, and this
project's class is the first nonzero one it has swept, so the gates pin the
class end to end. This project's round 1
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)) re-swept every inherited
constant at its own hour filters and found each of them still the optimum.
It added one thing: a **second first-level budget** for wheels nothing under
the old one can split. That lets the planner take the full wheel to 53 at
the multi-day filters, which measured 1.10–1.21× on the expected clock
there and changes no other plan (planner p2). It also capped a first-level
chunk at CUDA's gridDim.y, a latent bug the new budget exposed and G9
caught. **Engine v2** (round 2) measured the kernel before changing it: it
is bound by shared/global load issue, and the window's loads are already at
their ideal count, so v2 changed what is *not* the window. The narrow
in-block rounds skip both corrections of their reductions over tripled
tables, a queue entry is one 32-bit word, the window's per-thread offsets
are packed two to a word (a sixth block per SM), and each launch builds its
blocks' offset rows once instead of every block recomputing them. The
survivor stream is identical, and every fingerprint reproduced. It runs
**1.09–1.15×** the v1 rate at every filter the campaigns spend hours or days
in. **Engine v3** (round 3) was measured where the campaign stood, at
A083518's filter n = 20 on its real terms, again with Nsight Compute before
anything changed: the kernel's shared-memory data path at 87% of its peak,
five blocks per SM for want of 54 bytes of shared memory, and the wide
record's in-block rounds reading a 3 GB table of per-residue rows in badly
coalesced loads. So a sieve prime up to 96 is no longer read across the
whole 160-period window (its pattern repeats inside the window, so three of
the five words are read, in one 16-byte load, and two are shifts of those);
the wide record's rounds run the narrow record's arithmetic with the period
folded into each reduction, which retires the rows and their shared-memory
slots; and the first tail rounds are generated with their primes as
literals. The stream is identical on the same plan and the same launches,
every fingerprint reproduced, and it runs **1.10×** the v2 rate at that
filter and 1.04–1.12× at every filter measured, on a third of the device
memory. The parity gate (G9) pins GPU against CPU bit for bit on 26
populated windows: both families, the class 3 (mod 6), one- to three-level
and subset wheels, first levels of 11 million residues on both records,
above 2⁶⁴, past each proof crossing, and hard against the ceiling.

**The ceiling is 10³⁰, measured, and why it is not 10⁴⁰.** Rule 5h's 10⁴⁰
rests on a structure this project does not have. In every multiplicative
ladder here a value less one, or plus one, is the term times known numbers,
so one factorization of the term proves a whole run. Here N − 1 is
a(i)·a(n) + 1 and N + 1 is a(i)·a(n) + 3, numbers like any other, so each
value is proved on its own by a bounded certificate search on N − 1 or
N + 1: huntlib's default search, then one retry at 200 ECM curves. Measured
on random primes of this project's shape, every one of 341 values from 45
to 60 digits was proved, the worst in about 22 s. At 62 digits 2 of 25 were
not, and at 65 digits 2 of 20. A find's largest value is about a(n)²/30, so
at a term of 10³⁰ it is about 59 digits, the top of the measured zone. The
hunt's reach this season is about 10²³. The deterministic Miller–Rabin
bound is crossed where a(n−1)·a(n) + 2 passes 3.3×10²⁴: at a term of
4.3×10¹³ for A083518's open index and 3.9×10¹⁴ for A083519's. The early
finds are therefore proved by the deterministic test, and everything from
about a(15) by certificate.

## The odds model

Bateman–Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from, with each product value about
a(i)·a(n). The multipliers are the sequences' own terms, which is why each
index costs more than in an additive ladder.

**Validation (G11), stated before the run.** E is the expected number of
hits between a(n−1) and the a(n) that actually occurred, given the real
prefix, and under a correct model it is a draw of Exp(1). Over the nine
published terms searched above the exception zone (a(n−1) ≥ 10⁴, which is
n ≥ 9 in A083518 and n ≥ 7 in A083519) the E's are:

| A083518 | a(9) | a(10) | a(11) | a(12) | a(13) | | A083519 | a(7) | a(8) | a(9) | a(10) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E | 1.00 | 0.07 | 0.93 | 1.31 | 0.49 | | E | 0.34 | 0.16 | 0.35 | 3.14 |

They sum to **7.79** (mean 0.76 and 1.00 per family), at P = 0.38 under the
Gamma(9, 1) law, with quantiles 0.07–0.96. That is the intensity about
right, on too few draws to say more. product-cliques' published draws came
early and its eleven finds at the intensity, so **read the whole quantile
table, not the median**.

**The model sees exactly one term ahead.** The first row per family is the
model's real answer. Every later row replaces each unknown term by a
*stand-in*: the first integer past the previous median, in a seeded free
class of every prime to 31 (so 3 mod 6), that no prime under 2000 kills.
Those rows are a **projection** (`model_results.json`).

| A083518 | Q1 | median | P90 | | A083519 | Q1 | median | P90 |
|---|---|---|---|---|---|---|---|---|
| a(14) | 1.33e12 | **3.62e12** | 1.86e13 | | a(11) | 1.86e10 | **3.74e10** | 1.48e11 |
| a(15)* | 3.58e13 | 1.11e14 | 6.03e14 | | a(12)* | 2.34e11 | 6.72e11 | 3.52e12 |
| a(16)* | 1.28e15 | 3.98e15 | 2.14e16 | | a(13)* | 7.75e12 | 2.43e13 | 1.31e14 |
| a(17)* | 4.83e16 | 1.49e17 | 7.82e17 | | a(14)* | 2.86e14 | 8.79e14 | 4.62e15 |
| a(18)* | 2.08e18 | 6.44e18 | 3.34e19 | | a(15)* | 9.38e15 | 2.82e16 | 1.44e17 |
| a(19)* | 8.61e19 | 2.62e20 | 1.33e21 | | a(16)* | 3.27e17 | 9.78e17 | 4.94e18 |
| a(20)* | 3.68e21 | 1.12e22 | 5.61e22 | | a(17)* | 1.32e19 | 3.99e19 | 2.00e20 |
| a(21)* | 2.20e23 | 6.79e23 | 3.41e24 | | a(18)* | 5.13e20 | 1.53e21 | 7.56e21 |
| | | | | | a(19)* | 2.37e22 | 7.14e22 | 3.52e23 |

A083518's a(14) row is conditioned on Wasserman's bound, 2.66×10¹¹. The
campaign does not rely on that bound: it sweeps from a(13) + 1, which is
under a second of device, and so re-establishes it.

**What that costs.** The planned configuration was measured through the
engine API (engine v2) at each opening and at the model's stand-in filters
(* = projection). The figure is the expected device clock to a *confirmed*
find ([BENCHMARKS.md](BENCHMARKS.md) has the full table):

| A083518 | clock | A083519 | clock |
|---|---|---|---|
| a(14)–a(16)* | under 2 s each | a(11)–a(15)* | under 5 s each |
| a(17)* | 34 s | a(16)* | 76 s |
| a(18)* | 14 min | a(17)* | 29 min |
| a(19)* | **5.9 h** | a(18)* | **11.5 h** |
| a(20)* | 7.1 days | a(19)* | 14.0 days |
| a(21)* | 8.2 months | | |

So **a night of each family buys a(14)–a(19) of A083518 and a(11)–a(17) of
A083519**, with A083519's a(18) half a day more. That is about thirteen new
terms, six and seven or eight per entry. Each term costs about 1.5 decades
more than the last. A caveat on what the early ones are worth: everything
up to A083518's a(18) and A083519's a(17) is minutes of device or less.
Those terms stood since 2004 and 2008 because nobody returned to these
entries, not because they were hard. The hunt proper is A083518's a(19)
and a(20) and A083519's a(18) and a(19).

**How it came out.** A night of each family bought what the table said:
a(14)–a(19) of A083518 in 8.38 h of campaign and a(11)–a(18) of A083519 in
6.86 h, the two long legs 6.34 h and 6.23 h. Re-scored on the real prefix,
the fourteen finds have E summing to **13.15, a mean of 0.94**, at P = 0.44
under the Gamma(14, 1) law, and with the nine published draws the
twenty-three sum to 20.94 (P = 0.35): the intensity is right. The draws
scattered as they should. A083519's a(15) and a(16) landed at the 93rd and
94th percentiles, 5–7× their medians, and its a(14) at the 7th; A083518's
six averaged 0.58, a little early. A083518 ran at 0.84–1.04× its stand-in
prices on the long filters and A083519 at about 0.67× on every filter past
the openings, a gap not yet measured (RESULTS.md has every draw and every
leg). Rerun on the real prefix, the open terms' medians are **1.17e22 for
A083518's a(20)** and **4.81e22 for A083519's a(19)**. At the rates the open
filters ran at before they were stopped, that is about 7 and 11 days.

## Running it

```bash
python launch.py --selftest     # the full battery -- must end ALL GREEN (~3 min)
python score.py                 # gates and five fingerprinted benchmarks (~2.5 min)
python launch.py --status       # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py                        # A083518, indefinite, resumable (opens at a(14))
python launch.py --family A083519       # the other family (opens at a(11))
python launch.py --to 1e20              # stop at a chosen depth in a(n)
python launch.py --stop-on-discovery    # stop when THIS RUN finds something
```

One campaign per family, each with its own checkpoint and ledger. Runs
indefinitely by default, to the 10³⁰ ceiling. Requires CuPy and a CUDA GPU;
sympy and numpy for the oracle and the CPU engine. At the multi-day filters
the planned wheel holds 0.5–1.4 GiB of device memory (engine v3; v2 held
1.2–4.3 there).

**What the first `[STATUS]` lines should show** (the rule 5g acceptance test
is the owner's, from those lines). With the checkpoints in place, each
campaign resumes inside the first segment of its open filter: one `[STAGE]`
line saying the cursor was read (A083518's was written by engine v2 and is
inherited at its launch), then `[STATUS]` lines naming the filter
("A083518 filter n = 20"), a rate near the one the filter ran at before the
stop (4.1e16 a(n)-line/s on v2 at A083518's n = 20, 4.6e16 measured on v3
there; 9.7e16 at A083519's n = 19), `pool 1` or `pool 2` with no HOST-BOUND
fragment, and `next a(20)` or `next a(19)` at the model's quantile for the
open term, never for one already found. The odds read 0% until the claim
passes the open term's lower quantiles. **Without the checkpoints** (a fresh
clone) each campaign opens at the published frontier, a(14) and a(11), and
re-derives the fourteen terms before it reaches the open ones: A083518's
a(14)–a(17) inside a minute from a pool of four, then a(18) in minutes and
a(19) in about six hours; A083519's a(11)–a(15) inside a minute from a pool
of two, then a(16) and a(17) in minutes and a(18) in about six hours. That
is what the run in RESULTS.md looked like.

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md). Specific to this project:

* **The definition is regenerated, not quoted.** G1 checks that both
  published lists are cliques under the bare definition and rebuilds each
  greedily from its first term below 10⁶ (10 and 9 terms), which pins the
  start and the absence of a self condition. G5 has the CPU engine re-derive
  six published terms as first occurrences above their predecessors, and
  the canary has the GPU stream do the same for four more (A083518's a(12),
  a(13), A083519's a(9), a(10)) in six runs, in the class 3 (mod 6) as well
  as on the dense line.
* **Engine v2's two new mechanisms are pinned on their own.** G21 emulates
  the lazy round reductions bit for bit over every pack of the A083518
  opening and trips on a pack past their 2^31 bound; G22 reads the
  per-launch offset table back against its definition row for row. Both
  A/B the device stream against the path they replaced, and G9 and the five
  fingerprints pin the whole of v2 to v1 and to the CPU engine.
* **So are engine v3's.** G14 forms every window word the way the kernel
  does (three words read, the rest derived, on pair and on quad tables) and
  compares it with the plain pattern at every position of every group. G21
  emulates the wide record's folded reductions and every generated tail
  round bit for bit, each with a tripwire past its bound, and A/Bs both on
  the device against the paths they replaced; G20 puts both kinds of wide
  round against the CPU engine. A v2 checkpoint is read under v3 only in
  its own launch units (the inherited-cursor drill): v3 cuts a segment into
  the same launches and returns the same stream launch for launch, so a
  campaign started on v2 resumes at the launch it stopped at.
* **Every index is the OEIS index.** G1c rebuilds both lists from the %S and
  %O lines stored verbatim in the oracle. The offset drill puts each
  frontier term through everything a person reads about a find: the
  evidence header, the file name, the [DISCOVERY] headline, the open index,
  and the run a classifier reads. It also requires A083519's 9 to be filed
  as a(3), whatever the entry's %e line says.
* **The real loop is run, on published ground, and cannot reach the open
  index.** `_rediscovery_run_drill` opens `Campaign.run` below the published
  frontier on scratch files, in both families: A083518 at a(12), A083519 at
  a(9). It requires the loop to find a(n), promote itself, and find a(n+1)
  *under the condition a(n) created*, with both evidence files complete and
  keyed by the OEIS index. A drill-only bound then stops the run before the
  filter after that is swept, so a drill can never hunt an open term.
* **A drill may not fabricate a find.** A term becomes part of every later
  index's definition and the oracle keeps it, so drill campaigns open below
  the published frontier and "find" real published terms, with those terms
  hidden from the oracle until the campaign registers them.
* **An earlier term is not a later one.** An earlier term is joined to every
  other term, so at a later index it can fail only its own square plus two.
  What rejects it is the ordering, and the protocol drill checks exactly
  that.
* **Everything past the bound is proved, not tested.** Every certificate is
  BLS75 Theorem 1 or 5 on N − 1, or Theorem 15 on N + 1, found by a bounded
  search and re-verified from scratch before it is written. A value no
  bounded search proves is reported in the evidence file's `unproved` list,
  never hidden. The certificate drill proves values at the ceiling with the
  recursion exercised, and a value the first search misses by the retry.
