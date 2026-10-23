# primorial-runs — A257466, A257467 and A258035

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

**Independent mathematical review:** Codex (OpenAI) maintains static
analysis and implementation proposals in [codex-reviews/](codex-reviews/README.md).
These reports follow the repository's [review workflow](../CODEX_REVIEWS.md);
Claude's original implementation and historical records retain their authorship.

A GPU hunt for the next terms of three **exact-run shift ladders** — one
unknown prime p and a list of additive shifts built from the primorials.
**A257466** asks for the smallest prime p such that p + pps(1), p + pps(2),
…, p + pps(n) are all prime but p + pps(n+1) is not, where pps(n) is the
partial primorial sum 2# + 3# + … + prime(n)# (2, 8, 38, 248, 2558, …).
**A257467** asks the same with psq(n), the square of the primorial (4, 36,
900, 44100, …), and **A258035** with pssq(n), the partial sums of those
squares (4, 40, 940, 45040, …). All three are Fred Schneider's, of April
and May 2015, each carries the keyword `hard`, and none has gained a term
since its author's last, between May and July 2015.

**Eighteen new terms, found and verified 2026-10-05 to 2026-10-08:
a(16)–a(20) of A257466, a(15)–a(19) of A257467 and a(11)–a(18) of A258035**
— the first advance on any of the three since 2015, and on A258035 a
correction as well: the entry's listed a(11) and a(12) are its a(12) and
a(13), and a(11) is 23,569,356,649. The integers, their verification and the
campaigns are in [RESULTS.md](RESULTS.md).

**Status: PAUSED — open to others** — nothing is running. One campaign per
family ran between 2026-10-05 and 2026-10-08 and each was stopped by the
owner inside the filter for its next term. The frontier stands at
a(20) = 9,588,149,987,699,367,569 on A257466, with a(21) open and every
open index searched empty to p = 1.0392×10²⁰; at
a(19) = 418,446,268,390,828,120,903 on A257467, with a(20) open above
p = 4.6117×10²⁰; and at a(18) = 438,392,474,524,896,220,603 on A258035,
with a(19) open above p = 4.4075×10²⁰. The model puts a(21) of A257466 and
a(19) of A258035 at about a week each from those cursors and a(20) of
A257467 at months ([RESULTS.md](RESULTS.md), "What is open now", which
also lists what a resume owes first).

## The problem

| entry | name (%N), verbatim | published terms | last published | last moved |
|---|---|---|---|---|
| [A257466](https://oeis.org/A257466) `hard`, `more` | Smallest prime number p such that p + pps(1), p + pps(2), ..., p + pps(n) are all prime but p + pps(n+1) is not, where pps(n) is the partial primorial sum (A060389(n)). | a(0)–a(15) | a(15) = 41,320,119,600,341 | Fred Schneider, May 15 2015 |
| [A257467](https://oeis.org/A257467) `hard` | Smallest prime number p such that p + psq(1), p + psq(2), ... p + psq(n) are all prime but p+psq(n+1) is not. (psq(n) is the square of the primorial.) | a(0)–a(14) | a(14) = 39,809,897,510,563 | Fred Schneider, May 16 2015 |
| [A258035](https://oeis.org/A258035) `hard`, `more` | Smallest prime number p such that p + pssq(1), p + pssq(2), ... p + pssq(n) are all prime but p+pssq(n+1) is not, where pssq(n) is the partial sum of the square of the proper terms of the primorial (A189997(n)-1). | a(0)–a(12) listed | a(12) listed as 4,428,230,508,349 | Fred Schneider, Jul 09 2015 |

All three are offset 0: a(0) = 2 in each, because 2 plus the first shift is
even. No entry carried a bound at an open index, and no other entry is an
affine map of any of them, so nothing rides for free. Found here, and not
yet entered in the OEIS (2026-10-08 export): a(16)–a(20) of A257466,
a(15)–a(19) of A257467 and a(11)–a(18) of A258035, the last including the
correction below.

**The run is exact, so the sequences are not monotone.** Call the *run* of
a prime p the number of leading shifts whose value is prime: p + pps(1),
p + pps(2), … up to the first that is not. a(n) is the first prime whose
run is *exactly* n. A prime with a longer run is a term of a later index
and says nothing about this one: A257466's a(9) = 191 and a(10) = 59 sit
far below its a(8) = 191,459, and its a(13) = 360,772,331 below its
a(12) = 494,272,241. So no term is a floor for another, and **every
index's line starts at the bottom, p = 2**.

**One sweep settles every index at once.** A sieve at filter n keeps the
primes p for which p and its first n shifted values have no small factor;
the classification then reads each survivor's run to its end. Every prime
below the cursor with a run of at least n has therefore had its exact run
read, which settles the first occurrence of *every* exact run from n up. A
campaign sweeps one line from the bottom with the filter at the lowest
open index. A survivor whose run is longer than the filter is a term of a
later index found early — recorded as a discovery of that index alone,
while the sweep goes on at the same filter — and when the filter's own
index lands, the filter moves to the next index still open, which may
skip indices found early.

**An erratum in A258035's published data, found here and confirmed by the
sweep.** The entry lists a(11) = 1,368,737,917 and
a(12) = 4,428,230,508,349. By the entry's own definition — the reading
under which its a(0)–a(10) and its worked example for 7 all check — the
run of 1,368,737,917 is exactly 12 and the run of 4,428,230,508,349 is
exactly 13 (the oracle's gate G1, sympy's `isprime` on every value). So
neither is the term it is listed as. This project built on a(0)–a(10)
only; that entry's campaign opened at index 11 and settled 11, 12 and 13
from the bottom of the line like any other term: **a(11) = 23,569,356,649**,
**a(12) = 1,368,737,917** and **a(13) = 4,428,230,508,349**. The listed
value is the first prime with a run of *at least* 11 — the sweep met it
first, one second before a(11) — which is what its author appears to have
computed for that index, the clause "p + pssq(n+1) is not prime" dropped.
The correction is evidenced like any discovery ([RESULTS.md](RESULTS.md),
"The erratum, confirmed").

**Which number goes in the OEIS.** The names give the term the letter p. An
evidence file carries the integer under that letter, `forms` reads
"p + pps(1), ..., p + pps(n) all prime, p + pps(n+1) not (and p prime)"
(or psq, or pssq), and `oeis_terms` is literally what to submit —
`{"16": <integer>}` reads "a(16) is this integer". A find settles exactly
one index: the run is exact, so one integer is never two terms.

## The mathematics of the engine

**The killed set.** For a prime q and a shift, q divides the term plus the
shift exactly when the term is congruent to minus the shift modulo q, so
the residues of the term that q kills at index n are

    K(q, n) = { 0 } ∪ { −pps(1), …, −pps(n) }  (mod q)

(with psq or pssq on the other two entries; 0 because p itself must be
prime). The oracle walks every residue and tests divisibility; the CPU
engine builds the set of negated shifts; the GPU engine consumes the set
and never sees a form. G2b and G3 pin the three constructions against each
other. The condition that p + pps(n+1) is *not* prime is no sieve's
business: it is read by the classification.

**Its size, and why the wheel is weak.** A primorial is 0 modulo q from
prime(n) ≥ q on. So psq(n) is 0 modulo q from there — the residue p itself
kills — and pps(n) and pssq(n) stop moving. Either way at most π(q) − 1
shifts are distinct and nonzero modulo q:

    w(q, n) ≤ 1 + min(n, π(q) − 1)

Fifteen kills at most for q = 47 where a linear ladder's 47 kills n of its
47 residues. The bound is below q, so no prime kills every residue: the
constellations have no fixed prime divisor, Dickson's conjecture applies,
and every index of every entry is conjecturally attained. The small primes
being nearly blind is the regime lcm-ladders and primorial-ladders found:
the primes to 59 keep 1.6×10⁻⁴ of the line on A257466, 4.7×10⁻⁴ on A257467
and about 3×10⁻⁴ on A258035, so what the hunt pays for is candidates, and
the engine that counts is the one with the highest candidate rate.

**The forced classes.** Every shift is even, so p is odd. Modulo 3, p and
its first shifted value leave one class — the first shift is 2 on A257466,
which leaves p ≡ 2 (mod 3), and 4 on the other two, which leaves
p ≡ 1 (mod 3) — and every later shift is congruent to the first. So
p ≡ 5 (mod 6) on A257466 and p ≡ 1 (mod 6) on A257467 and A258035, from
n = 1. No prime past 3 is ever forced. The GPU engine sweeps the class;
the CPU engine marks the dense line knowing nothing of it, so the parity
gate checks the forcing as well as the sieve.

**The exception zone.** A kill by q proves nothing unless the value exceeds
q, and the smallest value is p itself. So the device starts above the sieve
depth, and the primes from 2 to the depth are classified one at a time on
the host before the first launch — the forced class plus 2 and 3
themselves, which are primes outside the class that 2 and 3 force. It is
not vacuous: A257466's a(4) = 3 and a(3) = 5 are exactly such primes.

**The engine** is primorial-ladders' engine v1 and planner p1, taken whole
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), Decision 1) — which is
plus-two-cliques' engine v3: the window sieve (for a fixed wheel residue
the candidates of consecutive periods form an arithmetic progression modulo
every sieve prime, so "which of the next 160 periods does q kill" is one
window into a periodic bit pattern, read in one or two 64-bit shared loads
and a few funnel shifts), with subset wheels, the 2⁶⁴ reduction bound, the
narrow and wide survivor records, lazy and folded in-block rounds,
generated tail rounds, and the planner that chooses wheel and window
together to minimise the expected clock to a confirmed find. The kernel
sees killed residues, never a form; one list of shifts in place of another
changed the oracle's shift function and not one line of device code.
Candidates are carried as (base, offset) with the base a Python integer.
Engine v2 (round 2 of the log) reads every window prime's table as quads
— one 16-byte and one 8-byte shared load a prime instead of three 8-byte
loads, and only the words a periodic prime needs — after Nsight Compute
showed the kernel bound by the shared-memory pipes at every days-long
filter; it is worth 1.010–1.015 there, with the same survivor stream.
The parity gate (G9) pins GPU against CPU bit for bit on 29 populated
windows (749,295 survivors): every family, the classes 1 and 5 (mod 6),
one- to three-level and subset wheels, first levels of millions of
residues, the first period clipped at the engine floor, windows past 2⁶⁴
and past the deterministic bound, and hard against the 10⁴⁰ ceiling.

**What is this project's own** is everything about the run being exact:
the oracle's definition, the classification reading every survivor's run to
its end (the pool reads eight conditions past the filter and anything that
reaches that cap is re-read with none), the taxonomy that makes a run
longer than the filter a discovery of its own index, the frontier that can
jump over indices found early, and the model's exact-run intensity.

**Two ceilings, one of them measured.** The term stays under huntlib's
10⁴⁰, which no campaign here approaches: the open terms are below 10²⁴.
What grows is the shift — psq(20) = (71#)² is 3.1×10⁵³ — and a discovery
of a run of n needs a primality certificate for every value up to p plus
its n-th shift. Those values have no multiplier × term ± 1 structure, so
each is proved on its own by a bounded certificate search on N − 1 or
N + 1, and rule 5h asks for the height to be measured: random structureless
primes were proved by the first search 11 of 12 at 10⁴⁵, 12 of 12 at 10⁵⁰,
10⁵⁵ and 10⁶⁰ (the worst in 2.0 s), and 10 of 12 at 10⁶⁵; the launcher
retries a miss once with 200 ECM curves
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), Measurement 1). **The ceiling
on the values is 10⁶⁰**, and each family ends at the last index whose shift
is under it: n = 36 on A257466, n = 21 on A257467 (psq(22) = (79#)² passes
10⁶⁰), and n = 21 on A258035 as well. The
deterministic Miller–Rabin bound, 3.317×10²⁴ less the largest shift of the
filter, is crossed on A257466 near p = 3.3×10²⁴ through n = 18; the shift
alone passes the bound from n = 19 there and from n = 12 on the two
squared entries, and from then on every
classification is a strong probable-prime chain from the bottom of the
line (which can lengthen a run, never hide one) and every value of a
discovery past the bound is proved by certificate. It is a `[MILESTONE]`,
never a stop.

**The stopper.** What bounds a run from above is that the next shifted
value is composite. The evidence carries a prime factor of it where the
bounded effort (trial division, rho, 200 ECM curves) finds one; where it
does not — the value can be fifty digits with no small factor — it records
the failed base-2 strong probable-prime test, which is itself a proof of
compositeness.

## The odds model

Bateman–Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from. The intensity of primes whose
run is *at least* n is the series over the product of the logarithms of
the n + 1 values; the entries ask for a run of *exactly* n, so the
intensity of a(n)'s event is that of at least n less that of at least
n + 1. Each logarithm is taken of the *value*, not of p: psq(15) is
3.8×10³⁵ against terms near 10¹⁶, so on the squared entries most of the
factors are constants set by the shifts, which is what makes their terms
come later than A257466's at the same index. Every index is integrated
from the bottom of the line.

**Validation (G11), stated before the run.** E is the expected number of
primes with a run of exactly n between 2 and the a(n) that actually
occurred; under a correct model it is a draw of Exp(1). Over the 19
published terms above the exception zone (A258035's to a(10)):

| A257466 | a(6) | a(7) | a(8) | a(11) | a(12) | a(13) | a(14) | a(15) |
|---|---|---|---|---|---|---|---|---|
| E | 2.73 | 1.67 | 1.06 | 0.08 | 0.16 | 0.03 | 1.03 | 0.58 |

| A257467 | a(7) | a(8) | a(9) | a(10) | a(11) | a(12) | a(13) | a(14) | | A258035 | a(8) | a(9) | a(10) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E | 1.78 | 0.43 | 2.36 | 0.22 | 2.90 | 0.27 | 0.59 | 0.44 | | E | 0.76 | 2.34 | 0.58 |

They sum to 20.02 at P = 0.620 under the Gamma(19, 1) law, quantiles
0.03–0.95, and the families agree: mean E 0.92 over eight draws on
A257466, 1.12 over eight on A257467, 1.23 over three on A258035. Elsewhere
in this repository first occurrences have run 1.2–2.5× past their medians,
so read the whole quantile row, not the median alone.

**What it predicted** (`model_results.json`, written before the run and
kept as the record; every depth is the term p itself, from the bottom of
the line):

| A257466 | Q1 | median | Q3 | P90 |
|---|---|---|---|---|
| a(16) | 2.66e14 | **1.18e15** | 3.77e15 | 8.79e15 |
| a(17) | 6.19e15 | **2.66e16** | 8.30e16 | 1.90e17 |
| a(18) | 1.41e17 | **5.88e17** | 1.80e18 | 4.08e18 |
| a(19) | 3.49e18 | **1.43e19** | 4.30e19 | 9.61e19 |
| a(20) | 9.51e19 | **3.81e20** | 1.13e21 | 2.51e21 |
| a(21) | 2.50e21 | **9.84e21** | 2.89e22 | 6.32e22 |

| A257467 | Q1 | median | Q3 | P90 | | A258035 | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|---|---|---|---|---|
| a(15) | 5.86e14 | **1.93e15** | 4.92e15 | 9.71e15 | | a(11) | 4.11e09 | **1.48e10** | 4.00e10 | 8.25e10 |
| a(16) | 1.54e16 | **4.99e16** | 1.25e17 | 2.46e17 | | a(12) | 1.01e11 | **3.48e11** | 9.21e11 | 1.87e12 |
| a(17) | 4.27e17 | **1.37e18** | 3.42e18 | 6.66e18 | | a(13) | 2.46e12 | **8.35e12** | 2.17e13 | 4.36e13 |
| a(18) | 1.35e19 | **4.26e19** | 1.05e20 | 2.04e20 | | a(14) | 6.09e13 | **2.02e14** | 5.18e14 | 1.03e15 |
| a(19) | 4.16e20 | **1.30e21** | 3.20e21 | 6.17e21 | | a(15) | 1.77e15 | **5.79e15** | 1.47e16 | 2.89e16 |
| a(20) | 1.32e22 | **4.10e22** | 9.99e22 | 1.92e23 | | a(16) | 4.87e16 | **1.57e17** | 3.94e17 | 7.73e17 |

Each row is the distribution of the first prime with a run of exactly that
index, taken alone. The rows are not a schedule: the indices are settled by
one sweep, in whatever order their first occurrences lie on the line, and
a later index can land before an earlier one. On A258035 the listed values
1,368,737,917 and 4,428,230,508,349, which the sweep confirmed as a(12)
and a(13), sit at the 1.5% and 36% points of those rows.

At the measured rates ([BENCHMARKS.md](BENCHMARKS.md): 4.9×10¹⁵ p/s at
A257466's n = 16 rising to 2.6×10¹⁶ at n = 21; 2.1×10¹⁵ to 6.0×10¹⁵ p/s on
A257467; up to 1.0×10¹⁶ p/s on A258035) the model's median for each index,
taken alone, is this far from the bottom of the line: A257466 a(16) 0.2 s,
a(17) 4 s, a(18) a minute, a(19) 16 min, a(20) 5.6 h, a(21) 4.4 days,
a(22) four months; A257467 a(15) a second, a(16) 21 s, a(17) 7 min, a(18)
2.6 h, a(19) 2.5 days, a(20) ten weeks; A258035 a(11)–a(15) within two
seconds, a(16) 30 s, a(17) 11 min, a(18) 5.1 h, a(19) 5.5 days. So a night
of each campaign was expected to reach a(20) of A257466, a(18) of A257467
and a(18) of A258035, with one more term on each inside a week. Every one
of those was a median of a model that had run 1.5–2× late on first
occurrences elsewhere in this repository.

**How the finds scored.** Eighteen draws, each E taken from the bottom of
the line to the term that occurred:

| | A257466 a(16)–a(20) | A257467 a(15)–a(19) | A258035 a(11)–a(18) |
|---|---|---|---|
| E | 2.11, 1.29, 0.87, 0.31, 0.07 | 0.51, 0.63, 0.33, 0.99, 0.29 | 0.96, 0.01, 0.44, 0.55, 0.12, 0.45, 1.17, 1.58 |
| mean | 0.93 | 0.55 | 0.66 |

They sum to 12.68, a mean of 0.70 at P = 0.093 under Gamma(18, 1): the
terms came **earlier** than the intensity says, where the published terms
had scored on the mean (1.05) and every other family in this repository
has run late. The night reached a(20) of A257466 in 1.5 h (a(20) came in
the first segment of its filter, at the 7th percentile), a(19) of A257467
— the term "inside a week" — in 18 h of running, and a(18) of A258035 in
14.7 h. Five draws ran past their medians by more than 1.5× — A257466's
a(16) and a(17), which cost seconds, A258035's a(17) and a(18) (2.0 and
2.9 medians, 25 min and 14.2 h) and A257467's a(18) (1.6 medians, 3.95 h)
— and the other thirteen came early. The filters swept whole ran at
0.97–1.08× the rates above. The open terms from
where the cursors stand: a(21) of A257466 median 1.07×10²² (4.7 days at
2.6×10¹⁶ p/s), a(20) of A257467 median 4.27×10²² (76 days at 6.4×10¹⁵
p/s), a(19) of A258035 median 5.99×10²¹ (6.2 days at 1.04×10¹⁶ p/s). The
per-term table, the campaign rates and the probabilities are in
[RESULTS.md](RESULTS.md).

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # the full gate battery; must end ALL GREEN
```

```bash
python score.py                # gates x 6 fingerprinted shapes
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py                       # A257466, the default
python launch.py --family A257467
python launch.py --family A258035
```

Each family keeps its own checkpoint under its own config key, and no
campaign will read another's cursor. With the paused campaigns'
checkpoints in place each command resumes at its open term (a(21), a(20),
a(19)); the checkpoints are runtime state and are not in the repository.
Without them a fresh campaign opens at the bottom of its line with the
filter at its lowest *published* open index (16, 15 and 11), classifies
the exception zone on the host, and sweeps — so a fresh clone re-derives
the eighteen terms first, about 39 hours, until they are entered in the
oracle's `FOUND` ([RESULTS.md](RESULTS.md), "What is open now"). A find at the
filter's own index moves the filter to the next open index and carries the
classified line, and a find above the filter is recorded and changes
nothing else. The hunt is indefinite by default, resumable, checkpointed
every segment, and stops cleanly on Ctrl+C with exit 130; on its own it
ends only when the lowest open index passes the last one whose shift is
under the ceiling on the values. `--to` caps the depth,
`--stop-on-discovery` exits once **this run** confirms a find, `--workers`
overrides the pool that is otherwise sized from a measurement at the
campaign's own filter, and `--gentle` yields the device and classifies
inline for a quieter desktop.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle that walks
  residues and tests divisibility, a numpy CPU engine that marks the dense
  line with no wheel at all, and a CuPy engine that generates wheel
  survivors and tests them. G9 pins the GPU stream to the CPU stream bit
  for bit on 29 populated windows (above).
- **Exactness is checked in both directions.** The oracle reads every
  known term's run uncapped and requires exactly its index (G1, G6); the
  protocol drill accepts a genuine term at its true run and rejects the
  same integer claimed one run longer and one run shorter; a discovery is
  re-read by the oracle before it is written and anything but an exact run
  at an unsettled index is an alarm.
- **The small terms are re-derived from nothing.** G2 reads the run of
  every prime below a bound on each line from the bare definition and
  requires the first occurrence of each run length to be the published
  term of that index — and no other run length to occur there.
- **The erratum is a gate, not a remark.** G1 fails unless A258035's two
  listed values have exactly the runs stated above, and G1c fails unless
  the published list is kept verbatim beside the terms this project builds
  on.
- **Canaries meet a later index first, as the campaign will.** From the
  bottom of the line the stream's first prime with a run of at least the
  filter must be the least published term of that index or a later one:
  the end-to-end drills open A257466 at index 12 and find a(13) before
  a(12), open A257467 at index 9 and find a(10) before a(9), and open
  A258035 at index 9 and find a(9) then a(10), each on scratch files with
  the filter promoting itself.
- **The benchmark checks itself.** `SCORE2L` and `SCORE1L` sweep the
  identical absolute window with a two-level and a one-level wheel and must
  return the same 687 survivors and checksum.
- **Every ceiling raises rather than computes**, and the ceiling on the
  values is drilled where it binds: the certificate drill proves values of
  a find's own shape at the last index of each family.
- **The evidence files speak each entry's language** (p, with the shifts
  written pps, psq or pssq), checked by the names drill on every record on
  disk and on the writer's header.
