# power-ladders — A229626, A229627, A229630 and A229902

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

**Independent mathematical review:** Codex (OpenAI) maintains static
analysis and implementation proposals in [codex-reviews/](codex-reviews/README.md).
These reports follow the repository's [review workflow](../CODEX_REVIEWS.md);
Claude's original implementation and historical records retain their authorship.

A GPU hunt for the next terms of four **power ladders** — one unknown and n
conditions that differ in the EXPONENT. **A229626** asks for the smallest m
such that 2·m^k − 1 is prime for k = 1, 2, …, n; **A229627** for the
smallest prime q such that 2·q^k − 1 is prime for k = 1, 2, …, n;
**A229630** for the smallest semiprime m such that 2·m^k − 1 is prime for
k = 1, 2, …, n; and **A229902** for the smallest m such that 19·m^k + 1 is
prime for k = 1, 2, …, n. They are an October 2013 cluster (Farideh
Firoozbakht, Jahangeer Kholdi, with Giovanni Resta and Charles R Greathouse
IV extending them that month); Tyler Busby took three of them one term
further in January 2023, and A229630 has not moved since 2013. **One term came
free:** A229902's published a(8) = 1,944,616,927,560 has a run of nine
(19·m^9 + 1 is prime; 19·m^10 + 1 is divisible by 23), so it is a(9) as
well, and the first segment of its campaign recorded it (2026-10-22).

**Status: PAUSED — open to others** — nothing is running. One campaign per
family ran between 2026-10-15 and 2026-10-23, 161 hours on the campaigns'
clocks together, and found **eleven terms: a(10) and a(11) of A229626, and
a(9) through a(11) of A229627, of A229630 and of A229902** — the first
advance on A229630 since October 2013 and on the other three since January
2023. Each campaign was stopped by the owner inside the filter for its next
term, so every open index is searched empty to m = 2.7038×10¹⁹ on A229626
(a(12) open), q = 2.8594×10²¹ on A229627 (a(12) open), m = 7.3164×10²⁰ on
A229630 (a(12) open) and m = 2.4285×10²⁰ on A229902 (a(12) open). From
those cursors the model puts A229626's a(12) at 20 days and A229902's at
37 days to their medians at the measured n = 12 rates, and A229630's at
about nine months and A229627's at about four years at their n = 11 rates
([RESULTS.md](RESULTS.md), "What is open now", which also lists what a
resume owes first). The engine is as built and optimized 2026-10-15 to
10-20: 61/61 green, SCORE 2.18×10⁸ — 10⁻⁶ of the m/s at A229626's opening
— on the round-7 engine (BENCHMARKS.md).

## The problem

| entry | name (%N), verbatim | published | frontier | last moved |
|---|---|---|---|---|
| [A229626](https://oeis.org/A229626) `more` | a(n) is the smallest m such that 2*m^k-1 is prime for k = 1, 2, ..., n. | a(1)–a(9) | a(9) = 687,860,415,949 | Tyler Busby, Jan 2023 |
| [A229627](https://oeis.org/A229627) `more` | a(n) is the smallest prime q such that 2*q^k - 1 is prime for k = 1, 2, ..., n. | a(1)–a(8) | a(8) = 1,095,265,755,949 | Tyler Busby, Jan 2023 |
| [A229630](https://oeis.org/A229630) `more` | a(n) is the smallest semiprime m such that 2*m^k-1 is prime for k = 1, 2, ..., n. | a(1)–a(8) | a(8) = 79,235,997,091 | Charles R Greathouse IV, Oct 2013 |
| [A229902](https://oeis.org/A229902) `more` | a(n) is the smallest m such that 19*m^k+1 is prime for k=1, 2,...,n. | a(1)–a(8) | a(8) = 1,944,616,927,560 | Tyler Busby, Jan 2023 |

A229627 carries a comment, "a(9) > 3*10^13. - Tyler Busby, Jan 14 2023";
the campaign does not start from it. Its line starts at a(8), so what it
publishes rests on its own sweep (and a find under the bound would
contradict the comment). A229902's comment "10 divides all terms" is a
theorem from n = 4 on (below).

**The ladders nest.** Every condition of index n is one of index n + 1, so
a(n+1) ≥ a(n), the sweep for a(n+1) starts AT a(n), inclusive, and one
integer can be several terms: A229626's a(1) = a(2) = 2, A229630's a(1) =
a(2) = a(3) = 4, A229902's a(1) = a(2) = a(3) = 10 — and A229902's
a(8) = a(9), which the OEIS does not list. That one rests on Busby's a(8)
being the least with a run of eight, as every extension of a published
term rests on the term below it; the evidence the campaign writes carries
BLS75 certificates for all nine values (the largest 112 digits).

**Which number goes in the OEIS.** The names give the term a letter: m on
A229626, A229630 and A229902, q on A229627. An evidence file carries the
integer under that letter, `forms` reads "2*m^k - 1, k = 1..n" (or
"2*q^k - 1, k = 1..n (q prime)", "2*m^k - 1, k = 1..n (m semiprime)",
"19*m^k + 1, k = 1..n"), and `oeis_terms` is literally what to submit —
`{"10": <integer>}` reads "a(10) is this integer", with several indices
listed when one integer is several terms.

## The mathematics of the engine

**The killed set.** For a sieve prime ℓ not dividing the multiplier, the
k-th condition vanishes mod ℓ exactly when the term's k-th power is minus
the inverse of the multiplier's constant (1/2 on the three ladders of
twice a power less one, −1/19 on A229902) — gcd(k, ℓ − 1) roots when that
residue is a gcd(k, ℓ − 1)-th power, none otherwise. The CPU engine builds
these by ONE discrete logarithm per prime (a primitive root g, then
L = log_g of the target, and the roots are g^t for every t with k·t ≡ L
mod ℓ − 1); the oracle walks every residue and asks sympy's nthroot_mod;
G3 checks both against direct divisibility, and against a brute power walk
on primes to 2²⁰ whose ℓ − 1 is a multiple of lcm(1..12). Two consequences
shape everything:

* **A prime kills about one residue per condition**, not about half its
  residues as on the polynomial runs, so the wheel is weak — the primes to
  59 keep 10⁻³ to 3×10⁻⁵ of the line — and the sieve leaves millions of
  values a second that have no small factor.
* **But up to gcd(k, ℓ − 1) per condition**: 601 kills 41 residues at
  n = 12 of A229626, and the proved bound is n(n+1)/2. The GPU tail's
  residue list is sized per engine from the primes it holds (up to 128
  slots), and the last expressible index is 15.

**The forced classes.** On A229627 the form q itself kills 0 mod 2 and 3,
and 2·q − 1 kills 2 mod 3: q ≡ 1 (mod 6). On A229902, 19·m + 1 is even for
odd m, and 19 ≡ −1 (mod 5) makes the conditions with k = 1, 2, 4 kill all
four nonzero residues mod 5 from n = 4 on: m ≡ 0 (mod 10). A229626 and
A229630 force nothing — 0 and 1 survive every prime, and 2 kills nothing —
so their campaigns sweep the whole line (unit 1). G2c checks it to n = 30.

**The engine** is polynomial-runs' window sieve, taken whole (wheel to 89
in up to three levels; the strongest 100 sieve primes tested 128–256
periods at a time through bit-pattern windows; in-block compaction rounds;
generated tail rounds to 2¹³), with four things of this project's own:

1. **The device Fermat stage.** No sieve depth gets the survivors down to
   what a host can classify (10⁻⁵ of the candidates survive a sieve to 2²⁰
   at ten conditions), but the leading values are small — 2·m − 1 is a
   two-limb number at every frontier this campaign will see. So every
   survivor's leading conditions (q itself on A229627, then k = 1 to 6) are
   Fermat-tested to base 2 ON THE DEVICE, one kernel per condition over the
   compacted queue the previous one left, in multi-limb Montgomery
   arithmetic compiled per limb count. A failed Fermat test is a proof of
   compositeness, so nothing whose leading six conditions are prime is ever
   dropped; the host re-reads every run it receives (1–4 thousand values a
   second, one or two cores).
2. **Queues that cannot overflow as a rule** (STARVE_GUARD, Q3_GUARD): the
   inherited engine treated a full queue as a rare event with a slow
   fallback; the weak sieve made it the norm, at 9 s a launch. Shapes and
   launches are now cut until the mean load fits.
3. **The sieve depth is a device decision** (2¹³ at every opening): with
   the host out of the loop, a tail prime is worth testing only while it
   saves more Fermat work than it costs.
4. **A229630's semiprime domain is in the wheel** (round 5, 2026-10-19). A
   semiprime m divisible by two distinct wheel primes p and q is pq, and
   one divisible by p² is p². So above 89² = 7,921 a semiprime has at most
   one prime factor among the wheel's primes, and the residue classes with
   two or more are never enumerated. 2 joins the wheel for this, since an
   even semiprime is 2p. "At most one" is a union of three products
   (zero counts ≤ 1, 0, 0 / 0, 1, 0 / 0, 0, 1 at the three levels), swept
   as three branches of one segment by the unchanged kernel. At n = 11 they
   keep 24.3% of the classes, and the campaign runs 3.69x the line a second
   (paired) on a segment of the same length. The host still decides the
   domain exactly.
5. **And its cofactor, in the sieve** (round 6, 2026-10-20). A class with
   a wheel prime p dividing m holds m = p·r′, and r′ of a semiprime is a
   prime, so above 89 times the sieve depth no sieve prime divides m
   either. The branches
   whose classes carry a zero therefore kill residue 0 of every sieve prime
   too, in the window, the in-block rounds and the tail. They hold 79% of
   the candidates at n = 11, and the extra kills keep 58% of those through
   the window and 40% of them to the Fermat stage. The zero-free classes
   cannot take the kills, so round 5's first branch is split in two: four
   branches, the kernel still untouched, 1.30x the line a second at n = 11
   (paired), on the same period and segment.

OPTIMIZATION_LOG.md has every measurement, from 6.4×10⁹ candidates a
second on the first read to 5.8×10¹¹.

**The ceiling and the proofs.** The term is bounded by huntlib's
K_CEIL = 10⁴⁰. Every value is the multiplier times a power of the term,
plus or minus one, so the value plus one (2·m^k, 2·q^k) or minus one
(19·m^k) is COMPLETELY factored by one factorization of the term: BLS75
Theorem 15 on the three 2·m^k − 1 and 2·q^k − 1 ladders, Theorem 1 on
A229902, at any height and any k — rule 5h's best case. The deterministic
Miller–Rabin bound is passed by the k = n value at a few hundred (m = 265 at
n = 10), so every campaign classifies on a strong probable-prime chain and
every discovery's values are proved by certificate before they are
written; A229627's q past 3.3×10²⁴ gets a subproof of its own.

## The odds model

Bateman–Horn over the conditions of each index, with the singular series
computed from the sieve's own killed sets (power_model.py): the k-th
condition contributes 1/ln(multiplier · term^k), A229627's q itself a
1/ln q, and A229630's semiprime m a density ln ln m / ln m. **Validation
(G11)**: at the 16 published terms that were searched for, E sums to 12.03
against a Gamma(16, 1) law (P = 0.158; per family A229626 0.89 over 4,
A229627 0.65 over 5, A229630 0.93 over 3, A229902 0.60 over 4) — published
terms have tended to come early, not late. Predictions, stated before any
run (model_results.json), with the expected clock to the median at the
campaign's measured rate at that filter:

| term | Q1 | median | Q3 | P90 | rate at the filter | clock to the median |
|---|---|---|---|---|---|---|
| A229626 a(10) | 3.1×10¹⁵ | 1.0×10¹⁶ | 2.7×10¹⁶ | 5.5×10¹⁶ | 2.4×10¹⁴ m/s | 44 s |
| A229626 a(11) | 1.3×10¹⁸ | 4.3×10¹⁸ | 1.1×10¹⁹ | 2.2×10¹⁹ | 5.0×10¹⁴ m/s | 2.4 h |
| A229626 a(12) | 7.6×10²⁰ | 2.5×10²¹ | 6.2×10²¹ | 1.2×10²² | 1.54×10¹⁵ m/s | 19 days (P90 90) |
| A229627 a(9) | 3.9×10¹⁵ | 1.3×10¹⁶ | 3.5×10¹⁶ | 7.0×10¹⁶ | 2.7×10¹⁵ q/s | 5 s |
| A229627 a(10) | 2.1×10¹⁸ | 7.1×10¹⁸ | 1.8×10¹⁹ | 3.6×10¹⁹ | 8.5×10¹⁵ q/s | 14 min |
| A229627 a(11) | 1.0×10²¹ | 3.3×10²¹ | 8.2×10²¹ | 1.6×10²² | 1.7×10¹⁶ q/s | 2.3 days (P90 11) |
| A229630 a(9) | 1.5×10¹⁴ | 5.3×10¹⁴ | 1.4×10¹⁵ | 2.9×10¹⁵ | 6.6×10¹³ m/s | 8 s |
| A229630 a(10) | 7.7×10¹⁶ | 2.6×10¹⁷ | 6.8×10¹⁷ | 1.4×10¹⁸ | 2.4×10¹⁴ m/s | 19 min |
| A229630 a(11) | 3.6×10¹⁹ | 1.2×10²⁰ | 3.0×10²⁰ | 5.9×10²⁰ | 3.1×10¹⁵ m/s (cofactor sieve, aligned window read; semiprime wheel 2.25×10¹⁵, v1 5.0×10¹⁴) | 11 h (P90 2.2 days) |
| A229902 a(9) | = a(8) | | | | | the first segment |
| A229902 a(10) | 3.6×10¹⁶ | 1.2×10¹⁷ | 3.0×10¹⁷ | 5.8×10¹⁷ | 1.2×10¹⁵ m/s | 95 s |
| A229902 a(11) | 1.3×10¹⁹ | 4.3×10¹⁹ | 1.1×10²⁰ | 2.1×10²⁰ | 2.7×10¹⁵ m/s | 4.4 h |
| A229902 a(12) | 4.3×10²¹ | 1.4×10²² | 3.4×10²² | 6.6×10²² | 4.6×10¹⁵ m/s | 35 days (P90 168) |

So: about nine terms in the first day of the four campaigns together, two
more (A229627 and A229630's a(11)) in the following days, and the a(12)s
of A229626 and A229902 at weeks. The term after those (a(12) of A229627 and
A229630, a(13) of the others) is years at these rates. The model has run
early and late elsewhere in this repository (mean E 0.70 to 1.62 across
the last three projects): read the quantile table, not the median.

**What the campaigns did against this table** is in
[RESULTS.md](RESULTS.md), "The finds against the model": the ten searched
finds scored a mean E of 1.03 (their sum, 10.26, sits at the 57th
percentile of Gamma(10, 1)), with A229630's a(9) at the 0.6th percentile
of its row and the a(11)s of A229626 and A229630 at the 93rd; A229902's
a(9) was the free term.

## Running it

Requirements: an NVIDIA GPU with CuPy (developed on an RTX 4090, CUDA 13,
CuPy 14), Python 3.12+, numpy, sympy (gmpy2 recommended).

```
python launch.py                       # the hunt: A229626, indefinite, resumable
python launch.py --family A229627      # 2*q^k - 1, q prime
python launch.py --family A229630      # 2*m^k - 1, m semiprime
python launch.py --family A229902      # 19*m^k + 1 (its first segment records a(9) = a(8))
python launch.py --status [--family F] # where the cursor is; reads, never writes
python launch.py --selftest            # the full battery (61 checks, ~4 min warm)
python score.py                        # gates x fingerprinted benchmark (~2.5 min warm)
```

Each family has its own checkpoint and ledger and one campaign runs at a
time. Throttles, each priced in `--help`: `--workers`, `--gpu-yield-ms`,
`--gentle`. **The first battery after a kernel change compiles every
configuration once** (NVRTC; the generated tail rounds take ~20 s a
thousand literal primes) and can run several minutes longer than the warm
figures above. The acceptance test of CLAUDE.md 5g — each family started
fresh with no flags, its first `[STATUS]` lines read for the pool, the
rate and the rung — is the owner's to run, being a campaign start.

## Trust

The repository's machinery is described in [CONVENTIONS.md](../CONVENTIONS.md):
an oracle in sympy (power_reference.py), a CPU engine marking a dense line
(power_search.py), the GPU engine pinned to it bit for bit on populated
windows at every height to the 10⁴⁰ ceiling (G9 — including the plain
window table every campaign filter runs, read at each alignment), frozen
benchmark fingerprints, canaries that must rediscover published terms in
every family, a three-way discovery protocol with a factor witness for the
value that stops each run, and BLS75 certificates for every value of a
discovery, re-verified before they are written. What is this project's:

* **The device Fermat stage can only drop composites**, and G23 pins it:
  its verdicts equal Python's `pow(2, N − 1, N) == 1` on 16,007 values at
  2–17 limbs and heights to 10³⁹, every published term passes every
  condition of its run, the base-2 pseudoprimes 341, 561 and 2047 pass (so
  the host's re-reading is load-bearing) and its stream equals the CPU
  sieve's survivors filtered by a CPU Fermat chain on six windows.
* **The kill sets are built four ways** (residue walk, nthroot_mod,
  discrete logarithm, brute power walk) and agree everywhere they are
  compared (G2b, G3).
* **A229630's semiprime domain** is decided exactly on the host (huntlib's
  bounded split, then the cube-root argument, then factorint) wherever a
  run reaches the census floor, and every A229630 evidence file carries the
  term's two prime factors. The wheel only drops classes no semiprime above
  7,921 can be in, and the cofactor sieve only m that no semiprime above
  89 times the sieve depth can be (a wheel prime and a sieve prime both
  dividing it). G24a checks both theorems on every semiprime to 2×10⁵, and
  that each floor is needed. G24 pins the branches' stream to the CPU
  engine's survivors filtered by both conditions, every one once, the
  second removing some on every window. The engines never sweep below the
  larger floor on A229630 (89 × 8,192 = 729,088 at the campaign's depth):
  the host covers that zone.
* **The free term** A229902 a(9) = a(8) rests on Busby's a(8) being the
  least m with a run of eight; the campaign re-derives the run and proves
  every value, but does not re-sweep below a(8).
