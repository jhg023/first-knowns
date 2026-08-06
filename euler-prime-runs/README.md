# euler-prime-runs

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A164926](https://oeis.org/A164926): the
least prime p such that Euler's polynomial form **x² + x + p** is prime
for exactly n consecutive values x = 0, 1, ..., n−1.

**Result so far: a(17) = 348,284,517,256,411,907** — found and verified
2026-08-05, the first new term of the sequence since 2009. Details in
[RESULTS.md](RESULTS.md).

**Status: ACTIVE** — the production sweep toward the 64-bit cap
(1.8×10¹⁹) is in progress; a(18) is the current target (78% within the
cap). Results and evidence will be extended as the run proceeds.

## The problem

Euler noticed in 1772 that x² + x + 41 is prime for x = 0..39 — forty
primes in a row before 40² + 40 + 41 = 41² breaks the run. Rabinowitsch's
theorem explains the miracle: x² + x + p is prime for all x = 0..p−2
exactly when the field of discriminant 1−4p has class number 1, and by
the Heegner–Baker–Stark theorem there are only nine such discriminants.
So Euler's "lucky numbers" {2, 3, 5, 11, 17, 41} are provably the last
of their kind, and any prime with a long run beyond them is a *generic*
statistical object, findable only by search.

Define run(p) = the number of consecutive x from 0 with x² + x + p prime.
A164926(n) is the least prime with run exactly n. Before this project:
a(1)–a(16) known (a(15) = 291,598,227,841,757, Andersen 2009), then a
17-year gap — **a(17) through a(20) unknown**, with a run-21 example
234,505,015,943,235,329,417 known as an upper bound for a(21) (from a
construction-style search, so not a confirmed least).

There is no known upper bound for a(17)–a(20): every new segment of the
sweep could contain the find. That is what makes it a hunt.

## The mathematics of the engine

A prime p has run ≥ 17 only if none of the 17 values x² + x + p
(x = 0..16) has a small prime factor. For each prime q, the forbidden
residues of p are −(x²+x) mod q — about min(17, (q+1)/2) classes. The
engine:

1. **Wheel**: p is generated only in residues mod 29# = 6,469,693,230
   that survive all wheel primes 2..29 — 3.1×10⁻⁴ of the line.
2. **Stage 1**: survivors are tested against primes 31..1024 by Barrett
   magic-multiply modulo (no hardware 64-bit division; see
   `../huntlib/gpu.py`) with forbidden-residue bitmasks in L2 cache.
   Early exit kills most candidates in ~2–3 tests.
3. **Stage 2**: primes 1024..65536 via direct 17-value divisibility.
4. **Host classification**: the ~3.6×10⁻¹³ of the line that survives is
   handed to the CPU, where a deterministic 7-base Miller–Rabin (valid
   to 3.3×10²⁴) computes each survivor's exact run. The GPU only ever
   *proposes*.

Throughput: **1.9×10¹⁴ integers of p-line per second** end-to-end on an
RTX 4090 (SCORE 189,738,385; see BENCHMARKS.md), height-flat from 10¹⁶
to 10¹⁸. The full 64-bit-safe range (to 1.8×10¹⁹) takes ~26 hours.

## The odds model

`euler_model.py` computes the Bateman–Horn prediction with numerically
evaluated singular series (primes to 2×10⁶, tail bounded). Validation:
the six known generic terms a(9)–a(15) sit at model quantiles
.99/.56/.41/.23/.83/.64 — scattered, as an honest model's knowns should
be. Out-of-sample performance so far: a(17) landed at quantile 0.69, and
the gap to the second run-17 prime was E = 0.72 against a theoretical
median of ln 2 ≈ 0.69.

Predictions: a(18) median at 4.5×10¹⁸ (78% within the 64-bit range);
a(19) median at 1.6×10²⁰ (needs the future 128-bit engine); a(20) at
6×10²¹.

## Running it

```
python launch.py --selftest    # full gate battery + drills (~10 min)
python launch.py               # THE HUNT (checkpointed; resumes)
python launch.py --status      # scoreboard
python score.py                # gates x fingerprinted benchmark
python euler_model.py          # rebuild the odds model + its gates
```

Requires Python 3.12+, numpy, sympy, CuPy + CUDA GPU (or `--engine cpu`).

The launcher preludes every fresh campaign with an exhaustive oracle
sweep of [2, 10⁵) — during which Euler's 41 (run 40) fires the complete
discovery protocol as a positive control — and with mini-hunts that must
rediscover a(14) and a(15) end-to-end before production is allowed to
proceed.

## Trust

This project follows the repository-wide [CONVENTIONS](../CONVENTIONS.md):
three independent implementations (oracle / CPU / GPU) with bit-parity
gates on populated windows up to the 64-bit ceiling, in-stream canaries,
planted-fake and resume drills, and a three-way verification protocol
with factor witnesses on every discovery. See `evidence/` for the
verifiable artifacts.
