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

**Status: ACTIVE** — built 2026-10-08, no campaign run yet. The frontiers
stand at a(15) = 17,762,917,045,631 on A165234 (a(16) open; the entry also
states a(29) = 29), a(15) = 19 on A230663 (a(16) open; a(39) = 43 stated),
a(15) = 409,333 on A092120 (a(16) open; a(19) = 163 stated) and
a(16) = 1,500,599,554,819 on A347537 (a(17) open). The model puts a(16)
through a(20) of A165234 inside two hours of sweeping from the bottom of
the line and a(21) at about two days; A230663 and A347537 the same shape;
A092120 a(16)–a(18) inside the first hour and a(20) at about three days
([RESULTS.md](RESULTS.md), "What is open now").

## The problem

| entry | name (%N), verbatim | published terms | last published | last moved |
|---|---|---|---|---|
| [A165234](https://oeis.org/A165234) `hard`, `more` | Least prime p such that 2x^2 + p produces primes for x=0..n-1 and composite for x=n. | a(1)–a(15), and a(29) = 29 in a comment | a(15) = 17,762,917,045,631 | Daniel Suteu, Dec 22 2024 |
| [A230663](https://oeis.org/A230663) `more` | Least prime p such that x^2 + 3*x + p produces primes for x = 0..n-1 but not x = n. | a(1)–a(15), and a(39) = 43 in a comment | a(15) = 19 (a(14) = 11,613,197,109,589) | Daniel Suteu, Dec 22 2024 |
| [A092120](https://oeis.org/A092120) | a(n) is the first term p in a sequence of primes such that p+4m^2 is prime for m = 0 to n, but composite for m = n+1; a(n) = -1 if no such prime exists. | a(0)–a(15), and a(19) = 163 in a comment | a(15) = 409,333 (a(14) = 604,490,757,900,187) | Jens Kruse Andersen, Oct 24 2008 |
| [A347537](https://oeis.org/A347537) `more` | a(n) is the smallest prime p such that the polynomial k^4 + k^3 + k^2 + k + p yields primes for k = 0..n-1, but not for k = n. | a(1)–a(16) | a(16) = 1,500,599,554,819 (a(15) = 699,669,742,107,967) | Bert Dobbelaere, May 12 2026 |

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

| A230663 | bound, from A164926 | the model's P(a(n) at or below it) |
|---|---|---|
| a(16) | ≤ 348,284,517,256,411,909 | 0.999 |
| a(17) | ≤ 8,461,068,614,861,832,373 | 0.98 |
| a(18) | ≤ 3,744,101,869,688,673,856,369 | 0.998 |
| a(20) | ≤ 234,505,015,943,235,329,419 | 0.14 |

(`model_results.json` carries the exact figures.) And in the other
direction A164926(n+1) ≥ A230663(n) − 2 for every n, with equality when
A230663(n) − 2 is prime: **a find of A230663(n) whose p − 2 is prime
settles A164926(n+1) = p − 2**, which the launcher records in the
evidence as `also_settles` after checking it from the bare definition; a
find whose p − 2 is composite proves A164926(n+1) > p − 2. Both are
gated (G1d). A164926's a(20) is open above 3.744×10²¹ (euler-prime-runs).

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
depth constants, the sieve depth and the launch budget re-swept flat. The parity gate (G9) pins GPU against CPU bit for bit on
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

**What it predicts** (`model_results.json`, written before any run; every
depth is the term p itself, from the bottom of the line):

| A165234 | median | P90 | | A230663 | median | P90 |
|---|---|---|---|---|---|---|
| a(16) | 3.68e15 | 4.73e16 | | a(16) | 2.56e15 | 2.82e16 |
| a(17) | 1.01e17 | 1.29e18 | | a(17) | 1.14e15 | 4.74e17 |
| a(18) | 3.19e18 | 3.97e19 | | a(18) | 3.08e18 | 3.00e19 |
| a(19) | 1.41e20 | 1.44e21 | | a(19) | 7.60e19 | 8.79e20 |
| a(20) | 4.95e21 | 4.93e22 | | a(20) | 3.58e21 | 3.27e22 |
| a(21) | 2.19e23 | 1.93e24 | | a(21) | 6.40e22 | 9.69e23 |

| A092120 | median | P90 | | A347537 | median | P90 |
|---|---|---|---|---|---|---|
| a(16) | 1.51e17 | 1.43e18 | | a(17) | 1.37e17 | 1.16e18 |
| a(17) | 5.02e18 | 4.44e19 | | a(18) | 3.96e18 | 3.21e19 |
| a(18) | 1.90e20 | 1.56e21 | | a(19) | 1.45e20 | 1.13e21 |
| a(20) | 2.73e23 | 2.05e24 | | a(20) | 6.31e21 | 4.71e22 |
| a(21) | 1.08e25 | 7.81e25 | | a(21) | 2.39e23 | 1.73e24 |

A230663's a(17) is predicted *below* its a(16): the seventeenth form adds
no new kill at any prime under 37 (x(x + 3) takes the same value at x and
at −x − 3), so its singular series jumps. The rows are not a schedule:
one sweep settles the indices in whatever order their first occurrences
lie on the line.

**The clocks, from the engine API** (BENCHMARKS.md has the per-filter
table and what is still owed; the campaign itself has not run). A165234
runs 2.6×10¹⁷ p/s at n = 18 and 1.18×10¹⁸ p/s at n = 21 on the full wheel
to 53, A347537 6.0×10¹⁷ p/s at n = 19; at those rates the medians above
are: A165234 a(16)–a(19) within minutes, a(20) under two hours, a(21)
about three days (the expected clock to a CONFIRMED find, which weighs the
tail of the distribution, is 7.7 days); A230663 the same to a(20), a(21)
about a day and a half; A092120 a(16)–a(18) within an hour, a(20) about
three days; A347537 a(17)–a(19) within minutes, a(20) under two hours,
a(21) about two and a half days. Budget 1.5–2× on each.

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
campaign will read another's cursor. A fresh campaign opens at the bottom
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
