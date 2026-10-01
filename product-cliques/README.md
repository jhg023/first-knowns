# product-cliques — A034881 and A219761

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of two OEIS sequences that are one object seen
twice: **join two integers when their product plus one is prime, and grow
the clique greedily from 1** — a(n) is the least integer above a(n−1) for
which a(n)·a(i) + 1 is prime for every earlier term a(i). A219761 also asks
that each term join *itself*, a(n)² + 1 prime. It is the multiplicative twin
of the six additive cliques in [clique-ladders](../clique-ladders/), and
both entries cite that family. Neither had moved since 2012.

**Status: PAUSED — open to others** — **11 terms found & verified
2026-09-29 to 2026-10-01**: a(16)–a(19) of A034881 and a(12)–a(18) of
A219761 ([RESULTS.md](RESULTS.md)), the first advance on either since 2012.
Paused with each family's next term open just above its last find: a(20) of
A034881 above a(19) = 2,412,240,527,764,607,793,810, and a(19) of A219761
above a(18) = 8,981,486,409,894,740,569,620. Both are multi-week terms.

**In the OEIS** (checked against the 2026-10-01 export): none of the eleven
is entered yet. A034881 still ends at a(15), with its comment
"a(16) > 2·10^16", and A219761 at a(11).

## The problem

| entry | condition | published terms | published frontier | last moved |
|---|---|---|---|---|
| [A034881](https://oeis.org/A034881) | a(n)·a(i) + 1 prime for all 1 ≤ i ≤ n − 1 | 15 | a(15) = 18,216,437,241,240 | Don Reble, Oct 2012 |
| [A219761](https://oeis.org/A219761) `more` | a(n)·a(n−i) + 1 prime for all 0 ≤ i ≤ n − 1 | 11 | a(11) = 7,746,764,190 | Robert G. Wilson v, Dec 2012 |

Both start at a(1) = 1. A034881 is Erich Friedman's, with a(9)–a(13) by Phil
Carmody and a(14)–a(15) by Don Reble; it links a 2003 sci.math thread, "Sets
producing primes", and carries the unattributed comment "a(16) > 2·10^16".
It is not tagged `more`, which is why a scan of `more` entries misses it.
A219761 is Sloane's (Dec 2012, from a Sequence Fans posting by Rainer
Rosenthal), with a(8)–a(11) by Robert G. Wilson v. Its i = 0 condition is
the self-product a(n)² + 1, and that is the whole difference: the two
families part at a(4), where A034881 takes 18 and A219761 cannot, because
18² + 1 = 325.

No derived entry rides on either (checked against the 2026-09-29 export;
A274694, "1 + the product of any two distinct terms is a prime power", is a
different sequence).

**Notation, and which number goes in the OEIS.** Neither name gives the term
a letter — they say a(n) — so that is what an evidence file carries it
under: the field `a(n)` is the term, `forms` is the entry's own condition,
and `oeis_terms` is literally what to submit, `{"16": <integer>}` reading
"a(16) is this integer". Only the code calls the swept candidate `x`, which
*is* the term (CONVENTIONS.md "Naming in an evidence file").

## The mathematics of the engine

**The form list is state.** At index n the conditions on the candidate
a(n) are the products with every earlier term, a(1)·a(n) + 1 up to
a(n−1)·a(n) + 1, plus A219761's a(n)² + 1. The filter for a(n+1) does not
exist until a(n) does, so, exactly as in clique-ladders: one opening per
family, a find restarts the sweep just above itself (the new index has a
condition the old filter never tested), no riders, and a find is re-derived
by the oracle from the bare definition against the whole prefix before
anything is written.

**The killed set.** A prime q kills, for each product form, the one residue
of a(n) at which q divides a(n)·a(i) + 1 — the negative inverse of a(i)
modulo q, and nothing when q divides a(i) — and, for a(n)² + 1, the square
roots of −1 modulo q: two when q ≡ 1 (mod 4), none when q ≡ 3 (mod 4). That
second form is the one thing the engines had to learn, because a prime can
now kill one more residue than there are conditions: the per-prime residue
lists are sized from the forms' degrees (`maxkills`), not their count. The
oracle walks every residue; the CPU engine builds the set algebraically with
its own Tonelli–Shanks; the GPU engine consumes the set and never sees a
form.

**Admissibility is a theorem here, and the class is 0 (mod 6).** Every
condition is 1 when a(n) ≡ 0 (mod q), so residue 0 survives every prime at
every index — the sequence can never be emptied by a local obstruction (in
clique-ladders that had to be *checked* at each promotion). Two and three
are forced from a(3) on: 1·a(n) + 1 kills a(n) ≡ 1 (mod 2) and ≡ 2 (mod 3),
2·a(n) + 1 kills a(n) ≡ 1 (mod 3). No larger prime is ever forced: the map
r → −r⁻¹ is an involution of the nonzero residues, and two terms whose
residues it swaps have a(i)·a(j) + 1 ≡ 0 (mod q), which a prime value allows
only by *being* q — it happens among the first few terms (1·6 + 1 = 7,
2·6 + 1 = 13) and nowhere a multiplier is large. So a prime kills at most
about half its classes, and every published term from a(3) is a multiple of
6. `product_reference` G2c and G2d check all of it at every index that
exists.

**The engine** began as clique-ladders' v1, unchanged except for the
residue-list sizing: factorial-ladders' window sieve (a segment of wheel periods sieved
at once against periodic bit patterns, in-block and tail compaction rounds,
the narrow or wide survivor record chosen at runtime), subset wheels, the
2⁶⁴ reduction bound, the forced class (in the code, `x = r0 + unit*t`), and
a planner that chooses the wheel and the window together to minimise the
*expected clock to a confirmed find* (a find is only the least once its
segment closes, and here the rest of that segment is thrown away). Engine
v2 (OPTIMIZATION_LOG.md round 1) is this project's own: measured here, the
window sieve is bound by the *issue* of shared-memory loads, and a 64-bit
load costs what a 32-bit one does, so the window's periodic patterns are
stored as overlapping word pairs and read two words a load — three loads a
prime where there were five — with the live words kept in registers and
the window sieved deeper. Every window now spans 160 periods (planner p3).
The stream is unchanged: every v1 fingerprint reproduces bit for bit. It is
1.27–1.46× on the expected clock at every filter a campaign passes through.
The sieve is planned deep enough that a pool of one or two workers keeps up past the
opening filters. The parity gate (G9) pins GPU against CPU bit for bit on
24 populated windows: both families, the quadratic form, the dense line and
the forced class, one- to three-level and subset wheels, above 2⁶⁴, past each proof
crossing, and hard against the ceiling.

**The ceiling is 1e40, and this project is rule 5h's best case.** Every
value less one is a(i)·a(n) or a(n)²: completely factored the moment a(n)
is, since each prefix term was factored when it was found. So one
factorization of a(n) proves every value of a run by BLS75 Theorem 1, at any
height, with a subproof for any prime factor past the deterministic bound.
That matters from the start: the deterministic Miller–Rabin bound is crossed
where a(n−1)·a(n) + 1 passes 3.3e24 — at a(n) ≈ 1.8e11 for A034881's open
index, a hundred times below its frontier, and at 1.8e12 for A219761's (where
a(n)² + 1 passes it) — so nearly every value this hunt classifies is past the
bound, and every discovery there is proved by certificate. The certificate
drill proves this project's own values at 1e40, a(n)² + 1 included (an
80-digit value), with the recursion exercised.

## The odds model

Bateman–Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from, and the integrand
1/Π ln(value) with each product value about a(i)·a(n) — the multipliers are
the sequence's own terms, which is why each index costs more than in an
additive ladder.

**Validation (G11), stated before the run.** E — the expected number of hits
between a(n−1) and the a(n) that actually occurred, given the real prefix —
is a draw of Exp(1) under a correct model. Over the twelve published terms
searched above the exception zone (a(n−1) ≥ 10⁴: n ≥ 9 in A034881, n ≥ 7 in
A219761) the E's sum to **5.79**: A034881 mean 0.41 over 7, A219761 0.58
over 5. That sum sits at P = 0.016 in the lower tail of its Gamma(12, 1)
law — unusual, not damning, and in the direction of **terms arriving early**.
The quantiles 1 − e^(−E) run 0.01–0.82. So G11 tests the law (neither 0.1%
tail, quantiles scattered, per-family means in (0.2, 4)) rather than a mean
inside a band; the band clique-ladders used was sized for 49 draws and would
fail a correct model on twelve one time in five. **Read every median below
as conservative.**

**The model sees exactly one term ahead.** The first row per family is the
model's real answer; every later row replaces each unknown term by a
*stand-in* — the first integer past the previous median, in a seeded free
class of the small primes, that no prime under 2000 kills — and is a
**projection** (`model_results.json`). The tables in this section are as
stated before the run; "How it came out" below scores them.

| family | open term | Q1 | median | P90 | then, projected medians |
|---|---|---|---|---|---|
| A034881 | a(16) | 3.4e16 | **5.6e16** | 1.7e17 | 1.1e18, 3.8e19, 1.5e21, 6.8e22, 3.4e24 |
| A219761 | a(12) | 3.8e11 | **1.4e12** | 8.1e12 | 4.7e13, 1.6e15, 6.9e16, 2.7e18, 1.3e20 |

A034881's a(16) row is conditioned on the entry's "a(16) > 2·10^16"; the
campaign does not rely on that bound — sweeping from a(15) to 2e16 is under
a second of device — so it re-establishes it.

**What that costs.** The planned configuration measured through the engine
API at each opening and at the model's stand-in filters (* = projection),
as the expected device clock to a *confirmed* find (BENCHMARKS.md has the
full table):

| A034881 | clock | A219761 | clock |
|---|---|---|---|
| a(16) | 4 s | a(12)–a(14)* | under a second |
| a(17)* | 65 s | a(15)* | 10 s |
| a(18)* | 25 min | a(16)* | 4 min |
| a(19)* | **10.5 h** | a(17)* | **1.5 h** |
| a(20)* | 15 days | a(18)* | **39 h** |
|  |  | a(19)* | 55 days |

(engine v2 and planner p3; v1 read 15.3 h, 2.0 h and 55 h for the three
bold rows.) So a night of each family buys **a(16)–a(19) of A034881 and
a(12)–a(17) of A219761**, with A219761's a(18) a day and a half more: about
ten new terms, four and six-to-seven per entry. Each term costs about 1.6 decades more than
the last. A caveat on what the early ones are worth: A219761's a(12)–a(15)
and A034881's a(16)–a(17) are seconds of device — they stood since 2012
because nobody returned, not because they were hard. The hunt proper is the
last two terms of each.

**How it came out.** A night of each family bought what the table said, and
A219761's a(18) took the day and a half: a(16)–a(19) of A034881 in 8.00 h of
campaign, a(12)–a(18) of A219761 in 43.12 h. Re-scored on the real prefix,
the eleven finds have E summing to **9.54, a mean of 0.87**, at P = 0.36
under the Gamma(11, 1) law. That is the intensity about right; the twelve
published draws had suggested terms come early. The individual draws
scattered. A034881's a(17) and a(18) landed at the 81st and 91st
percentiles, 3–5× their medians. A219761's a(16) and a(17) landed at the
10th and 5th, which is why its six cheap terms took four minutes. The long
legs ran at 1.1× their stand-in prices on A034881, and at 0.72× on
A219761's n = 18, a gap not yet measured (RESULTS.md has every draw and
every leg). Rerun on the real prefix, the open terms' medians are
**8.8e22 for A034881's a(20)** and **1.7e23 for A219761's a(19)**. At the
rates the last legs ran, that is about 11 and 32 days.

## Running it

```bash
python launch.py --selftest     # the full battery -- must end ALL GREEN (~3.5 min)
python score.py                 # gates x five fingerprinted benchmarks (~3 min)
python launch.py --status       # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py                        # A034881, indefinite, resumable (resumes at a(20))
python launch.py --family A219761       # the other family (resumes at a(19))
python launch.py --to 1e20              # stop at a chosen depth in a(n)
python launch.py --stop-on-discovery    # stop when THIS RUN finds something
```

One campaign per family, each with its own checkpoint and ledger. Runs
indefinitely by default, to the 1e40 ceiling. Requires CuPy and a CUDA GPU;
sympy and numpy for the oracle and the CPU engine.

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md). Specific to this project:

* **The definition is regenerated, not quoted.** G1 checks that both
  published lists are cliques under the bare definition and rebuilds each
  greedily from a(1) = 1 below 10⁶ (9 and 7 terms) — which pins the start
  and the self-product condition. G5 has the CPU engine re-derive six
  published terms as first occurrences above their predecessors, and the
  canary has the GPU stream do the same for four more, on the dense line and
  in the forced class.
* **The real loop is run, on published ground.** `_rediscovery_run_drill`
  opens `Campaign.run` below the published frontier on scratch files, in
  both families, and requires it to find a(n), promote itself, and find
  a(n+1) *under the condition a(n) created*, with both evidence files
  complete. It can find nothing new.
* **A drill may not fabricate a find.** A term becomes part of every later
  index's definition and the oracle keeps it, so drill campaigns open below
  the published frontier and "find" real published terms (`DRILL_N`), with
  those terms hidden from the oracle until the campaign registers them.
* **An earlier term is not a later one.** An earlier term satisfies *every*
  condition of a later index — a clique is a clique in any order — so what
  rejects it is the ordering alone. The protocol drill checks exactly that,
  and that 18, A034881's a(4), is refused as A219761's by 18² + 1 alone.
* **Everything past the bound is proved, not tested.** Every certificate is
  BLS75 Theorem 1 on a completely factored N − 1 (R = 1), re-verified from
  scratch before it is written; a value that cannot be proved is reported in
  the evidence file's `unproved` list, never hidden.
