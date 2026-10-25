# cyclotomic-ladders — A070737, A072942 and A233512

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

**Independent mathematical review:** Codex (OpenAI) maintains static
analysis and implementation proposals in [codex-reviews/](codex-reviews/README.md).
These reports follow the repository's [review workflow](../CODEX_REVIEWS.md);
Claude's original implementation and historical records retain their authorship.
The [2026-10-23 static review](codex-reviews/2026-10-23-static-review.md)
and [Claude validation plan](codex-reviews/2026-10-23-validation-plan.md)
are complete; proposals and their implementation status are tracked in the
[review ledger](codex-reviews/README.md), which round 1 of
OPTIMIZATION_LOG.md updated (the baseline frozen, experiment D shipped,
the launcher's rider, cap and index-scope fixes made, the rest priced).

A GPU hunt for the next terms of two **cyclotomic ladders** — one unknown
x and a set of conditions that differ in which cyclotomic polynomial is
evaluated at it. **A070737** asks for the smallest number x such that the
first n cyclotomic polynomials evaluated at x are primes; **A072942** for
the least x such that the cyclotomic polynomial values Phi(d,x) are prime
for all d dividing n; **A233512** is A070737 restated with the arguments
strictly increasing and coincides with it from n = 5 (G1d), so every
A070737 find settles it too. Don Reble and Phil Carmody published
A070737's ten terms in 2002 and nothing had moved since; Carmody's A072942
(2002), corrected and extended by Reble in 2014 to n = 39 in the data and
n = 99 in an a-file, had ten open indices below 100 — 48, 60, 66, 72, 78,
80, 84, 88, 90, 96 — the question marks of that a-file. **Standing result
([RESULTS.md](RESULTS.md)): a(11) and a(12) of A070737 — and so a(11) and
a(12) of A233512 — and a(48), a(60), a(66), a(78), a(80) and a(88) of
A072942, found and verified 2026-10-23 to 10-25**, every value certified
except nine at a(66), a(78) and a(88), which were proved prime by APR-CL on
2026-10-25 and carry no certificate in the evidence (RESULTS.md).

**Status: PAUSED — open to others** — built and optimized 2026-10-23/24,
hunted by the owner 2026-10-23 to 10-25, paused 2026-10-25 with eight
terms found (above; RESULTS.md). A070737 is paused at x = 1.86×10²² inside
the filter for a(13), whose model median is 1.7×10²⁵ — about 10 days at
the measured rate (Q1 3 days, P90 7 weeks). A072942's campaign closed six
of its ten open indices and was stopped nine minutes into n = 72, before
its first segment closed, so a(72) restarts from x = 3 (median 2.2 days),
with a(84), a(96) and a(90) unstarted (7, 10 and 11 days). The engine is
power-ladders' window sieve with its device Fermat stage, re-shaped for
this project's large window primes (engine v2, planner p2:
OPTIMIZATION_LOG.md round 1 — 1.31x at the day-long filters of both
families over the engine as inherited, 1.25–1.8x at the openings, with
every constant measured on these filters and the benchmark shapes frozen).
Planner p3 (round 2, 2026-10-24) adds the MEASURED wheels of A072942's
n = 60, 72, 84 and 96 — Codex's CYL-011 exchanges of a weak small wheel
prime for a strong one above the planner's 89 — at 1.04–1.10x the planned
wheels, paired at x = 3 and at the model's median, with the coverage
segment at 84 and 96 five times shorter and at 60 half; at n = 90 every
exchange measured 0.97–1.00 and was declined. The live n = 60 cursor was
adopted onto the new wheel at the owner's restart and a(60) was found under
it. The campaigns ran at their prices (RESULTS.md); the pause battery of
2026-10-25 is in BENCHMARKS.md (30 gates and the 57/57 selftest green,
every fingerprint reproduced, on the code as committed). Whoever resumes
runs `python launch.py --selftest` and `python score.py` first (CLAUDE.md
rule 2).

## The problem

| entry | name (%N), verbatim | published | frontier | last moved |
|---|---|---|---|---|
| [A070737](https://oeis.org/A070737) | Smallest number x such that the first n cyclotomic polynomials evaluated at x are primes. | a(1)–a(10) | a(10) = 13,533,264,289,711,320 | Don Reble and Phil Carmody, 2002 |
| [A072942](https://oeis.org/A072942) | a(n) is the least x such that the cyclotomic polynomial values Phi(d,x) are prime for all d dividing n. | a(1)–a(39) in the data; the a-file to a(99) with ten question marks | a(48), a(60), a(66), a(72), a(78), a(80), a(84), a(88), a(90), a(96) open | Don Reble, Feb 2014 |
| [A233512](https://oeis.org/A233512) `hard,more` | The first n cyclotomic polynomials are simultaneously prime for these arguments. | a(1)–a(6) | a(6) = 6,770,610; "a(7) > 2*10^9" | T. D. Noe, Dec 2013 |

That table is the frontier this project started from. It moved on
2026-10-23 to 10-25 (RESULTS.md): A070737 and A233512 now stand at a(12),
and A072942's open indices below 100 are 72, 84, 90 and 96.

A070737's a(1) to a(10) are 3, 4, 6, 6, 1068630, 6770610, 2981997480,
339126523890, 120351747887280, 13533264289711320. **The ladder nests**:
every condition of index n is one of index n + 1, so a(n+1) ≥ a(n), the
sweep for a(n+1) starts AT a(n) inclusive, and a(3) = a(4) = 6 (Φ₁ to Φ₄
are prime at 6, Φ₅(6) = 1555 = 5·311). A233512 lists 3, 4, 6, 150, 1068630,
6770610: its a(4) = 150 is the least x > 6 with the first four values
prime, so it is the strictly increasing variant, identical to A070737 from
n = 5 on — and its a(7) to a(10) are A070737's published terms (G1d). Its
comment "a(7) > 2·10⁹" is consistent with a(7) = 2,981,997,480.

A072942's indices are **separate problems**: a(n) is the least x with
Phi(d,x) prime for every divisor d of n (equivalently, x^n − 1 has only
its algebraic factors), and a(n) says nothing about a(n+1). Each open
index is its own line from x = 3 (Phi(1,2) = 1 is not prime, so 2 never
appears — the entry's own comment). The a-file's known entries up to 99
are in cyclotomic_reference.FAMILIES and were re-verified on 2026-10-23;
a(36) = 24,380,304,369,772,260, a(70) = 2,355,476,281,187,040 and
a(56) = 257,943,509,313,180 are the largest.

**Which number goes in the OEIS.** Both names give the term the letter
**x**. An evidence file carries the integer under `x`, `forms` reads
"Phi_k(x), k = 1..n" (A070737) or "Phi(d,x), d | n" (A072942), and
`oeis_terms` is literally what to submit — `{"11": <integer>}` reads
"a(11) is this integer". An A070737 record's `also_settles` lists the same
integer for A233512 at the same index, under x: that entry's name gives
the term no letter, and its comment and example lines call it x.

## The mathematics of the engine

**The killed set.** For a prime q not dividing x, q divides Φ_k(x) exactly
when the multiplicative order of x modulo q is k with its q-part stripped;
and Φ_k(0) = 1 for k ≥ 2 (Φ₁(0) = −1), so the residue 0 is never killed.
The kill set of q at a filter is therefore the set of residues whose order
is one the filter's cyclotomic indices ask for — φ(m) residues for each
attainable order m dividing q − 1. The CPU engine builds it as powers of a
primitive root; the oracle walks every residue and evaluates the
polynomials, and builds the roots of unity by sympy's nthroot_mod; G3
checks both against direct divisibility and against a vectorised
evaluation on primes to 2²⁰. Three consequences shape everything:

* **A prime kills about one residue per form on average, but up to q − 1
  where q − 1 is smooth**: 97 kills every nonzero residue at A072942's
  n = 96, 61 at n = 60. The proved bound is the sum of φ(k) over the forms
  — 128 at A070737's n = 20 exactly, which is the last filter the GPU
  tail's residue list can hold; n itself on A072942.
* **The forced classes have a formula.** A prime q is forced — x ≡ 0 (mod
  q) — exactly when every order dividing q − 1 is asked for, which on
  A070737 is every prime q ≤ n + 1 (2, 3, 5, 7, 11 from n = 10; 13 from
  n = 12; 17 from n = 16) and on A072942 every prime q with (q − 1) | n
  (2, 3, 5, 7, 11, 13, 31, 61 at n = 60: a unit of 56,786,730; 97 joins at
  n = 96). G2c proves it against the walk at every filter; the campaigns
  run in these classes, with units far past any earlier project's.
* **The wheel is of middle strength**: the primes to 59 keep 1.3×10⁻⁶ of
  the line at A070737 n = 11 and 1.6×10⁻⁷ at n = 13, 1.9×10⁻⁹ at A072942
  n = 60 — between the power ladders' 10⁻³ to 10⁻⁵ and the polynomial
  runs' 10⁻⁸.

**The engine** is power-ladders' (polynomial-runs' window sieve: wheel to
89 in up to three levels; the strongest sieve primes — 62 to 90 of them
here, where the survival target or a 12 KB budget on their bit-pattern
tables stops the window — tested 160–256 periods at a time through those
windows; in-block compaction rounds; generated tail rounds, the last one
included; and the device Fermat stage, which Fermat-tests the leading six
values of every sieve survivor on the device, cheapest degree first, so
that only a few thousand values a second reach the host). The kernel
never sees a form, only the residues each prime kills, so what is this
project's is the kill set above and the Fermat stage's arithmetic: each
value is formed by Horner from the cyclotomic coefficients (−1, 0 or 1 for
every index below 105), a multiply by x and an add or subtract of one per
coefficient, in multi-limb Montgomery arithmetic compiled per limb count.
One engine rule is this project's too (OPTIMIZATION_LOG.md round 1): the
strongest killers here are LARGE primes (q with a smooth q − 1 kills many
residues: to 1,300 at A070737 n = 13, to 6,000 at the A072942 openings),
so the window's bit-pattern tables hold ONE period of each prime's pattern
and the kernel reduces its position with one unsigned min, which is what
lets the pairs layout, the packed residues and the per-launch offset
table fit at every filter (96 registers and 4 blocks per SM at A070737
n = 13 where the inherited layout ran at 168 and 3). Every constant was
re-measured at the day-long filters (round 1).

**Two shapes of campaign.** On A070737 a find promotes the filter and
carries the classified line (the classification reads runs six forms past
the filter). On A072942 a find closes the index — there is nothing more to
sweep for — and the campaign moves to the next open index in TARGETS,
cyclotomic_reference's frozen order of the model's expected clock,
cheapest first: 66, 78, 88, 48, 80, 60, 72, 84, 96, 90 (G12 checks the
model still ranks them so). Each index has its own checkpoint.

**The ceiling and the proofs.** The term is bounded by huntlib's
K_CEIL = 10⁴⁰. Φ_k(x) − 1 factors over the integers as x^a times
cyclotomic polynomials of smaller index at x times a leftover of degree 0,
3, 5 or 6; for every k to 14, for 16 to 20, 24, 40, 48, 72 and 96 the
leftover is 1 and the smaller indices are earlier forms of the same run,
so N − 1 is completely factored by one factorization of x plus the run's
own proved values, whose certificates ride along as subproofs (BLS75
Theorem 1); for k = 15, 30, 60, 80, 84 and 90 the factored part still
passes the cube root (Theorem 5). A072942's n = 66, 78 and 88 need a
65–70-digit cyclotomic value outside the run factored to prove Φ₁₁, Φ₁₃
and Φ₄₄ there; huntlib's bounded factoring may not reach it, and the
evidence then lists those values as UNPROVED (the find stands on the three
legs; the owner certifies them by hand). The deterministic Miller–Rabin
bound is passed by the top value at x = 258 (A070737 n = 11), so every
campaign classifies on a strong probable-prime chain and proves every
discovery's values by certificate before writing them.

## The odds model

Bateman–Horn over the forms of an index, with the singular series computed
from the sieve's own killed sets (cyclotomic_model.py): each form
contributes 1/ln Φ_k(x), about 1/(φ(k) ln x). **Validation (G11)**: at the
54 published terms searched above the exception zone (A070737's a(5) to
a(10) from their predecessors; A072942's 48 indices with a(n) ≥ 10⁴ from
x = 3), E sums to 67.2 against a Gamma(54, 1) law (P = 0.956, inside both
tails; per family 1.13 over 6 and 1.26 over 48; quantiles 0.10–1.00) — the
terms have come a little late rather than early. Predictions, stated before
any run (model_results.json):

| term | from | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|
| A070737 a(11) | a(10) = 1.35×10¹⁶ | 9.1×10¹⁸ | 3.7×10¹⁹ | 1.0×10²⁰ | 1.8×10²⁰ |
| A070737 a(12) | a(11)'s median | 8.5×10²¹ | 3.2×10²² | 8.3×10²² | 1.5×10²³ |
| A070737 a(13) | a(12)'s median | 4.6×10²⁴ | 1.7×10²⁵ | 4.3×10²⁵ | 7.7×10²⁵ |
| A072942 a(66) | 3 | 6.3×10¹⁵ | 2.0×10¹⁶ | 5.2×10¹⁶ | 9.7×10¹⁶ |
| A072942 a(48) | 3 | 1.9×10¹⁷ | 6.9×10¹⁷ | 1.8×10¹⁸ | 3.4×10¹⁸ |
| A072942 a(78) | 3 | 8.9×10¹⁴ | 3.1×10¹⁵ | 8.1×10¹⁵ | 1.5×10¹⁶ |
| A072942 a(88) | 3 | 1.6×10¹⁶ | 5.5×10¹⁶ | 1.4×10¹⁷ | 2.5×10¹⁷ |
| A072942 a(80) | 3 | 6.2×10¹⁹ | 2.1×10²⁰ | 5.3×10²⁰ | 9.8×10²⁰ |
| A072942 a(60) | 3 | 1.0×10²⁵ | 3.4×10²⁵ | 8.6×10²⁵ | 1.6×10²⁶ |
| A072942 a(72) | 3 | 4.7×10²⁵ | 1.6×10²⁶ | 3.9×10²⁶ | 7.2×10²⁶ |
| A072942 a(84) | 3 | 5.3×10²⁴ | 1.8×10²⁵ | 4.4×10²⁵ | 8.0×10²⁵ |
| A072942 a(96) | 3 | 1.0×10²⁵ | 3.4×10²⁵ | 8.6×10²⁵ | 1.6×10²⁶ |
| A072942 a(90) | 3 | 3.0×10²⁴ | 1.0×10²⁵ | 2.6×10²⁵ | 4.7×10²⁵ |

The clock to each median at the engine's measured rates (BENCHMARKS.md,
engine v2): a(11) of A070737 is under a minute and a(12) about an hour;
a(13) about 10 days at the median (Q1 3 days, P90 7 weeks); A072942's
a(66), a(78), a(88), a(48) and a(80) seconds to minutes, a(60) about 15
hours, a(72) about 2 days, a(84) a week, a(96) and a(90) 10–11 days.
a(14) of A070737 (median 5.6×10²⁷) is years. The model has run early and
late elsewhere in this repository (mean E 0.70 to 1.62): read the quantile
table, not the median.

**How the finds scored** (RESULTS.md): over the eight finds E sums to 7.69
against a Gamma(8, 1) law (P = 0.50), a mean E of 0.96 — percentiles from
15% (a(80) of A072942, the one find under its Q1) to 86% (a(78)), none past
its P90. The model ran true here; the clocks were the campaigns' (a(12) in
35 minutes, a(60) in 31.5 h).

## Running it

Requirements: an NVIDIA GPU with CuPy (developed on an RTX 4090, CUDA 13,
CuPy 14), Python 3.12+, numpy, sympy (gmpy2 recommended).

```
python launch.py                            # the hunt: A070737, indefinite, resumable
python launch.py --family A072942           # A072942: every open index in turn, cheapest first
python launch.py --family A072942 --index 60   # one open index of A072942
python launch.py --status [--family F]      # where the cursor is; reads, never writes
python launch.py --selftest                 # the full gate battery
python score.py                             # gates x fingerprinted benchmark
```

A070737 has one checkpoint and ledger; A072942 one checkpoint per index
and one ledger; one campaign runs at a time. Throttles, each priced in
`--help`: `--workers`, `--gpu-yield-ms`, `--gentle`. **The first battery
after a kernel change compiles every configuration once** (NVRTC) and runs
several minutes longer than a warm one. The acceptance test of CLAUDE.md
5g — each family started fresh with no flags, its first `[STATUS]` lines
read for the pool, the rate and the rung — is the owner's to run, being a
campaign start; the campaigns of 2026-10-23 to 10-25 ran at their priced
rates (RESULTS.md). `--family` takes A070737 or A072942 only: A233512 is
the derived entry, settled by A070737's finds (`also_settles`), and asking
the launcher for it raises a KeyError naming the two families.

## Trust

The repository's machinery is described in [CONVENTIONS.md](../CONVENTIONS.md):
an oracle in sympy (cyclotomic_reference.py), a CPU engine marking a dense
line (cyclotomic_search.py; the dense t line of the class where no dense x
line fits), the GPU engine pinned to it bit for bit on populated windows at
every height to the 10⁴⁰ ceiling (G9), frozen benchmark fingerprints,
canaries that must rediscover published terms in both families, a
three-way discovery protocol with a factor witness for the value that stops
an A070737 run, and BLS75 certificates for every value of a discovery,
re-verified before they are written. What is this project's:

* **The forcing formula is proved and checked**, not assumed: the walk's
  forced primes equal "q ≤ n + 1" at every A070737 filter to 30 and
  "(q − 1) | n" at every A072942 index to 99 (G2c), and the CPU engine
  raises if its kill sets ever force something else (forced_unit).
* **The kill sets are built four ways** (residue walk, roots of unity by
  nthroot_mod, powers of a primitive root, vectorised polynomial
  evaluation) and agree everywhere they are compared (G2b, G3).
* **The Fermat stage's Horner arithmetic** equals Python's pow on every
  limb count it compiles, for cyclotomic indices of degree 1 to 12 at
  heights to 10³⁹, and its stream equals the CPU sieve filtered by a CPU
  Fermat chain (G23).
* **The derived entry** A233512 is the strictly increasing restatement
  of A070737, so a find settles it only where that recurrence says so
  (Codex's CYL-005): at the first index a find settles, when the find
  exceeds the previous term and every term from a(5) to it has been
  strictly increasing (G1d proves that through a(10)); a plateau (one x
  settling two indices) leaves the second index of A233512 open. Its
  records carry the integer under x, the letter its own comment and
  example lines use (its name gives none).
* **Nine values of three A072942 finds carry no certificate** (RESULTS.md):
  their BLS75 route needs a cyclotomic value outside the run factored
  (Φ₅(x) and Φ₁₀(x), 67 digits, at n = 66 and 88), so the evidence lists
  them under `unproved` and the finds stand on the three legs. Each was
  proved prime by FLINT's APR-CL on 2026-10-25 (0.1–25 s at 168–670
  digits) — a deterministic proof, not a file a reader can re-check; a
  checkable certificate is Codex's CYL-003 route or ECPP.
