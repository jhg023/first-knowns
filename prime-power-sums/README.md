# prime-power-sums

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line of it — the engines, the CUDA kernels, the verification
> machinery, the documentation, including this README — was authored by
> **Claude (Anthropic's AI)**, working at my direction. My contributions are
> the goals, the hardware, and the decisions between runs.

A single contiguous sweep of the prime line that hunts **seven open OEIS
sequences at once** — fourteen counting their prime-reported partners —
by asking, for each power *m*, which indices *k* divide the sum of the
*m*-th powers of the first *k* primes. The frontiers are held by two
amateurs working on CPUs, and their own published bounds show where a GPU
should be able to take the problem from them: 6.5×10¹⁵ at *m* = 1, where
the running sum fits in 128 bits, against 5×10¹⁴ at *m* ≥ 8, where it does
not.

**Status: ACTIVE** — no results yet, and **the campaign is now
startable**. The mathematics, the four implementations, the odds model and
the full gate battery are built and green at **SCORE 58,754** (v1 scored
95); the v2 engine measures **3.3×10¹⁰ p/s at campaign height**, against
v1's 3.3×10⁷ there, which turns the nearest target from 8.7 years into
about eleven days and reaches new ground on five families in six. The
optimization pass and everything it rejected are in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md); the rates and what they cost
the campaign are in [BENCHMARKS.md](BENCHMARKS.md). Starting the hunt is
the owner's call, not the pipeline's.

## The problem

For a power *m* and an offset *e* ∈ {0, 1}, let

    S(m, k) = prime(1)^m + prime(2)^m + ... + prime(k)^m

and ask for the *k* with **k | e + S(m, k)**. Each such *k* is a term of
two published sequences at once — one listing the index *k*, one listing
prime(*k*) — and for *m* = 1 of four.

The seven target families, their frontiers, and who holds them:

| m | index seq | prime seq | terms | frontier *k* | held by |
|---|-----------|-----------|-------|--------------|---------|
| 1 | [A045345](https://oeis.org/A045345) `nice` | [A171399](https://oeis.org/A171399) | 16 | 6.5×10¹⁵ | Paul W. Dyson, Sep 2022 |
| 7 | [A125826](https://oeis.org/A125826) `hard` | [A232865](https://oeis.org/A232865) | 19 | 1.26×10¹⁵ | Paul W. Dyson, Jan 2024 |
| 9 | [A131263](https://oeis.org/A131263) | [A232962](https://oeis.org/A232962) | 13 | 5×10¹⁴ | Paul W. Dyson, Dec 2024 |
| 11 | [A125827](https://oeis.org/A125827) `hard` | [A233192](https://oeis.org/A233192) | 18 | 5×10¹⁴ | Paul W. Dyson, Dec 2024 |
| 13 | [A131273](https://oeis.org/A131273) | [A232770](https://oeis.org/A232770) | 13 | 5×10¹⁴ | Paul W. Dyson, Dec 2024 |
| 17 | [A131277](https://oeis.org/A131277) | [A233555](https://oeis.org/A233555) | 19 | 6.29×10¹⁴ | Paul W. Dyson, Sep 2023 |
| 19 | [A131279](https://oeis.org/A131279) | [A233767](https://oeis.org/A233767) | 26 | 5×10¹⁴ | Paul W. Dyson, Dec 2024 |

A term of *m* = 1 also extends [A050247](https://oeis.org/A050247) (the sum
itself) and [A050248](https://oeis.org/A050248) (its integer average).

**Why it is open, and why it is a hunt rather than a race.** Nothing
bounds any term from above: every family carries only lower bounds, so
every swept window could hold the next find. The published frontiers are
where two people stopped, and they are recent — Dyson's most recent move
on *m* = 11 was 31 Dec 2024, its partner updated 16 Jan 2025 — which makes
this a **contested** frontier rather than a stale one, and the reason to
take it is arithmetic width rather than being first to look.

**A published value this project does not believe.** The two tables of a
family must satisfy A233555(*n*) = prime(A131277(*n*)), and across all
seven families that ratio behaves — except at *n* = 18, where A233555 lists
1701962315686097 against an expected ≈1.157×10¹⁵. That value is exactly
prime(5×10¹³), i.e. the family's own `a(19) > 5*10^13` search limit; it
looks like a limit entered where a term belongs. The project does not edit
OEIS: it excludes the value from the checks it would fool, pins it with a
gate (oracle G1c) so a silent future correction breaks the battery instead
of drifting, and notes that the *m* = 17 sweep passes *k* = 3.44×10¹³ in
its first hours and produces the correct value as a by-product.

## The mathematics of the engine

**The obstruction, and the wheel it gives.** Let *q* be a prime with
(*q*−1) | *m*. Fermat gives *p*^*m* ≡ 1 (mod *q*) for every prime *p* ≠ *q*,
so once *q* is itself among the first *k* primes,

    S(m, k) ≡ k − 1   (mod q)      for all k ≥ pi(q).

For *e* = 0 a term needs S ≡ 0 (mod *k*), so **no *k* divisible by such a
*q* can ever be a term**: the terms live on the *k* coprime to
Q(*m*) = ∏{*q* : (*q*−1) | *m*}. That is a wheel on the index line (half
the indices at *m* = 11, four fifths at *m* = 12), it explains why every
known term of A045345 is odd, and it is proved against the definition in
the oracle's G3 rather than assumed.

**The sweep.** The engine walks the prime line in segments, carrying
`(p, k, sums)` — the line position, how many primes have been consumed,
and the exact S(*m*, *k*) for each *m*. That state is the whole cursor:
hand it to a checkpoint or to the other engine and the sweep resumes
bit-for-bit. There is a sublinear way to compute S at a height without
walking there (a Lucy_Hedgehog-style prefix recurrence) and it is
deliberately not used — the run-up below the lowest live frontier is 0.1%
of the campaign, and walking it makes the engine rediscover **124
published terms** on the way, which is the canary battery for free.

**On the device (v2).** A prime's whole journey — *p*^*m* for all eight
families, the running prefix, and the test — happens in registers inside
one kernel; nothing is ever materialised. Four things make that work:

- **The source is generated per run.** Family (*m*, *e*) gets exactly
  ⌈(*m*·log₂ p_hi + log₂ k_hi)/32⌉ words and *p*^*j* exactly
  ⌈*j*·log₂ p_hi/32⌉, so every loop bound is a compile-time constant the
  compiler unrolls into registers. v1 walked 48 limbs for every family at
  every height because LIMBS was a constant; the same work is 83 words at
  the score window.
- **One addition chain, chosen by shared cost.** All eight powers come off
  one chain, and the exponent set is enumerated exactly rather than
  guessed — a per-exponent DP double-counts what the powers already share
  and misses *p*¹⁹ = *p*¹⁷·*p*² for a *p*¹⁸ nothing wants.
- **A Montgomery Horner with no division and no R².** The sum is reduced
  bottom-up, A_j = w_j + A_{j−1}·2⁻⁶⁴ (mod *k*), one REDC per limb, and
  never converted back: *k* is odd, so X·2⁻⁶⁴ᴸ ≡ 0 exactly when X ≡ 0.
  The accumulator is left **unreduced between limbs** — `hi` carries
  weight 1 in that recurrence, so folding it by *k* when it would overflow
  changes no residue and costs two instructions, which is what removes the
  last division. Montgomery needs an odd modulus and the obstruction
  supplies it for nothing: 2 divides Q(*m*) for every *m*, so every
  *e* = 0 term is odd and **ODD_ONLY** coverage loses nothing.
- **A decoupled look-back for the prefix.** A warp owns a tile of
  consecutive primes, scans it with carry-propagating shuffles, publishes
  its aggregate, and sums its predecessors 32 at a time until it meets a
  published inclusive prefix. A segment is three launches and the running
  state never leaves the device.

The sieve is a segmented sieve over the odd residues, split by how much
work a prime carries: a small prime is walked by the whole block in
disjoint chunks, a large one gets a thread, and a prime bigger than a
sub-segment gets its own pass over the whole segment. One thread per prime
throughout — the obvious shape — gives the thread that draws *q* = 3 a
third of the sub-segment to itself, and cost 72% of an early window.

**Ceiling.** v1's LIMBS = 48 is gone as a constant: the width is computed
from the run, so a run that cannot be represented raises before a kernel
is compiled. P_CEIL = 2⁶² and K_CEIL = 2⁵⁷ still bind, and are still
checked rather than assumed (GPU G9, G16).

**v1 stays in the tree** as the parity reference and is never reachable
from a campaign (CLAUDE.md rule 3): G14 compares the two engines' streams
and states bit-for-bit.

## The odds model

On the index line, E[terms in (A, B)] = *c* · ln(B/A), because
P(*k* | *e* + S) ~ 1/*k* and summing over the *k* the obstruction leaves is
a logarithm. **c is derived, not fitted**: *c* = ∏(1 − 1/*q*) over the
obstruction primes, which is exactly 1/2 at every odd *m*.

Validation, stated before the run: **observed/predicted = 1.07 over 74
published terms in the asymptotic regime, 95% [0.83, 1.31]**, and the
known-term quantiles scatter (mean 0.50, 26% below 0.25, 27% above 0.75) —
CONVENTIONS.md refuses a model whose knowns all sit at ~0 or ~1.

Predictions for the next term of each family, on the index line:

| family | next term | Q1 | median | Q3 | P90 |
|--------|-----------|----|--------|----|-----|
| A125827 (m=11) | a(19) | 8.9×10¹⁴ | **2.0×10¹⁵** | 8.0×10¹⁵ | 5.0×10¹⁶ |
| A131263 (m=9) | a(14) | 8.9×10¹⁴ | 2.0×10¹⁵ | 8.0×10¹⁵ | 5.0×10¹⁶ |
| A131273 (m=13) | a(14) | 8.9×10¹⁴ | 2.0×10¹⁵ | 8.0×10¹⁵ | 5.0×10¹⁶ |
| A131279 (m=19) | a(27) | 8.9×10¹⁴ | 2.0×10¹⁵ | 8.0×10¹⁵ | 5.0×10¹⁶ |
| A131277 (m=17) | a(20) | 1.1×10¹⁵ | 2.5×10¹⁵ | 1.0×10¹⁶ | 6.3×10¹⁶ |
| A125826 (m=7) | a(20) | 2.2×10¹⁵ | 5.0×10¹⁵ | 2.0×10¹⁶ | 1.3×10¹⁷ |
| A045345 (m=1) | a(17) | 1.2×10¹⁶ | 2.6×10¹⁶ | 1.0×10¹⁷ | 6.5×10¹⁷ |

The `nice` headline (A045345) is the *most expensive* family, because its
frontier is the highest — a fact worth stating plainly rather than hiding
inside a total.

## Running it

```
python launch.py --selftest   # the full gate battery -- must end ALL GREEN
python score.py               # gates x fingerprinted benchmark
python launch.py --status     # where the checkpoint stands
python launch.py              # the hunt (owner-started, days)
```

Requirements: Python 3.12, numpy, sympy, cupy (CUDA 12), one NVIDIA GPU.
`launch.py` is indefinite by default and stops only at the engine ceiling;
`--to` and `--stop-on-discovery` are the only stops and both are opt-in.
Ctrl+C is a normal exit: it checkpoints at the last segment boundary, logs
one line, and exits 130 with no traceback. `--gpu-yield-ms` and `--gentle`
trade a few percent of rate for a quieter desktop.

## Trust

The gate discipline, the discovery protocol and the census rule are
repo-wide and live in [CONVENTIONS.md](../CONVENTIONS.md). Project-specific:

- **Four independent implementations.** The oracle (sympy, exact Python
  integers, the definition as written), the CPU engine (numpy sieve, exact
  integers, plain `%`), the v1 GPU engine (fixed 48-limb arithmetic, a
  materialised prefix), and the v2 GPU engine (widths generated per run, a
  fused kernel, a division-free Montgomery Horner). No one of them ever
  calls another; the parity gates compare their *streams* on populated
  windows, and G14 requires all three engines to agree exactly.
- **The geometry must be invisible.** G15 sweeps the same window at five
  segment/tile shapes and requires one stream and one state. One shape is
  deliberately tile-rich, past the number of warps the device holds at
  once: an earlier build capped its own grid there and dropped the tail of
  the line, deterministically and silently, and every gate shape at the
  time had too few tiles to notice.
- **124 published terms as canaries.** The sweep starts below every live
  frontier, so it must rediscover them all before it reaches new ground.
  A hit below a frontier that is *not* published is an ALARM, not a
  discovery: either this engine is wrong or a published search missed a
  term, and both stop the campaign.
- **The third verification leg re-derives the segment**, on the CPU
  engine, at a different segment size, and captures the exact sum *at the
  hit index* — the protocol drill caught the earlier version reading the
  sum at the end of the segment instead, which is why it is written this
  way.
- **The witness is the quotient.** Every evidence file carries *k*,
  prime(*k*), the exact S(*m*, *k*) and (*e* + S)/*k*, so the claim is
  checkable with one multiplication by anyone who does not trust any of
  this code.
