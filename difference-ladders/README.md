# difference-ladders — A216666, A216668 and A229073

> **Authorship disclaimer:** None of this code was written by me — it was
> entirely authored by **Claude (Anthropic's AI)** at my direction.

**Independent mathematical review:** Not yet reviewed. Codex (OpenAI)
writes static analyses for this repository under the
[review workflow](../CODEX_REVIEWS.md); this project's index is
[codex-reviews/](codex-reviews/README.md).

A GPU hunt for the next terms of three related entries of Jean-Louis
Charton and Eric M. Schmidt, the **difference ladders**: one unknown, and a
ladder of conditions on the difference of two consecutive p-th powers.
[A216666](https://oeis.org/A216666) asks for the smallest integer b such
that (b+1)^p − b^p is prime for all primes p ≤ prime(n);
[A216668](https://oeis.org/A216668) for the smallest integer b > 1 such that
for all primes p ≤ prime(n), (b+1)^p − b^p is prime if and only if 2^p − 1 is
prime; [A229073](https://oeis.org/A229073) for the least m ≥ 2 such that
m^p − (m − 1)^p is composite for p = prime(n) but no smaller prime p.
Charton's tables stopped in October 2012 at a(8) and a(11), Schmidt's in
September 2013 at a(7), and Tyler Busby's "a(9) > 10^11" (Feb 2023) is the
only line added to any of them since. **Standing result
([RESULTS.md](RESULTS.md)): eighteen new terms over the three entries** —
a(9) = 8,631,333,707,125,241 and a(10) = 4,706,913,956,767,150,128 of
A216666; a(12) through a(17) of A216668, all equal to its a(11) =
288,975,248,496, and a(18) through a(23), all 28,883,337,280,604,081; and
a(8) = 30,717,523,795, a(9) = 55,779,743,836, a(10) =
8,631,333,707,125,242 and a(11) = 4,706,913,956,767,150,129 of A229073.
Eight were read off the runs at published terms without a sweep; ten were
found by the campaigns. Each is verified three ways and re-verified from
disk by an independent sympy harness, with every value either proved by
BLS75 or a strong probable prime awaiting a general prover (RESULTS.md says
which).

**Status: PAUSED — open to others** — nothing is running. Built and gated
2026-11-23 (62/62 selftest rows, every score.py fingerprint reproduced;
engine v2, 1.33x to 1.69x over v1 at the campaign filters). The owner's two
campaigns ran on 2026-11-24 (UTC), 14.64 hours on A216666's clock and 2.78
on A216668's, at their benchmark rates, and found the ten campaign terms
above: A216666's a(9) (about 4 minutes in) and a(10) (9.6 hours), with
A229073's a(10) and a(11) riding, and A216668's a(18) (50 minutes), whose
run of exactly 23 settled a(19) to a(23) with it. Each campaign was stopped
inside the search for its next term: A216666 is searched empty to b =
5.0307×10^18 with a(11) open (median about six months at the measured
rate), A216668 to b = 2.9029×10^16 with a(24) open (median about two
weeks). See the clock table below and RESULTS.md "What is open now".

## The problem

| entry | name (%N), verbatim | published | frontier | last moved |
|---|---|---|---|---|
| [A216666](https://oeis.org/A216666) `hard,more` | Smallest integer b such that (b+1)^p - b^p is prime for all primes p <= prime(n). | a(1)–a(8) | a(8) = 55,779,743,835; "a(9) > 10^11" | Jean-Louis Charton, Oct 2012; Tyler Busby, Feb 2023 |
| [A216668](https://oeis.org/A216668) `hard,more` | Smallest integer b > 1 such that for all primes p <= prime(n), (b+1)^p - b^p is prime if and only if 2^p-1 is prime. | a(1)–a(11) | a(11) = 288,975,248,496 | Jean-Louis Charton, Oct 2012 |
| [A229073](https://oeis.org/A229073) `hard` | Least m >= 2 such that m^p - (m - 1)^p is composite for p = prime(n) but no smaller prime p. | a(1)–a(7) | a(7) = 809,652,229; "no other terms <= 10^9" | Eric M. Schmidt, Sep 2013 |

That table is the frontier this project started from (the OEIS export of
2026-11-23, re-read on oeis.org the same day). A216666's terms are 1, 1, 1,
1, 6524, 809652228, 30717523794, 55779743835; A216668's are 2, 2, 2, 296,
296, 369719, 457578, 43410300320 (three times), 288975248496; A229073's are
5, 6, 4, 3, 2, 6525, 809652229.

**Both b-ladders nest.** Every condition of index n is one of index n + 1,
so a(n+1) ≥ a(n), the sweep for a(n) starts AT a(n − 1) inclusive, and a
term whose run passes its index is the next term too — A216666's a(1) =
a(2) = a(3) = a(4) = 1 (2^p − 1 is prime for p = 2, 3, 5, 7 and
2^11 − 1 = 23 · 89), and A216668's a(8) = a(9) = a(10).

**A229073 is A216666's line read exactly.** Its a(n) is the least m whose
m − 1 has an A216666 run of exactly n − 1: the conditions at the first
n − 1 primes hold and the one at prime(n) fails. So an A216666 term whose
run is exactly its index n gives A229073 a(n + 1) = that term plus one
(Schmidt's own a(6) = 6525 and a(7) = 809,652,229 are A216666's a(5) and
a(6) plus one), and this project's two free terms are its a(7) and a(8)
plus one. When an A216666 find's run passes its index, A229073's terms
below it still need exact runs further up the line — the launcher holds the
filter down until they appear (below).

**A216668 asks for composites too.** Its conditions are prime at the
Mersenne exponents 2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127 and
COMPOSITE at every other prime. The run at its a(11) is exactly 17:
(b+1)^p − b^p is composite at p = 37, 41, 43, 47, 53 and 59, as 2^p − 1 is,
and composite at p = 61, where 2^61 − 1 is prime — so a(12) through a(17)
are a(11), and a(18) needs a b whose value at p = 61 is prime. The
next Mersenne exponent is 89, so a(19) to a(23) ask only for composites at
p = 67, 71, 73, 79 and 83 and will be a(18) with probability about 98.5%
(the single-form Bateman–Horn chance that one of the five values is prime is
under 0.4% each) — and were: a(18) = 28,883,337,280,604,081 runs to exactly
23. a(24) adds p = 89.

**Which number goes in the OEIS.** A216666 and A216668 name the term b, and
their evidence files carry the integer under `b`; A229073 names it m, and
its records carry m (with A216666's b = m − 1 beside it). Every record's
`oeis_terms` is literally what to submit: `{"12": 288975248496, ...,
"17": 288975248496}` reads "a(12) through a(17) are this integer".

## The mathematics of the engine

**The killed set.** For a prime q and a prime p, q divides (b+1)^p − b^p
exactly when (b+1)^p ≡ b^p (mod q), that is — b = 0 gives 1, and (b+1)/b is
never 1 — when (b+1)/b is a primitive p-th root of unity ζ mod q, which is
to say b ≡ 1/(ζ − 1) (mod q). Such roots exist exactly when p divides
q − 1, and then there are p − 1 of them. So a prime q kills p − 1 residues of
b for each sieved p dividing q − 1 and none for any other p; q = p never
kills ((b+1)^p − b^p ≡ 1 mod p), nor does q = 2 (the value is always odd).
The residues 0 and q − 1 always survive, so **nothing is ever forced**: no
prime pins b to one class, the engines sweep the whole line, and no prime
covers every residue (every index is conjecturally attained). This is
exactly cyclotomic-ladders' killed set — the residues of multiplicative
order p — carried through the change of variable that sets that project's
unknown (x, in A070737's own letters) to (b+1)/b, so its engine is this
one's. The oracle builds the set by walking
every residue and by sympy's roots of unity, the CPU engine from a primitive
root, and gates G2b and G3 pin the constructions to each other and to
direct divisibility.

**A weak wheel.** A prime kills one residue per sieved form on average
(p divides q − 1 for one prime q in p − 1), and nothing is forced, so the
primes to 59 keep 0.75% of the line at A216666's n = 9, 0.39% at n = 10
and 11, and 2.6% at A216668's n = 18 to 24 — the weakest wheel in this
repository. The window sieve and the tail rounds therefore carry far more
of the work than in the ladders before it, and the device Fermat stage
sees many survivors.

**The engine** is cyclotomic-ladders' engine v2 (power-ladders' window
sieve with the device Fermat stage), taken whole: a wheel planned per filter
as a subset of the primes to 89 in up to three CRT levels (2, which kills
nothing, is always declined), the strongest sieve primes tested 256 periods
at a time through bit-pattern windows, in-block compaction rounds,
generated tail rounds, and the device Fermat stage, which Fermat-tests the
first five values of every sieve survivor — (b+1)^2 − b^2 = 2b + 1,
(b+1)^3 − b^3 and on, cheapest first — so only a few thousand values a
second reach the host. What is this project's: the kill sets above; the
Fermat stage's arithmetic, which forms (b+1)^p − b^p as two powers by
repeated multiplication truncated to the value's limbs and takes their
difference modulo 2^(32·limbs) — exact, because truncation is a ring map
and the difference fits — at 2 to 65 limbs (G23 pins it to Python's pow at
every limb count, the ceiling's included); a residue list of 256 slots in
the tail (A216668's n = 24 can kill 237 residues a prime); and the
classification of A216668's composite conditions on the host, which reads
the prime-asking values first and the composite-asking ones only for the
rare value that passes them all. The engine is gated against an
independent CPU engine (plain `%` over a dense line, no wheel) on 23
populated windows to the 1e40 ceiling (G9), and against the sympy-only
oracle.

**Engine v2: which primes the sieve tests.** A sieve prime's test costs the
same whatever it kills, and what a kill saves is the Fermat work the b
would otherwise cost — which depends on the form it kills through: the
stage tests 2b + 1 first and cheapest, so a kill through 2b + 1 saves
little, while a kill through a form the stage never tests saves the whole
stage. Every odd prime kills one residue of 2b + 1, and about a fifth of the
primes kill nothing else; a prime q with q − 1 divisible by many of the
sieved p kills dozens. So the campaigns sieve the primes to 32768 whose
kills, each weighted by its form's place in the stage, are worth a test
(`difference_search.select_primes`, read by both engines), not every prime
to a depth: the primes past ~300 that kill only 2b + 1's residue drop out
and primes to 32768 with a smooth q − 1 come in. A prime past 8192 is tested
in the tail through an exact perfect-hash table of its killed residues (a
few hundred bytes) rather than a bit pattern of 2q bits, which is what had
made a deeper sieve a loss. The Fermat stage runs on its own CUDA stream
beside the next launch's sieve, its squarings by a squaring. Measured paired
against v1 at the campaign filters: 1.33x at A216666 n = 9 and 10, 1.42x at
n = 11, 1.69x at A216668 n = 18 and 1.51x at n = 24 (OPTIMIZATION_LOG.md
round 1, which also prices what was declined).

**The filter, and A229073 riding.** A216666's campaign sieves the forms of
its open index n = frontier + 1 — unless A229073 has an open index whose
exact run is lower, in which case the filter is held there: every b whose
run is at least the filter is in the stream, so the first b of each exact
run is seen. A find at filter n settles A216666 from a(n) up to the index
its run reaches, and A229073 at the index one past its run, at once; the
filter climbs only when nothing below it is
open (drilled end to end on published ground: from b = 1, which runs to 4,
the filter is held at 3 until b = 2's exact run of 3 gives A229073's
a(4) = 3).

**The ceiling and the proofs.** The term is bounded by huntlib's
K_CEIL = 10⁴⁰. (b+1)^p − b^p − 1 factors over the integers as
p · b · (b+1) · (b² + b + 1)^e · E(b), with e = 2 when p ≡ 1 (mod 6) and
E of degree p − 3 − 2e (sympy's factor_list, multiplied back in the
certificate drill for every p to 89). With b, b + 1 and b² + b + 1 factored
completely, the factored part of N − 1 = (b+1)^p − b^p − 1 is all of it at
p ≤ 7, over half at p = 13 (BLS75 Theorem 1), and over a third at p = 11 and
19 (Theorem 5) — measured at b = 3·10^19 and 3·10^21: every such value
proved in 2–4 seconds, prime factors of b² + b + 1 past 3.3·10^24 carried
as subproofs. At p = 17 it is a quarter, and from p = 23 on under a fifth:
**those values have no N − 1 route at any height**, and a discovery leaves
them UNPROVED in its evidence — strong probable primes to thirteen bases
and BPSW, proved later by a general prover (APR-CL or ECPP). Neither is
installed on this machine (python-flint and PARI/gp are absent); which to
install is the owner's decision. OPTIMIZATION_LOG.md has the measured
BLS75 table and what is known of the general provers' cost.

## The odds model

Bateman–Horn over the conditions of an index, with the singular series
computed from the sieve's own killed sets (difference_model.py): each
prime-asking condition contributes 1/ln((b+1)^p − b^p), about
1/((p − 1) ln b), and each of A216668's composite-asking conditions a
factor of one less that value's single-form chance of being prime.
**Validation (G11)** at the nine published terms searched above 100
(A216666's a(5)–a(8), A216668's a(4), a(6), a(7), a(8), a(11)): E sums to
13.3 against a Gamma(9, 1) law (P = 0.91, inside both tails); per family
mean E 1.89 (0.97, 5.36, 1.21, 0.01) and 1.14 (1.99, 1.51, 0.01, 2.14,
0.07) — the terms have come late more often than early, and A216666's
a(6) very late. Predictions, stated before any run (model_results.json;
each index searched from the model's median of the one before, a(9) and
a(18) from the frontier term):

| term | from b = | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|
| A216666 a(9) | 5.58×10¹⁰ | 1.11×10¹⁵ | 3.67×10¹⁵ | 9.30×10¹⁵ | 1.83×10¹⁶ |
| A216666 a(10) | 3.67×10¹⁵ | 1.59×10¹⁸ | 5.04×10¹⁸ | 1.24×10¹⁹ | 2.40×10¹⁹ |
| A216666 a(11) | 5.04×10¹⁸ | 1.03×10²¹ | 3.19×10²¹ | 7.77×10²¹ | 1.49×10²² |
| A216666 a(12) | 3.19×10²¹ | 1.28×10²⁴ | 3.91×10²⁴ | 9.42×10²⁴ | 1.79×10²⁵ |
| A216668 a(18) | 2.89×10¹¹ | 2.03×10¹⁵ | 6.61×10¹⁵ | 1.67×10¹⁶ | 3.26×10¹⁶ |
| A216668 a(24) | 6.61×10¹⁵ | 9.08×10¹⁸ | 2.84×10¹⁹ | 6.93×10¹⁹ | 1.33×10²⁰ |

A229073's open terms ride: its a(10) is A216666's a(9) plus one unless
a(9)'s run passes 9 (the value at p = 29 prime: about 0.5% at the median),
and so on up (0.7% at a(10), 0.4% at a(11)).

**The clock at the measured rates** (engine v2; BENCHMARKS.md: 4.75·10¹³
b/s at A216666 n = 9, 1.44·10¹⁴ at n = 10, 1.99·10¹⁴ at n = 11; 1.07·10¹³
at A216668 n = 18, 2.39·10¹³ at n = 24 — about 4·10¹¹ to 1.0·10¹²
candidates a second):

| term | Q1 | median | Q3 | P90 |
|---|---|---|---|---|
| A216666 a(9) | 23 s | 77 s | 3 min | 6 min |
| A216666 a(10) | 3.1 h | 9.7 h | 24 h | 1.9 days |
| A216666 a(11) | 60 days | 6.1 months | 15 months | 2.4 years |
| A216668 a(18) | 3 min | 10 min | 26 min | 51 min |
| A216668 a(24) | 4 days | 14 days | 34 days | 64 days |

A216666's a(12) is out of reach. The survey that chose this cluster priced
these clocks at 5·10¹² candidates a second, the rate cyclotomic-ladders and
primorial-ladders measured; this project's weak wheel runs at a fifth to a
twelfth of that (its sieve keeps 0.5–2.6% of the line, so the window, the
tail and the Fermat stage all carry far more than on a forced wheel;
OPTIMIZATION_LOG.md), so its clocks are still several times the survey's:
a(10) 10 hours rather than 1.1, a(11) six months rather than 29 days,
A216668's a(24) two weeks rather than 39 hours (engine v1: 14 hours, nine
months, three weeks). The model has run early and late elsewhere in this
repository (mean E 0.5 to 1.9): read the quantile table, not the median.

**The finds against the model** (RESULTS.md): A216666's a(9) came at the
model's P = 0.73 (E 1.31), its a(10) at P = 0.48 (E 0.66), and A216668's
a(18) at P = 0.88 (E 2.10) — mean E 1.36, a little late, as the published
terms were, and not significantly (with G11's nine, an upper tail of 0.07).
The campaigns ran at their benchmark rates (0.91 to 1.06 at each filter).
From the paused cursors the open terms stand at: A216666's a(11) 60 days /
6.1 months / 15 months / 2.4 years, and A216668's a(24) 4.4 / 14 / 34 / 64
days (Q1 / median / Q3 / P90).

## Running it

Requirements: an NVIDIA GPU with CuPy (developed on an RTX 4090, CUDA 13,
CuPy 14), Python 3.12+, numpy, sympy; gmpy2 recommended (the host's base-2
tests are eight times faster with it at 1,700 digits, and the pool is sized
from what it measures).

```
python launch.py                       # the hunt: A216666 with A229073 riding, indefinite, resumable
python launch.py --family A216668      # A216668
python launch.py --status [--family F] # where the cursor is; reads, never writes
python launch.py --selftest            # the full gate battery (about 3 minutes warm)
python score.py                        # gates x fingerprinted benchmark (about 2.5 minutes)
```

`--family A229073` runs A216666's campaign and says so. One campaign runs
at a time; each family has one checkpoint, and each sequence its own ledger
in `evidence/`. Throttles, each priced in `--help`: `--workers`,
`--gpu-yield-ms`, `--gentle`. **The first battery after a kernel change
compiles every configuration once** (NVRTC; the Fermat stage's 65-limb
kernels among them) and runs several minutes longer than a warm one. The
acceptance test of CLAUDE.md 5g — each family started fresh with no flags,
its first `[STATUS]` lines read for the pool, the rate and the rung — is the
owner's to run, being a campaign start; both families were started that way
on 2026-11-24 and ran at their benchmark rates at every filter they reached
(RESULTS.md).

## Trust

The repository's machinery is described in [CONVENTIONS.md](../CONVENTIONS.md):
an oracle that uses nothing but sympy and the definitions; an independent
CPU engine; a GPU engine pinned to it bit for bit on populated windows to
the ceiling; canaries (A216666's a(6), a(7), a(8) and A216668's a(7), a(8)
rediscovered by the GPU stream from their floors) and two end-to-end
rediscovery runs of the real campaign loop on published ground; three
independent confirmations and a witness for every recorded run; frozen
benchmark fingerprints. Specific to this project:

* **Two kinds of stopper.** A run of A216666 ends at a composite value (its
  witness is a prime factor, or — when none is found under 2^17 or by the
  bounded rho and ECM search — the failed base-2 Fermat test, which anyone
  can rerun); a run of A216668 can also end at a PRIME value where a
  composite was asked, and then its witness is that value's primality.
* **Composite conditions are witnessed one by one**: every A216668 record
  lists, for each non-Mersenne exponent of its run, a prime factor under
  2^17 or the failed Fermat test.
* **Unproved values are named.** A value with no BLS75 route is listed under
  `unproved` in its record; the free terms' unproved values are exactly the
  values the published a(11) of A216668 and a(7), a(8) of A216666 already
  rest on, while the campaign terms' are new — p = 17 and 23 at A216666's
  a(9), p = 17, 23 and 29 at its a(10), p = 17, 31 and 61 at A216668's
  a(18), strong probable primes to thirteen bases and BPSW (RESULTS.md).
* **The census floor is 6 conditions**, and the device tests five forms:
  every value whose run reaches the floor passes the device stage, so the
  census is complete from the floor up.
* **The sieve set is a choice, and both engines make the same one.** Which
  primes are sieved changes only which b reach the Fermat stage — a kill is
  a proof of compositeness whatever the set, and every run is read by the
  host's classification — so the campaigns' value-selected set is gated the
  way the full set is: the GPU stream, hashed tail primes included, == the
  CPU engine sieving the same set on populated windows, and every hashed
  prime of both day-long engines is emulated over every remainder it can
  meet (G24).
