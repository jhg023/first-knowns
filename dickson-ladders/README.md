# dickson-ladders

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A247965](https://oeis.org/A247965): the
least k such that **m·k² + 1 is prime for every m = 1, 2, …, n**. The
sequence is `nonn,hard,more`; its last computational advance was in
**October 2014**, and the four terms this project targets — a(10) through
a(13) — have never had an upper bound published for them.

**Status: ACTIVE** — the engine is built, gated and benchmarked; the
first production leg has not been started yet (hunts are started
deliberately by the repository owner, never by an agent). The standing
frontier is still where Hiroaki Yamanouchi left it in 2014:
**a(9) = 3,332,396,388,090**, with a(10) > 1.54665×10¹³ and
a(11) > 1.076691×10¹⁴. The model puts a(10) at median 1.68×10¹⁵ — about
**4 minutes** at the measured line rate — and a(11) at 7.18×10¹⁶, about
3 hours. Predictions are stated in full below *before* the run, which is
the only time they are worth anything.

## The problem

Michel Lagneau proposed the sequence in September 2014; Derek Orr and
Michel Marcus filled in the small terms within days, and Hiroaki
Yamanouchi computed a(7)–a(9) and the two lower bounds on October 1,
2014. Nothing computational has happened to it since — the only edits in
the eleven years after are editorial.

| n | a(n) |
|---|------|
| 1 | 1 |
| 2 | 1 |
| 3 | 6 |
| 4 | 3,240 |
| 5 | 113,730 |
| 6 | 30,473,520 |
| 7 | 3,776,600,100 |
| 8 | 16,341,921,960 |
| 9 | 3,332,396,388,090 |
| 10 | **> 15,466,500,000,000** (open) |
| 11 | **> 107,669,100,000,000** (open) |
| 12, 13 | **open, no bound published** |

Why it is open rather than solved: a k that works for n must make n
distinct quadratic forms simultaneously prime, and even the n = 1 case —
are there infinitely many primes of the form k²+1? — is Landau's fourth
problem, open since 1912. Nobody can prove a(10) exists. Dickson's
conjecture says it does, Bateman–Horn says roughly where, and the only
way to find it is to sweep. That is the same bargain as the sibling
project in this repository: **a find confirms the conjecture, never
refutes it**, and every window swept could contain it.

The published bounds are *lower* bounds — searched-and-empty ranges, not
ceilings. There is no depth at which the hunt is guaranteed to end.

## The mathematics of the engine

**1. The wheel is forced, and it is enormous.** For a prime q ≤ n+1 and
a k not divisible by q, the residue u = −k⁻² mod q is one of
1, …, q−1 ⊆ {1, …, n}, so the value u·k²+1 is divisible by q — composite
as soon as it exceeds q. Every candidate is therefore a multiple of

  W(n) = product of the primes q ≤ n+1  (2310 at n = 10, 30030 at n = 12)

and the search line is 1/2310 as long as it looks. Every published term
above the floor sits on its wheel; **G1** checks that rather than
assuming it. (The exception zone is real: a(1) = a(2) = 1 works because
1·1+1 *is* the prime 2. The engines refuse to run below k = 10⁴ and the
oracle owns everything under it.)

**2. Representation: (W, j), never k.** A candidate is the pair (W, j)
with k = W·j. The value k passes 2⁶⁴ around a(12) and the *values*
m·k²+1 pass it before a(8) — but no engine ever forms either. Every
sieve test needs only

  k mod q = ((W mod q) · (j mod q)) mod q

and j stays inside u64 to the enforced ceiling (4×10¹⁸, i.e. k up to
9.2×10²¹ on the 2310 wheel). One engine spans the whole range; there is
no second engine waiting at the machine-word boundary, which is
[OPTIMIZATION.md](../OPTIMIZATION.md) §2.7 applied at the start of a
project instead of after it hurts.

**3. The sieve.** For a prime q > n+1 the killed residues of k are the
roots of k² ≡ −1/m (mod q) over m = 1..n: two roots for each m with
(−m|q) = +1, disjoint across m, so exactly 2·#{m ≤ n : (−m|q) = +1} of
them. The two engines exploit that fact in deliberately different ways —

- the **CPU engine** (`ladder_search.py`) builds the root table with
  sympy's `sqrt_mod`, converts it to j-residues, and marks arithmetic
  progressions with numpy slice strides;
- the **GPU engine** (`ladder_gpu.py`) builds **no table at all**. Per
  candidate it computes t = k² mod q by Barrett reduction and then walks
  r ← r + t from r = t+1, n times, killing on r = 0. That walk is
  m·k²+1 mod q for m = 1..n with no multiplication and no memory traffic
  beyond (q, magic, W mod q).

They share no subroutine, so **G6** — bit-for-bit parity on populated
windows from j = 10⁶ up to the enforced ceiling — is a real check rather
than a tautology.

**4. Host classification, designed cheap on day one.** Survivors are
classified by run length with a strong-probable-prime chain that tests
m = 1 first and stops at the first composite; 61% of survivors die on
the first test. The sibling project learned the hard way that a fast
kernel turns the host into the bottleneck (its host share went from 2%
to 52% while nobody was watching), so this one measures the split from
the first commit — see [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

**5. Certificates, because this problem hands them over.** The values
m·k²+1 pass huntlib's deterministic Miller–Rabin bound (3.317×10²⁴)
*before a(9)*, so probable-prime tests are evidence and not proof. But
N − 1 = m·k² is our own number: factor m and k and the factorization is
complete, which is exactly what Brillhart–Lehmer–Selfridge Theorem 1
needs. Every claimed find therefore carries a **primality certificate**
for all n of its values — a per-factor witness set, re-verified from
scratch by the evidence checker — instead of a probable-prime assertion.

The other half of a least-claim never needed certificates: a candidate is
rejected because a small prime divides one of its values (a proof) or
because a strong test fails (also a proof). So "this is the least k"
rests on rigorous ground for the whole swept range, and "these n values
are prime" rests on certificates. **G11** drills the verifier with a
forged witness and a falsified factorization; both must be rejected.

## The odds model

`ladder_model.py` computes the Bateman–Horn prediction with a
numerically evaluated singular series (primes to 2×10⁶, tail bounded),
using two closed forms for the killed-residue count w_q that **Z4** pins
against the oracle's direct divisibility count at every prime below 400.

Validation, on the six known terms it did not help find — their expected
counts at the true a(n) should scatter around 1, and do:

| a(4) | a(5) | a(6) | a(7) | a(8) | a(9) |
|------|------|------|------|------|------|
| E = 1.07 | 1.01 | 1.05 | 2.15 | 0.39 | 0.69 |

**Predictions, stated before the run** (first occurrence, so
P(a(n) > K) = e^(−E); conditional on the published searched-empty range
where one exists):

| term | Q1 | **median** | Q3 | P90 |
|------|----|-----------|----|-----|
| a(10) | 5.22×10¹⁴ | **1.68×10¹⁵** | 4.33×10¹⁵ | 8.67×10¹⁵ |
| a(11) | 2.12×10¹⁶ | **7.18×10¹⁶** | 1.88×10¹⁷ | 3.78×10¹⁷ |
| a(12) | 5.33×10¹⁸ | **1.83×10¹⁹** | 4.75×10¹⁹ | 9.51×10¹⁹ |
| a(13) | 6.34×10²⁰ | **2.14×10²¹** | 5.50×10²¹ | 1.09×10²² |

At the v1 line rate (6.54×10¹² k/s at n = 10, 8.78×10¹³ k/s at n = 12 —
see [BENCHMARKS.md](BENCHMARKS.md)) that is **4.3 minutes to the a(10)
median, 3.1 hours to a(11), 2.4 days to a(12)**. a(13) is out of reach
for the v1 kernel at ~9 months, and closing that gap is the whole
optimization brief in [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

## Running it

```
python launch.py --selftest    # full gate battery + drills
python launch.py --stop-on-discovery
                               # THE HUNT: resumes at the frontier,
                               # halts after a frontier-extending find
python launch.py --status      # scoreboard
python score.py                # gates x fingerprinted benchmarks
python ladder_model.py         # rebuild the odds model + its gates
```

The launcher preludes every fresh campaign with an exhaustive oracle
sweep of [1, 10⁴) — which must return a(1)–a(4) and nothing else — and
then makes the production engine **rediscover a(7), a(8) and a(9)
end-to-end as first occurrences**, sweeping from the floor. A stream that
cannot find what is known does not get to report what is not.

`--stop-on-discovery` follows the repo-wide convention: only a run beyond
the campaign frontier (currently ≥ 10) halts the hunt. Once a term is
settled it joins `CAMPAIGN_FOUND` in the launcher, and further k with
that run length are verified, evidenced and counted as census rather than
stopping a leg.

Requires Python 3.12+, numpy, sympy, CuPy + CUDA GPU (or `--engine cpu`,
which is the gating reference and orders of magnitude too slow to hunt
with).

## Trust

This project follows the repository-wide
[CONVENTIONS](../CONVENTIONS.md): three independent implementations
(oracle / CPU / GPU) with bit-parity gates on populated windows up to the
enforced ceiling, canary rediscoveries that must fire before production
runs, planted-fake drills in both directions, and a discovery protocol
whose every claim is checkable from the evidence file alone.

Project-specific: because the values outgrow deterministic Miller–Rabin
early, this hunt's evidence carries **primality certificates** rather
than probable-prime claims, and the certificate verifier is itself
drilled with forgeries (**G11**). See `evidence/` for the artifacts.
