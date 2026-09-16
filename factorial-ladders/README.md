# factorial-ladders — A177013, A177014, A226935

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

A GPU hunt for the next terms of three OEIS sequences that ask the same
question twice, with the sign flipped: **what is the smallest m for which
every one of k!·m ∓ 1, k = 1..n, is prime?** Both frontiers are the ten
terms Enoch Haga and Farideh Firoozbakht entered in May 2010; neither carries
a bound at any open index, neither has a b-file, and the third entry — the
chain of primes p(i) = i·p(i−1) − (i−1), which unrolls to i!·(p−1) + 1 — has
never been extended. The forms are the linear ladder this repository has
hunted five times, with the multiplier list swapped to the factorials, and
the published term is m itself: one line, no substitution, a wheel that
grows with n.

**Status: ACTIVE** — the engine, the gate battery and the campaign are
built and green; no term has been hunted yet.

## The problem

| entry | definition | terms | frontier | last moved |
|---|---|---|---|---|
| [A177013](https://oeis.org/A177013) | least m with k!·m − 1 prime for k = 1..n | 10 | a(10) = 3,240,034,842 | Haga & Firoozbakht, May 2010 |
| [A177014](https://oeis.org/A177014) | least m with k!·m + 1 prime for k = 1..n | 10 | a(9) = a(10) = 228,698,250 | Haga & Firoozbakht, May 2010 (a(10) corrected by Jon E. Schoenfield, 2018) |
| [A226935](https://oeis.org/A226935) | least prime p(1) with p(i) = i·p(i−1) − (i−1) prime for i = 1..n | 10 | = A177014 + 1 | never extended (Robin Garcia, 2013) |

The third is a rider: p(i) = i!·(p − 1) + 1 by induction, so its chain is
prime exactly when m = p − 1 satisfies A177014's condition, and the least
such p is the least such m plus one (`fladder_reference` G2d re-derives this
by running the recurrence on every published term). **So a find on A177014
settles two entries.** A177013 has no rider: nobody has entered the chain
p(i) = i·p(i−1) + (i−1).

a(11) is open on all three. The conditions nest — anything satisfying filter
n satisfies filter n − 1 — so a(n) is non-decreasing and the previous term
is a free floor; nothing below it has to be swept at all.

## The mathematics of the engine

**The killed set.** For a prime q and a multiplier k!: if k ≥ q then q | k!
and the form k!·x + s ≡ s (mod q) is never divisible by q. For k < q it is
divisible exactly when x ≡ −s·(k!)⁻¹ (mod q). So q kills

    K(q,n) = { −s·(k!)⁻¹ mod q : 1 ≤ k ≤ min(n, q−1) }

and its size w(q,n) is the number of *distinct* residues among
1!, …, min(n, q−1)! mod q. There is no closed form: consecutive factorials
collide whenever a product of consecutive integers is 1 mod q, and they do
so often — only 5 of 1!..10! are distinct mod 11, 9 of 1!..12! mod 13, 12 of
1!..17! mod 31. G2b pins the count three ways (the bounded count, the
distinct-multiplier count, direct divisibility) at every prime under 90 and
every n to 43.

**Only 2 and 3 are ever forced.** w(2,n) = 1 and w(3,n≥2) = 2, so every term
from a(2) on is a multiple of 6 outside the exception zone. For q ≥ 5
Wilson's theorem gives (q−2)! ≡ 1 ≡ 1! (mod q), so two factorials share a
residue and w(q,n) ≤ q − 2: **no larger prime is forced at any n**. The unit
is 6 for the whole hunt (G2c checks it to n = 44 and q < 200), which is the
opposite of the lcm ladders' sporadic forcing — and the engines still derive
it per filter and refuse anything else, because a unit is a coverage claim.

**Saturation, and why a shorter sieve finds a longer run.** K(q,n) ⊆
K(q,n+1), with equality from n = q − 1 on. So the filter-n sieve keeps a
superset of what the filter-(n+1) sieve keeps, and an x whose run passes
the filter — a *rider* — is found by the shorter sieve and settles every
term up to its run at once. The launcher decides riders by running the
chain on, by the oracle's definition, before anything is claimed.

**One line.** The published term is x, so a find at filter n is the floor
of filter n + 1 with no re-denomination. What changes at a promotion is the
plan: a larger kill set, the wheel the period cap admits, the sieve depth.
The engine is rebuilt; the new filter's claim starts at the find and its
sweep resumes at the end of the line the old filter classified — every
survivor of a closed segment was run to n + 8, and the new filter's sieve
keeps a subset of the old one's survivors, so nothing below that line can
be the next term without having been found already (`_promotion_drill`).

**The wheel is planned per filter, and it is short at the opening.** Each
wheel prime multiplies the period by q and the candidate density by
keep(q) = (q − w)/q; the planner takes primes by value density
−log(keep)/log(q) while the period fits every bound — including the
search: a find is only known to be the least once its segment closes, so
the segment may not exceed a quarter of the modelled median. At n = 11 the
median is 3e10 and the wheel stops at {5..23, 31}; from n = 16 the full
wheel {5..47} at unit 6 fits (period 6.1e17), and the reduction bound then
cuts the window to 179 periods. That bound is 2^64 — the word — and not
the 2^63 the engine shipped with: the one-conditional-subtraction Barrett
step is exact for every u64 (a paper bound and a bit-exact emulation with
a tripwire, G19), and the window it had been hiding is worth 1.19x at
n = 17 (OPTIMIZATION_LOG.md round 2).

**The engine.** Candidates are carried as (x, off) pairs, so no machine word
bounds the search. The GPU never materialises the x line: it generates the
residues of a three-level wheel and sieves them a segment of periods at a
time, testing each sieve prime against a periodic bit pattern, then
compacts the survivors through in-block rounds and global tail rounds. The
CPU engine marks arithmetic progressions into a dense array and uses no
wheel at all; the parity gate (G9) pins the two streams bit for bit on 22
populated windows from x = 2e9 up to the 1e40 ceiling. The kernel is
lcm-ladders' v1 unchanged (engine v2 here: the 2^64 bound, the window at
it, and a queue margin chosen against the occupancy actually reached);
every constant was re-swept at this project's window in
OPTIMIZATION_LOG.md round 2 and none moved.

**The ceiling is 1e40 on x, and certificates are this project's best case.**
Value k is k!·x + s, so (k!·x + s) − s = k!·x with k! k-smooth: **one
factorization of x proves the entire run**, by BLS75 Theorem 1 on V − 1 for
A177014 and Theorem 15 (a Lucas sequence per prime) on V + 1 for A177013.
The proof crossing — where a *classification* stops being a deterministic
proof — is very low here, x = 8.3e16 at n = 11, 2.5e12 at n = 15, 9.3e9 at
n = 17 and x = 1 from n = 25 (25! alone exceeds the Miller–Rabin bound), so
the certificate is the path from the first minutes. The ceiling is where its
*cost* was measured (`huntlib.ceiling`), not where the arithmetic runs out.

## The odds model

Bateman–Horn over the n linear forms, with the singular series computed from
the same w(q,n) the sieve is built from — so a wrong w would move the model
and the engine together, and the validation would catch it.

**Validation (G11), stated before the run.** E — the expected number of hits
the model puts between the previous term and the one that actually occurred
— must scatter around 1 on the knowns. Over the 8 independently-searched
terms (riders excluded: one vote per condition, from n = 6) the mean is
**1.20**, spread 0.10–2.51: A177013 0.80 over 4 draws, A177014 1.61 over 4.

**The series is large.** S(15) = 2.1e8, above even the lcm ladders' 1.3e8,
because w(q,n) ≤ min(n, q−1) with the collisions making it strictly less at
the primes just above n; G12 asserts the ordering against the linear law on
the same primes (a theorem) rather than a band around a number, and the
growth of S with n by its mechanism (every q ≤ n + 1 keeps its kill set and
contributes q/(q−1)).

**Predictions, in x = the published term** (`model_results.json`). Read
them as a floor: the ladder projects before this one landed their finds at
about 1.9–2.5× their medians while every census showed the intensity right
to a percent or two.

| term | Q1 | median | Q3 | P90 | proof crossing |
|---|---|---|---|---|---|
| a(11) A177013 | 1.30e10 | **3.37e10** | 8.30e10 | 1.69e11 | 8.3e16 |
| a(11) A177014 | 6.51e9 | **2.40e10** | 6.92e10 | 1.51e11 | 8.3e16 |
| a(12) | 3.4e11 | **1.3e12** | 3.6e12 | 7.8e12 | 6.9e15 |
| a(13) | 1.3e13 | **4.9e13** | 1.4e14 | 3.0e14 | 5.3e14 |
| a(14) | 5.1e14 | **1.9e15** | 5.3e15 | 1.1e16 | 3.8e13 |
| a(15) | 1.7e16 | **6.2e16** | 1.7e17 | 3.5e17 | 2.5e12 |
| a(16) | 8.7e17 | **3.1e18** | 8.4e18 | 1.7e19 | 1.6e11 |
| a(17) | 4.1e19 | **1.4e20** | 3.8e20 | 7.8e20 | 9.3e9 |
| a(18) | 1.7e21 | **6.0e21** | 1.6e22 | 3.2e22 | 5.2e8 |
| a(19) | 8.0e22 | **2.8e23** | 7.2e23 | 1.5e24 | 2.7e7 |
| a(20) | 5.3e24 | **1.8e25** | 4.7e25 | 9.4e25 | 1.4e6 |

(From a(12) on the two families' quantiles agree to three figures, the
floors being negligible against the depths.)

At the measured rates (BENCHMARKS.md, OPTIMIZATION_LOG.md round 2)
a(11) through a(15) are seconds of device each, a(16) is about **30
seconds** of line (one segment of 18 minutes, which the next filter
inherits), a(17) about **14 minutes** and a(18) about **7 hours** at the
medians — per family. So a night reaches a(17) on both, about 2.5× that at
the optimism factor the repository's earlier ladders suggest budgeting,
with a(18) a day each and a(19) (2.8e23 at 2.3e17 x/s: two weeks) the long
leg.

## Running it

```bash
python launch.py --selftest     # the full battery -- must end ALL GREEN (~4 min)
python score.py                 # gates x eight fingerprinted benchmarks (~4 min)
python launch.py --status       # where the cursor is; reads, never writes
```

The hunt itself, which is the owner's command and nobody else's:

```bash
python launch.py                        # A177013, indefinite, resumable
python launch.py --family A177014       # the other family
python launch.py --family A226935       # the rider spelling: opens A177014
python launch.py --to 1e20              # stop at a chosen depth in x
python launch.py --stop-on-discovery    # stop when THIS RUN finds something
```

One campaign per family, each with its own checkpoint and ledger. Runs
indefinitely by default, to the 1e40 ceiling. Requires CuPy and a CUDA GPU;
sympy and numpy for the oracle and the CPU engine.

## Trust

The gate discipline is [CONVENTIONS.md](../CONVENTIONS.md); the optimization
process is [OPTIMIZATION.md](../OPTIMIZATION.md). Specific to this project:

* **The rider identity is gated, not quoted.** G2d runs A226935's own
  recurrence from m + 1 on every published term, requires every link prime
  and equal to i!·m + 1, and checks the least-claim exhaustively at n = 4
  and 6.
* **The unit is derived and refused.** `assert_unit` raises on a unit whose
  primes are not forced at the filter *or which is not squarefree* (forcing
  says 2 | x, never 4 | x); G3, G7 and the ceiling drill require 30, 10, 12
  and 30030 to be refused at every filter.
* **Four wheels, one stream.** G17 sweeps one whole period of the unit-6
  wheel to 43 with that wheel, the same primes split at a different level,
  a coarser wheel that covers the window in 43 of its own periods, and an
  x-space wheel — and requires the identical survivor set.
* **A hazard the gates caught while this project was being built.** At the
  opening filter the period cap leaves a short wheel, and the level
  splitter returned it as (5..23), (), (31): an empty second level with a
  non-empty third, which the engine would have dropped from the wheel *and*
  left out of the sieve, so 31 would have gone untested. G13, which builds
  every planned wheel level by level, failed on the raw shape; the splitter
  now normalises it.
