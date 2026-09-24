# clique-ladders — A093483, A103828, A037100, A119752, A119751, A133761

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of six OEIS sequences that are one object seen
from six starting points: **join two integers when their sum plus one is
prime, and grow the clique greedily** — a(n) is the least x > a(n−1) for
which x + a(i) + 1 is prime for every earlier term a(i). Five more entries
are the same integers under an affine map and ride along for free. Two of
the six have not moved since 2008 and carry `hard`; the flagship, A093483,
carries `hard,nice` and Sloane's remark that proving it infinite would prove
the twin prime conjecture. It is the simultaneous-primality ladder this
repository has hunted eight times, with one difference that reaches
everywhere: **the conditions for a(n+1) do not exist until a(n) does.**

**Status: PAUSED — open to others** — **26 terms found & verified
2026-09-19/20 across all six families**, and 22 more riding on them in the
five derived entries: a(18)–a(21) of A093483, a(19)–a(21) of A103828
and of A037100, a(15)–a(20) of A119752 and of A119751, and a(17)–a(20) of
A133761 ([RESULTS.md](RESULTS.md)). The first advance on A093483 since 2012
and on A119751 and A119752 since 2008. Paused with each family's next term
open just above its last find — a(22) of A093483, A103828 and A037100, and
a(21) of A119752, A119751 and A133761.

## The problem

| entry | start, and the extra condition on x | terms | frontier | last moved |
|---|---|---|---|---|
| [A093483](https://oeis.org/A093483) `hard,nice` | 2 | 17 | a(17) = 252,534,792,143,648 | Don Reble, Sep 2012 |
| [A103828](https://oeis.org/A103828) | 1 (odd) | 18 | a(18) = 2,504,509,324,460,255,499 | Don Reble, Aug 2021 |
| [A037100](https://oeis.org/A037100) | 4 (even) | 18 | a(18) = 20,116,294,396,883,346 | Don Reble, Feb 2019 |
| [A119752](https://oeis.org/A119752) `hard` | 2, and 2x + 1 prime | 14 | a(14) = 4,566,262,987,328 | Donovan Johnson, Mar 2008 |
| [A119751](https://oeis.org/A119751) `hard` | 1, and 2x + 1 prime | 14 | a(14) = 4,565,283,812,559 | Donovan Johnson, Mar 2008 |
| [A133761](https://oeis.org/A133761) | 5, and x itself prime | 16 | a(16) = 3,544,413,963,914,171 | Don Reble, Feb 2015 |

That table is the published record this project started from. Where each
entry stands now:

| entry | new terms (this project) | frontier | open |
|---|---|---|---|
| A093483 | a(18)–a(21) | a(21) = 217,741,095,176,373,431,678 | a(22) |
| A103828 | a(19)–a(21) | a(21) = 4,584,245,071,483,320,696,489 | a(22) |
| A037100 | a(19)–a(21) | a(21) = 140,672,999,403,766,760,844 | a(22) |
| A119752 | a(15)–a(20) | a(20) = 23,912,359,356,224,311,448 | a(21) |
| A119751 | a(15)–a(20) | a(20) = 5,566,439,406,842,300,763,219 | a(21) |
| A133761 | a(17)–a(20) | a(20) = 1,206,761,188,144,986,057,371 | a(21) |

In every one of them a(n) is the smallest integer above a(n−1) such that
a(n) + a(i) + 1 is prime for all i < n; A119751 and A119752 let i run to n,
which adds 2·a(n) + 1. None carries a bound at its open index and none has
a b-file.

**Five entries ride on the finds**, because an affine map carries one
definition onto another (`clique_reference` G2d checks every published term
*and* the derived entry's own pairwise condition on the mapped set):

| derived entry | is | because |
|---|---|---|
| [A180565](https://oeis.org/A180565) | 2·A093483 + 1 | (b_i + b_j)/2 = a_i + a_j + 1 |
| [A115760](https://oeis.org/A115760) | 2·A103828 + 1 | the same (Sloane's own comment) |
| [A128933](https://oeis.org/A128933) | A103828 + 1 | by its name |
| [A120403](https://oeis.org/A120403) | A119752 + 1 | b_i + b_j − 1 = a_i + a_j + 1, 2b − 1 = 2a + 1 |
| [A113875](https://oeis.org/A113875) `hard` | 2·A119751 + 1 | the pairwise average, and the entries prime: that is the form 2x + 1 |

The last identity is in neither OEIS entry; it holds on all 14 published
terms. **So a find on A103828 settles three entries and a find on A093483,
A119752 or A119751 settles two.**

**Notation, and which number goes in the OEIS.** None of these names gives
the term a letter — they say "a(n)" — so that is what an evidence file
carries it under: the field `a(n)` is the term, `forms` is the entry's own
condition, and `oeis_terms` is literally what to submit, `{"18": v}` reading
"a(18) is v". A derived entry's integer (2v + 1, or v + 1) is in
`also_settles`. The code calls the sweep variable x, which *is* the term
(CONVENTIONS.md "Naming in an evidence file").

## The mathematics of the engine

**The form list is state.** At index n the conditions on x are

    forms(F, n) = [ extra(F) ... ,  x + a(1) + 1,  ...,  x + a(n−1) + 1 ]

— n − 1 shifts by the sequence's own earlier terms, plus the family's extra
form (2x + 1, or x). Every form is linear, so the sieve, the wheel and the
model are the ones this repository already has. But in every other ladder
here the filter is a function of n; here it is a function of *what has been
found*. Four consequences:

* **One opening per family.** The filter for a(n+1) needs a(n), so a
  campaign can be planned, priced and benchmarked at exactly one index — the
  open one. `score.py` has one campaign shape per family for that reason.
* **A find restarts the sweep just above itself.** The new index has a
  condition the old filter never tested, so whatever the old filter swept
  past the find claims nothing; the rest of that segment is re-swept under
  the rebuilt engine. (factorial-ladders carries its classified line across
  a promotion. Here that would be a coverage hole one segment wide, and
  `_promotion_drill` exists to stand in front of it.)
* **No riders.** a(n) > a(n−1) strictly, and the run of an x cannot pass the
  filter — the form that would decide index n + 1 is x + a(n) + 1, and a(n)
  is this x. A full run is n; one condition short is n − 1.
* **An error would propagate.** A wrong a(n) poisons every later term, so a
  find is never taken from the engine: the oracle re-derives it from the
  bare definition against the whole prefix before anything is written, the
  evidence file carries that prefix, and the oracle refuses to have a term
  changed once it holds it (`clique_reference.register`).

**The killed set.** A prime q kills x ≡ −b·a⁻¹ (mod q) for each form a·x + b
it does not divide the leading coefficient of, and nothing else. K(q,n) ⊆
K(q,n+1): a new term adds one form and removes none.

**Admissibility is checked, not proved.** In every other ladder here some
residue class provably survives every prime. Here nothing says the offsets
a(i) + 1 leave a class free modulo every q: if at some index they cover all
of ℤ/q, *no* x satisfies the conditions and the sequence is **finite** —
which would be a bigger result than a term. Only q ≤ (number of forms) can
be covered, so the check is finite; G2c runs it at every index that exists
and the launcher runs it at every promotion, and says so with a `[MILESTONE]`
rather than sweeping a line that holds nothing.

**Forcing is to a class, not to zero.** When q kills q − 1 residues exactly
one class survives, and it is generally not 0:

| family (at its open index) | forced class |
|---|---|
| A093483, A119752 | x ≡ 2 (mod 6) |
| A037100 | x ≡ 0 (mod 6) |
| A103828, A119751 | x ≡ 9 (mod 30) |
| A133761 | x ≡ 11 (mod 30) |

So where the other ladders sweep the multiples of a unit, this one sweeps a
class: the GPU engine runs t with **x = r + u·t**, the killed residues
carried through the map (t ≡ (k − r)·u⁻¹), and the host maps back. Because
r < u, the periods of x and of t share their boundaries, so the coverage
cursor is unchanged. The CPU engine marks the dense x line and knows nothing
of r or u, which is what makes the parity gate a check of the forcing as
well as of the sieve. u is derived per filter — it *grows* with the
sequence, the moment a new term fills a prime's last class but one — and a
unit with a prime that is not forced is refused, because a unit is a
coverage claim.

**The engine** is factorial-ladders' v3 — a three-level subset wheel planned
per filter, a segment of periods sieved at once against periodic bit
patterns, in-block and tail compaction rounds, the narrow (u64) or wide
(offset, period) survivor record chosen at runtime from the plan — with the
form list generalised from k!·x ± 1 to a·x + b and the unit generalised to a
class: two lines of the engine core and the kernel cache key. Candidates are
(x, off) pairs, so no machine word bounds the search. Since round 2 the
in-block rounds dispatch on the record as well: on the wide record a round
test is a bit of the window's own period-indexed pattern (no multiply,
1.08–1.10× at the live n = 22 filters), on the narrow record it is still a
Barrett step, because there the same change measured 0.90×
(OPTIMIZATION_LOG.md round 2).

**The plan is priced in clock, not in density.** A find is only known to be
the least once its segment closes, and here the rest of that segment is
thrown away (above), so the wheel and the window are chosen together to
minimise the *expected clock to a confirmed find*: the model's expected line
swept until the segment holding a(n) closes, times the measured device
seconds per unit of line at that wheel, window width and window depth
(`clique_gpu.plan`). A longer wheel is fewer candidates and a longer
segment; a wider window is a faster kernel and a longer segment; the plan
is whichever the model and the measurements say lands the term soonest, and
it was checked against its neighbours, paired, at every filter measured
(OPTIMIZATION_LOG.md round 1: 1.66× on the clock at the first filter that
costs hours). The sieve is planned deep enough that one host worker keeps
up. The parity gate (G9)
pins GPU against CPU bit for bit on 28 populated windows: every family, both
extra forms, x space and class space (mod 6 and mod 30), one- to three-level
and subset wheels, above 2^64, and hard against the ceiling.

**The ceiling is 1e40, by measurement — this project is rule 5h's
exception.** The values are x + a(i) + 1, 2x + 1 and x: V − 1 has no
structure, and nothing about x factors it. What saves it is size. The
deterministic Miller–Rabin bound puts the proof crossing at x ≈ 1.66e24
(where 2x + 1 is a form) and 3.3e24 (elsewhere) — *above* every term the
campaign can reach in weeks, so for nearly the whole hunt the classification
is the proof. Past it each value is proved on its own by
`huntlib.certificate.prove` (V − 1 or V + 1 factored by bounded rho and ECM,
a subproof for any factor past the bound), and whether that works at a
height is an empirical question: `huntlib.ceiling.subproof_rate` proved 12 of
12 random primes at every height from 1e25 to 1e40 in under half a second
each, G10 re-measures it on every battery, and the certificate drill repeats
it on this project's own values at the ceiling (24 of 24, with the recursion
exercised). A value that cannot be proved is *reported* in the evidence
file's `unproved` list, never hidden.

## The odds model

Bateman–Horn over the forms of an index, with the singular series computed
from the same killed sets the sieve is built from.

**Validation (G11), stated before the run.** E — the expected number of hits
between a(n−1) and the a(n) that actually occurred, given the real prefix —
must scatter around 1. Over the **49** published terms from n = 9 (there are
no riders: every term is a searched draw) the mean is **1.03**, spread
0.04–5.41: A093483 0.73 over 9, A103828 1.49 over 10, A037100 0.44 over 10,
A119752 1.05 over 6, A119751 0.98 over 6, A133761 1.53 over 8.

**The model sees exactly one term ahead.** The series of the index after the
open one depends on a term nobody has. The first row per family below is the
model's real answer; every later row replaces each unknown term by a
*stand-in* — the first x past the previous median that survives every prime
under 2000 — and is a **projection**, labelled so everywhere it appears
(`model_results.json`). Read all of it as a floor: this repository's first
occurrences have landed at 1.2–2.5× their medians while every census showed
the intensity right.

| family | open term | median | P90 | then, projected medians |
|---|---|---|---|---|
| A093483 | a(18) | **4.7e16** | 3.9e17 | 2.3e18, 4.5e19, 1.1e21, 3.7e22, 1.0e24 |
| A103828 | a(19) | **7.7e18** | 2.8e19 | 8.9e19, 2.1e21, 5.8e22, 1.8e24 |
| A037100 | a(19) | **7.1e17** | 5.0e18 | 2.3e19, 6.4e20, 1.9e22, 6.0e23 |
| A119752 | a(15) | **4.4e13** | 2.8e14 | ~7e16, 1.7e17, 8.9e17, 1.3e19, 3.4e20 |
| A119751 | a(15) | **8.4e13** | 5.9e14 | 4.0e15, 6.0e16, 1.0e18, 2.3e19, 6.5e20 |
| A133761 | a(17) | **1.1e17** | 7.9e17 | 3.5e18, 8.9e19, 2.2e21, 5.9e22, 1.9e24 |

Each term costs about 1.5 decades more than the last. At the frozen rates
(BENCHMARKS.md) every *open* term is seconds of device; the projections put
everything up to about 1e21 inside an hour per family and the term near
1e22–1e23 at a day or so — four to seven terms per entry, about thirty
hunted terms and twenty riding on them.

**A caveat on what the early terms are worth.** A119751 and A119752 stood at
4.6e12 because nobody returned to them after 2008, not because a(15) was
hard: Don Reble took the sibling A103828 to 2.5e18 on a CPU in 2021. The
hunt proper is the last two or three terms of each entry.

**How it came out.** The six real (first-row) medians against the terms
that landed, x / median: A093483 0.43, A103828 1.21, A037100 0.76, A119752
0.35, A119751 1.97, A133761 0.23 — all inside P90. The projections held too:
every family reached the 1e20–1e22 band inside six hours of campaign time
(`--status` elapsed: 0.27 h for A037100 to 5.31 h for A119751, whose a(20)
at 5.6e21 was the slowest). The open terms now sit at the
~1e22–1e24 rows the table calls a day or more, and those rows are still
projections over stand-ins: rerun `clique_model` on the real prefix before
pricing the next session.

## Running it

```bash
python launch.py --selftest     # the full battery -- must end ALL GREEN (~3.5 min)
python score.py                 # gates x nine fingerprinted benchmarks (~4 min)
python launch.py --status       # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py                        # A093483, indefinite, resumable
python launch.py --family A119752       # any of the six; a derived entry's
python launch.py --family A113875       #   A-number opens its base family
python launch.py --to 1e20              # stop at a chosen depth in x
python launch.py --stop-on-discovery    # stop when THIS RUN finds something
```

One campaign per family, each with its own checkpoint and ledger. Runs
indefinitely by default, to the 1e40 ceiling. Requires CuPy and a CUDA GPU;
sympy and numpy for the oracle and the CPU engine.

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md). Specific to this project:

* **The definition is regenerated, not quoted.** G1 checks that every
  published list is a clique under the bare definition and rebuilds each
  greedily from its first term as far as brute force reaches (8–11 terms) —
  which pins each family's start and extra form. G5 has the CPU engine
  re-derive 21 published terms as first occurrences above their predecessors,
  and the canary has the GPU stream do the same for eight more, in x space
  and in class space.
* **The real loop is run, on published ground.** `_rediscovery_run_drill`
  opens `Campaign.run` below the published frontier on scratch files and
  requires it to find a(13), promote itself, and find a(14) *under the
  condition a(13) created*, with both evidence files complete. It can find
  nothing new; it is the only gate that exercises the sequential dependence
  end to end.
* **A drill may not fabricate a find.** A term becomes part of every later
  index's definition and the oracle keeps it, so drill campaigns open below
  the published frontier and "find" real published terms (`DRILL_N`).
* **An earlier term is not a later one.** In the 2x + 1 families an earlier
  term satisfies *every* condition of a later index — a clique is a clique
  in any order, and 2a + 1 is its own extra form — so what rejects it is the
  ordering alone. The protocol drill checks exactly that.
