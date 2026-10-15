# polynomial-runs — A165234, A230663, A092120 and A347537

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of four **exact-run polynomial ladders** —
one unknown prime p and a list of additive shifts that are the values of a
polynomial. **A165234** asks for the least prime p such that 2x² + p is
prime for x = 0..n−1 and composite for x = n; **A230663** the same with
x² + 3x + p; **A092120** the first prime p such that p + 4m² is prime for
m = 0..n but composite for m = n+1 (offset 0); and **A347537** the smallest
prime p such that k⁴ + k³ + k² + k + p is prime for k = 0..n−1 but not for
k = n. They are the siblings of euler-prime-runs' A164926 (x² + x + p).
The entries' frontiers are Daniel Suteu's of December 2024 (A165234,
A230663), Jens Kruse Andersen's of October 2008 (A092120) and Bert
Dobbelaere's of May 2026 (A347537).

**Nineteen new terms, found and verified 2026-10-08 to 2026-10-15:
a(16)–a(21) of A165234, a(16)–a(20) of A230663, a(16)–a(18) of A092120 and
a(17)–a(21) of A347537** — the first advance on A092120 since 2008, on
A165234 and A230663 since 2024, and on A347537 since May 2026. The largest
is A347537's a(21) = 545,605,440,824,324,681,493,499. The integers, their
verification and the campaigns are in [RESULTS.md](RESULTS.md).

**Status: PAUSED — open to others** — nothing is running. One campaign per
family ran between 2026-10-08 and 2026-10-15, 89 hours on the campaigns'
clocks, and each was stopped by the owner inside the filter for its next
term. Every open index is searched empty to p = 4.2236×10²² on A165234
(a(22) open), 1.5907×10²¹ on A230663 (a(21) open), 2.6625×10²⁰ on A092120
(a(20) open) and 5.5072×10²³ on A347537 (a(22) open). The model puts
A230663's a(21) and A092120's a(20) at about two and a half days each from
those cursors, and the two a(22)s at 91 and 52 days
([RESULTS.md](RESULTS.md), "What is open now", which also lists what a
resume owes first).

## The problem

| entry | name (%N), verbatim | published terms | last published | last moved |
|---|---|---|---|---|
| [A165234](https://oeis.org/A165234) `hard`, `more` | Least prime p such that 2x^2 + p produces primes for x=0..n-1 and composite for x=n. | a(1)–a(15), and a(29) = 29 in a comment | a(15) = 17,762,917,045,631 | Daniel Suteu, Dec 22 2024 |
| [A230663](https://oeis.org/A230663) `more` | Least prime p such that x^2 + 3*x + p produces primes for x = 0..n-1 but not x = n. | a(1)–a(15), and a(39) = 43 in a comment | a(15) = 19 (a(14) = 11,613,197,109,589) | Daniel Suteu, Dec 22 2024 |
| [A092120](https://oeis.org/A092120) | a(n) is the first term p in a sequence of primes such that p+4m^2 is prime for m = 0 to n, but composite for m = n+1; a(n) = -1 if no such prime exists. | a(0)–a(15), and a(19) = 163 in a comment | a(15) = 409,333 (a(14) = 604,490,757,900,187) | Jens Kruse Andersen, Oct 24 2008 |
| [A347537](https://oeis.org/A347537) `more` | a(n) is the smallest prime p such that the polynomial k^4 + k^3 + k^2 + k + p yields primes for k = 0..n-1, but not for k = n. | a(1)–a(16) | a(16) = 1,500,599,554,819 (a(15) = 699,669,742,107,967) | Bert Dobbelaere, May 12 2026 |

Found here, and not yet entered in the OEIS (2026-10-15 export):
a(16)–a(21) of A165234, a(16)–a(20) of A230663, a(16)–a(18) of A092120 —
which brings the comment's a(19) = 163 into an unbroken run of known
terms — and a(17)–a(21) of A347537.

**The run is exact, so the sequences are not monotone.** Call the *run*
of a prime p the number of shifts from the first whose value is prime:
2·1² + p, 2·2² + p, … up to the first that is not. A165234's a(n) is the
first prime whose run is exactly n − 1 (the name counts x from 0, so n
primes), and likewise A230663's and A347537's; A092120's a(n) is the first
prime whose run is exactly n (m = 0..n prime). A prime with a longer run
is a term of a later index: A165234's a(3) = 3, a(5) = 5, a(11) = 11 and
a(29) = 29 are the four primes p for which 2x² + p is prime for every
x < p — the imaginary quadratic field Q(√−2p) has class number 2, and
that list is complete — and A230663's a(39) = 43 is Euler's polynomial
shifted by one. So no term is a floor for another and **every index's
line starts at the bottom, p = 2**.

**One sweep settles every index at once.** A sieve at filter n keeps the
primes p for which p and the shifted values of a(n) have no small factor;
the classification then reads each survivor's run to its end. Every prime
below the cursor with a run at least a(n)'s has therefore had its exact
run read, which settles the first occurrence of *every* exact run from n
up. A campaign sweeps one line from the bottom with the filter at the
lowest open index; a survivor whose run belongs to a later index is a
discovery of that index alone, and when the filter's own index lands the
filter moves to the next index still open — skipping the indices found
early and the indices the entries settle in a comment.

**A230663 and A164926 are one problem, shifted.** x² + 3x + p =
(x+1)² + (x+1) + (p − 2), so x² + 3x + p is prime for x = 0..n−1 exactly
when y² + y + (p − 2) is prime for y = 1..n. Hence
A230663(n) ≤ A164926(n+1) + 2 — an upper bound at every open index of
A230663 whose successor is known on A164926:

| A230663 | bound, from A164926 | the model's P(a(n) at or below it) | found |
|---|---|---|---|
| a(16) | ≤ 348,284,517,256,411,909 | 0.9999 | 57,204,849,284,656,039 |
| a(17) | ≤ 8,461,068,614,861,832,373 | 0.9999 | 97,079,155,423,260,379 |
| a(18) | ≤ 3,744,101,869,688,673,856,369 | 1.000 | 15,197,452,440,079,259,719 |
| a(20) | ≤ 234,505,015,943,235,329,419 | 0.12 | **the bound itself** |

(`model_results.json` carries the exact figures, written before the run.)
a(20) came at its bound: the prime A164926(21) + 2 was always a candidate,
and the sweep proved no smaller one. And in the other
direction A164926(n+1) ≥ A230663(n) − 2 for every n, with equality when
A230663(n) − 2 is prime: **a find of A230663(n) whose p − 2 is prime
settles A164926(n+1) = p − 2**, which the launcher records in the
evidence as `also_settles` after checking it from the bare definition; a
find whose p − 2 is composite proves A164926(n+1) > p − 2. Both are
gated (G1d). A164926's a(20) is open above 3.744×10²¹ (euler-prime-runs).
Of the five finds only a(20)'s p − 2 is prime, and it is A164926's known
a(21); the other four bound A164926 below what is already known, so
nothing new rode on this hunt.

**Which number goes in the OEIS.** Every name gives the term the letter
p. An evidence file carries the integer under that letter, `forms` reads
the condition in the entry's own letters (x for A165234 and A230663, m for
A092120, k for A347537), and `oeis_terms` is literally what to submit —
`{"16": <integer>}` reads "a(16) is this integer". A find settles exactly
one index: the run is exact, so one integer is never two terms.

## The mathematics of the engine

**The killed set.** For a prime q and a shift c, q divides p + c exactly
when p ≡ −c (mod q), so the residues of p that q kills at index n are
{0} ∪ {−c : c a shift of index n} (mod q). The oracle walks every residue
and tests divisibility; the CPU engine builds the set of negated shifts;
the GPU engine consumes the set and never sees a form (G2b, G3). That the
next value is *not* prime is no sieve's business: the classification reads
it.

**Its size, and why the wheel is strong.** Every shift is even, so p is
odd. For odd q a quadratic takes at most (q + 1)/2 distinct values modulo
q and the quartic k(k+1)(k²+1) at most q − 1, so q kills at most
min(forms, (q + 1)/2) residues on the quadratics and min(forms, q − 1) on
A347537 — about half of each prime's residues once the index passes
(q + 1)/2. The primes to 59 keep 1.1×10⁻⁵ of the line on A165234 at
n = 16, 1.5×10⁻⁵ on A230663, 8.8×10⁻⁶ on A092120 and 6.8×10⁻⁶ on A347537
at n = 17: the opposite regime from the primorial ladders, where the wheel
was nearly blind. Here the wheel does most of the work and the hunt is
paid in line. Both bounds are below q, so no prime kills every residue,
Dickson's conjecture applies, and every index is conjecturally attained
(the entries say so, citing the prime k-tuples conjecture and Mollin).

**The forced classes.** Modulo 3 the first two forms kill two classes on
every family: 2x² takes 0 and 2, so p ≡ 2 (mod 3) on A165234; x² + 3x,
4m² and the quartic take 0 and 1, so p ≡ 1 (mod 3) on the other three. So
p ≡ 5 (mod 6) on A165234 and p ≡ 1 (mod 6) on A230663, A092120 and
A347537 from the first index with two forms (n = 2; n = 1 on A092120). No
prime past 3 is ever forced on the quadratics ((q + 1)/2 < q − 1 for
q ≥ 5); the quartic is checked to n = 30 at every prime under 400 (G2c).

**The exception zone.** A kill by q proves nothing unless the value
exceeds q, and the smallest value is p itself. So the device starts above
the sieve depth and the primes from 2 to the depth are classified one at a
time on the host — the forced class plus 2 and 3 themselves. It is not
vacuous: A165234's a(11) = 11 and a(29) = 29 and A230663's a(15) = 19 and
a(39) = 43 live there.

**The engine** is primorial-runs' engine v2 and planner p1, taken whole
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), Decision 1): the window
sieve with every window prime on a quad table, subset wheels, the 2⁶⁴
reduction bound, the narrow and wide survivor records, lazy and folded
in-block rounds, generated tail rounds, and the planner that chooses wheel
and window together to minimise the expected clock to a confirmed find.
The kernel sees killed residues, never a form; one polynomial in place of
the primorial sums changed the oracle's shift function and not one line of
device code. Candidates are carried as (base, offset) with the base a
Python integer. **What round 1 changed** ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)):
the strong kill sets reach the window's survival target after 24–32 sieve
primes where the primorial regime needed 40, so the fixed work per
candidate residue is a larger share of the kernel and a wider window with
a bigger block amortises more of it — the planner's width table was
re-measured here (a 256-period window reads 1.118 over the inherited 160
at n = 18, and the (16, 2) block shape 1.047 over (8, 2) at the day-long
n = 21), the planner now considers the engine's full 256 periods, and the
depth constants, the sieve depth and the launch budget re-swept flat.
**What round 2 changed — engine v2** ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)):
Nsight Compute on this regime's kernel at the day-long filters found the
three pipes it is bound by within 5% of each other at 70–74%, a warp
stalled on instruction fetch about once per issued instruction (the
queue-overflow fallback, never executed, inlined and unrolled at fifty-odd
sites to seven tenths of the kernel's code and threaded through the hot
path), and a block per SM left behind by a queue margin ranked before the
queue entry was decided. The fallback now sits behind a call and the
margin is re-ranked on the compiled footprint: 1.05–1.06 at the day-long
filters, the survivor stream identical. The parity gate (G9) pins GPU against CPU bit for bit on
populated windows: every family, both classes, one- to three-level and
subset wheels, first levels past the planner's memory budget, the first
period clipped at the engine floor, windows past 2⁶⁴ and past the
deterministic bound, and hard against the 10⁴⁰ ceiling.

**What is this project's own:** the index arithmetic (the index is not
the run: `run_of`/`index_of` carry each name's reading), the sparse known
tables (a comment's term far above the data is settled and skipped, never
hunted), the A164926 rider, and the model's integration floor (below).

**Ceilings.** The term stays under huntlib's 10⁴⁰ on every family, and the
values are within a few thousand of the term, so there is one ceiling.
The deterministic Miller–Rabin bound, 3.317×10²⁴ less the largest shift,
is a few thousand under the bound itself; past it every classification is
a strong probable-prime chain (which can lengthen a run, never hide one)
and every value of a discovery is proved by a BLS75 certificate found by a
bounded search, re-verified before it is written. It is a `[MILESTONE]`,
never a stop. What ends a family is the GPU tail's residue list — 32 kills
a prime, one per form — so the last filter is n = 32 (31 on A092120);
the model puts a(23) a decade away.

## The odds model

Bateman–Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from; the intensity of a(n)'s
event — a run of exactly its index's — is the intensity of index n less
that of index n + 1, each logarithm taken of the value. **The integrals
start at the exception zone's top, 10⁴, not at 2:** with a singular series
near 10⁹ (strong kill sets) and sixteen logarithms of values near 10 the
integrand at the very bottom of the line is not a density of anything —
the primorial ladders never saw this because their shifts put every value
far above the bottom — and the line below 10⁴ is classified on the host by
brute force regardless.

**Validation (G11), stated before the run.** E is the expected number of
primes with a(n)'s exact run between 10⁴ and the a(n) that actually
occurred; under a correct model it is a draw of Exp(1). Over the 26
published terms above the exception zone the E's sum to 21.00 at P = 0.162
under Gamma(26, 1), quantiles 0.00–0.92; per family, mean E 0.92 over
five draws on A165234, 0.95 over six on A230663, 0.84 over eight on
A092120 and 0.57 over seven on A347537 (its a(16) = 1.5×10¹², E = 0.02,
came very early). Elsewhere in this repository first occurrences have run
1.2–2.5× past their medians, and primorial-runs' came early (mean 0.70);
read the whole quantile row.

**Scored on the run.** The nineteen finds are nineteen more draws: E sums
to 18.60, **a mean of 0.98**, at P = 0.49 under Gamma(19, 1) — neither late
nor early — with per-family means of 0.64, 1.72, 1.04 and 0.61 and the
usual Exp(1) scatter, from A165234's a(21) at the 4th percentile of its row
to A230663's a(16) at the 96th ([RESULTS.md](RESULTS.md), "The finds
against the model").

**What it predicts** (`model_results.json`, written before any run; every
depth is the term p itself, from the bottom of the line), and what came:

| A165234 | median | P90 | found | | A230663 | median | P90 | found |
|---|---|---|---|---|---|---|---|---|
| a(16) | 6.12e15 | 5.39e16 | 1.14e15 | | a(16) | 3.31e15 | 3.02e16 | 5.72e16 |
| a(17) | 1.79e17 | 1.50e18 | 6.43e17 | | a(17) | 9.57e16 | 8.24e17 | 9.71e16 |
| a(18) | 5.79e18 | 4.62e19 | 5.52e16 | | a(18) | 3.98e18 | 3.22e19 | 1.52e19 |
| a(19) | 2.09e20 | 1.60e21 | 5.35e20 | | a(19) | 1.30e20 | 1.01e21 | 1.57e21 |
| a(20) | 7.40e21 | 5.49e22 | 1.06e22 | | a(20) | 4.70e21 | 3.53e22 | 2.35e20 |
| a(21) | 2.89e23 | 2.08e24 | 1.72e21 | | a(21) | 1.67e23 | 1.22e24 | open |

| A092120 | median | P90 | found | | A347537 | median | P90 | found |
|---|---|---|---|---|---|---|---|---|
| a(16) | 1.79e17 | 1.50e18 | 1.22e17 | | a(17) | 1.37e17 | 1.16e18 | 1.71e17 |
| a(17) | 5.79e18 | 4.62e19 | 2.92e19 | | a(18) | 3.97e18 | 3.21e19 | 5.55e17 |
| a(18) | 2.09e20 | 1.60e21 | 2.63e20 | | a(19) | 1.45e20 | 1.13e21 | 2.12e19 |
| a(20) | 2.89e23 | 2.08e24 | open | | a(20) | 6.32e21 | 4.71e22 | 5.51e21 |
| a(21) | 1.12e25 | 7.90e25 | open | | a(21) | 2.39e23 | 1.73e24 | 5.46e23 |

A165234's row n + 1 and A092120's row n agree to the figures shown: for
odd q, multiplication by 2 is a bijection, so {2x² : x = 0..n} and
{4m² : m = 0..n} kill the same number of residues of every prime, and the
two families' singular series are equal. (Until the pause these tables
carried figures from an earlier run of the model that did not match
`model_results.json`; they now carry the file's, which BENCHMARKS.md's
clocks always used.) The rows are not a schedule: one sweep settles the
indices in whatever order their first occurrences lie on the line, and
two of the four campaigns found an index before the one below it.

**The clocks, against the campaigns.** Every filter a campaign swept whole
for more than two minutes ran at 0.99–1.03× the rate BENCHMARKS.md priced
for it, from 4.6×10¹⁷ p/s at A165234's n = 19 to 2.03×10¹⁸ p/s for the 74
hours of A347537's n = 21 ([RESULTS.md](RESULTS.md), "The campaigns against
their benchmarks"). Everything up to a(20) on every family took minutes to
hours; the one long leg was A347537's a(21), at 2.3 medians. The filters
the campaigns stopped in run 9.2×10¹⁷ p/s (A230663 n = 21) to 3.42×10¹⁸ p/s
(A347537 n = 22).

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # the full gate battery; must end ALL GREEN
```

```bash
python score.py                # gates x 7 fingerprinted shapes
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py                       # A165234, the default
python launch.py --family A230663
python launch.py --family A092120
python launch.py --family A347537
```

Each family keeps its own checkpoint under its own config key, and no
campaign will read another's cursor. With the 2026-10 checkpoints in place
each command resumes its family at the cursor RESULTS.md gives; the
checkpoints are runtime files and not in the repository, and until the
finds are moved into the oracle's `FOUND` a fresh clone starts over. A
fresh campaign opens at the bottom
of its line with the filter at its lowest open index (16, 16, 16 and 17),
classifies the exception zone on the host, and sweeps. A find at the
filter's own index moves the filter to the next open index and carries
the classified line; a find above the filter is recorded and changes
nothing else. The hunt is indefinite by default, resumable, checkpointed
every segment, and stops cleanly on Ctrl+C with exit 130. `--to` caps the
depth, `--stop-on-discovery` exits once **this run** confirms a find,
`--workers` overrides the pool that is otherwise sized from a measurement
at the campaign's own filter, and `--gentle` yields the device and
classifies inline for a quieter desktop.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle that walks
  residues and tests divisibility, a numpy CPU engine that marks the dense
  line with no wheel at all, and a CuPy engine that generates wheel
  survivors and tests them. G9 pins the GPU stream to the CPU stream bit
  for bit on populated windows.
- **Exactness is checked in both directions.** The oracle reads every
  known term's run uncapped and requires exactly its index's (G1, G6); the
  protocol drill accepts a genuine term at its true run and rejects the
  same integer claimed one run longer and one run shorter; a discovery is
  re-read by the oracle before it is written.
- **The small terms are re-derived from nothing.** G2 reads the run of
  every prime below a bound on each line from the bare definition and
  requires the first occurrence of each run length to be the known term
  of that index — the comment terms a(29) = 29, a(39) = 43 and a(19) = 163
  among them — and no other run length to occur there.
- **The index is gated.** G1c rebuilds every index from the %S and %O
  lines and checks that a(n) has n forms where the name counts from 0 to
  n − 1 and n + 1 on A092120.
- **The rider is proved, not assumed.** G1d checks every A164926 bound on
  A230663 from the bare definition and the identity pointwise.
- **Canaries meet a later index first, as the campaign will.** From the
  bottom of the line the stream's first prime above the exception zone
  with a run at least the filter's must be the least known term there of
  that index or a later one: A230663 at filter 7 meets a(8) before a(7),
  A092120 at filter 9 meets a(15), A347537 at filter 9 meets a(10); the
  end-to-end drill on A165234 opens at index 13 and finds a(14) before
  a(13), on scratch files with the filter promoting itself.
- **The benchmark checks itself.** `SCORE2L` and `SCORE1L` sweep the
  identical absolute window with a two-level and a one-level wheel and must
  return the same 624 survivors and checksum.
- **Every ceiling raises rather than computes**, and the certificate drill
  proves values of a find's own shape near the 10⁴⁰ ceiling on the term.
- **The evidence files speak each entry's language** (p; x, m or k for
  the polynomial's argument), checked by the names drill on every record
  on disk and on the writer's header.
