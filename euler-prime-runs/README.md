# euler-prime-runs

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A164926](https://oeis.org/A164926): the
least prime p such that Euler's polynomial form **x² + x + p** is prime
for exactly n consecutive values x = 0, 1, ..., n−1.

**Results so far: a(17) = 348,284,517,256,411,907,
a(18) = 8,461,068,614,861,832,371, and
a(21) = 234,505,015,943,235,329,417.** a(17) and a(18) were found and
verified 2026-08-05/06, the first new terms of the sequence since
2009; a(21) was settled 2026-08-12 when the exhaustive sweep passed
the known Waldvogel–Leikauf upper bound at 2.35×10²⁰ without finding
a smaller run ≥ 19. Details in [RESULTS.md](RESULTS.md).

**Status: ACTIVE** — phase 1 (the full 64-bit-safe range) is complete;
phase 2, a 128-bit engine targeting a(19) beyond the 1.8×10¹⁹ ceiling,
is gated and hunting (`--engine gpu128`). The sweep is contiguous from
0 to ≈ 2.9×10²⁰, just past the conditional median for a(19)
(≈ 2.6×10²⁰; third quartile 6.8×10²⁰).

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
2. **Stage 1**: survivors are tested against primes 31..1024 with
   forbidden-residue bitmasks in L2 cache. Each GPU thread owns one
   wheel offset across 2048 consecutive periods, stepping its residues
   mod the first 16 primes incrementally (r += M mod q, conditional
   subtract) — the Barrett magic-multiply modulo (no hardware 64-bit
   division; see `../huntlib/gpu.py`) is paid once per prime per 2048
   periods, and again only for the ~0.3% of candidates that survive all
   16. Early exit kills most candidates in ~2–3 tests.
3. **Stage 2**: primes 1024..65536 via direct 17-value divisibility.
4. **Host classification**: the ~3.6×10⁻¹³ of the line that survives is
   handed to the CPU, where a deterministic 7-base Miller–Rabin (valid
   to 3.3×10²⁴) computes each survivor's exact run. The GPU only ever
   *proposes*.

**Phase 2 (beyond the 64-bit ceiling).** Above 1.8×10¹⁹ the candidate p
no longer fits a 64-bit word — but the engines never need it to. Every
candidate is carried as the pair (k, off) with p = k·29# + off, and
every sieve test reduces to
`((k mod q)·(29# mod q) + off mod q) mod q`, which stays 64-bit-safe all
the way to the enforced ceiling 10²⁴ (a factor >3 under the Miller–Rabin
validity bound). The incremental stage-1 residue stepping is unchanged —
it never depended on p's magnitude — and the 128-bit path splits hot and
cold work into two kernels (stage-1a compaction queue + one-candidate-
per-thread cold pass), making it **1.13x faster than the u64 engine
itself** (SCORE128 vs SCORE, same battery). Exact integers exist only on the
host as Python ints. The proven u64 engines are untouched; the 128 path
is pinned against them bit-for-bit on the fingerprint window (G9, G11),
against direct big-integer trial division on mini-windows at 2.35×10²⁰
and the 10²⁴ ceiling (G10), and end-to-end against a(18) and the
Waldvogel–Leikauf run-21 value 234,505,015,943,235,329,417 — the latter
rediscovered *above* the 64-bit cap (G10, G12, and the launcher's
phase-2 canary prelude).

Throughput: **5.1×10¹⁴ integers of p-line per second** end-to-end on an
RTX 4090 (SCORE 512,819,184; see BENCHMARKS.md), height-flat from 10¹⁶
to 1.7×10¹⁹. The full 64-bit-safe range (to 1.8×10¹⁹) took ~9.5 hours
in production.

## The odds model

`euler_model.py` computes the Bateman–Horn prediction with numerically
evaluated singular series (primes to 2×10⁶, tail bounded). Validation:
the six known generic terms a(9)–a(15) sit at model quantiles
.99/.56/.41/.23/.83/.64 — scattered, as an honest model's knowns should
be. Out-of-sample performance so far: a(17) landed at quantile 0.69
(median predicted 2.6×10¹⁷); a(18) landed at quantile 0.63, essentially
exactly at the predicted E = 1 depth (found 8.46×10¹⁸, predicted
8.58×10¹⁸); the run-17 census closed at 8 against an expected 11.6
(within Poisson scatter). The model is two-for-two on out-of-sample
terms.

Predictions for phase 2 (conditional on the empty 64-bit tail for
run ≥ 19, E = 0.20 spent): a(19) median at 2.6×10²⁰, quartiles
8.9×10¹⁹ / 6.8×10²⁰, 48% below the Waldvogel–Leikauf run-21 value at
2.35×10²⁰; a(20) median at ≈ 6×10²¹.

## Running it

```
python launch.py --selftest    # full gate battery + drills (~15 min)
python launch.py               # phase-1 hunt (u64 range; complete)
python launch.py --engine gpu128 --stop-on-discovery
                               # PHASE 2: the a(19) hunt beyond the u64
                               # cap (default depth 3.2e20; halts after
                               # a frontier-extending find)
python launch.py --status      # scoreboard (both phases)
python score.py                # gates x fingerprinted benchmarks (u64 + 128)
python euler_model.py          # rebuild the odds model + its gates
```

`--stop-on-discovery` follows the repo-wide convention (CONVENTIONS.md):
only a run beyond the campaign frontier (currently ≥ 19) halts the hunt;
run-17/18 repeats are verified, evidenced, and counted as census
(`near13-18` in the status line). The known run-21 value at 2.345×10²⁰
was treated as an in-flight canary, not a discovery — rediscovered on
schedule 2026-08-12 and thereby settled as a(21) (see RESULTS.md).

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
