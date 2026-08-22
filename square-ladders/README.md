# square-ladders — A089761

> Every line of code in this project was authored by Claude (Anthropic's
> AI) at the repository owner's direction. The mathematics, the gates, the
> engines and this document are all machine-written; the results below are
> machine-verified and human-reviewed. That audit trail is deliberate and
> it stays.

**A089761** asks for the least `k` such that `k·i² + 1` is prime for every
`i = 1..n` — a Dickson ladder whose rungs are the squares. Fifteen terms
are published, but the last **five of them are the same integer**: Donovan
Johnson searched for `a(11)` in 2008, found `k = 861,066,640`, and that one
value cleared `i = 12, 13, 14, 15` for free. The run stops at a single
composite, `861066640·16² + 1 = 220433059841 = 47 · 149 · 31476947`, and
that lone factorization is the entire reason `a(16)` is open. The only work
since is Max Alekseyev's searched-empty bound `a(16) > 1.4×10¹³`.

**Status: PAUSED — open to others.** The engine, the gate battery and the
odds model are complete and green; no production sweep has been run. The
frontier stands exactly where the literature leaves it: `a(15) =
861,066,640` published, `a(16) > 1.4×10¹³` searched-empty (Alekseyev). At
the measured production rate the model's median for `a(16)` is **10 seconds**
of sweeping and the engine's whole enforced range is about **12 hours**,
so anyone with a CUDA GPU can take this the rest of the way — overnight.

## The problem

    a(n) = least k >= 1 with k*i^2 + 1 prime for all i = 1..n

The conditions nest, so `a` is non-decreasing and a single lucky `k` can
settle several terms at once — which is exactly what happened at `a(11)`
and why the published list plateaus.

| | |
|---|---|
| Sequence | [A089761](https://oeis.org/A089761) (`hard`, `more`, `nonn`) |
| Published terms | `a(1)..a(15)` = 1, 1, 4, 22, 58, 58, 58, 54972, 68112, 4748632, 861066640 ×5 |
| Last *searched* term | `a(11)`, Donovan Johnson, Sep 27 2008 |
| Frontier | `a(16) > 1.4×10¹³` — Max Alekseyev, in the entry by 2017 |
| Last edit of any kind | revision #14, Aug 14 2017 |
| Upper bound | **none published, at any open n** |

Why it is open rather than merely unfinished: the density of qualifying `k`
falls like `1/(log k)ⁿ`, so each extra condition costs roughly a further
factor of `log k / S`-worth of line. It is conjecturally infinite for every
`n` — Dickson's conjecture, and Schinzel's Hypothesis H — so a find
**confirms** the guiding conjecture and can never refute it.

The floor of any claim here is free: `a(16) ≥ a(15) = 861,066,640` by
monotonicity, so nothing below that has to be swept at all.

## The mathematics of the engine

Fix a prime `q`. If `q | k` then every value is `k·i²+1 ≡ 1 (mod q)`, so
`k ≡ 0 (mod q)` is always **safe**. Otherwise `q | k·i²+1` exactly when
`i² ≡ -k⁻¹ (mod q)`, so the killed residues are

    K(q,n) = { -(i^2)^-1 mod q : 1 <= i <= n, q does not divide i }

and the engine sieves `k` against `K(q,n)` and nothing else. Its size is
exactly

    w(q,n) = |K(q,n)| = min(n, (q-1)/2)      for odd q,   w(2,n) = 1

proved both ways in `sqladder_reference.py`: for `q > 2n` the `i²` are
pairwise distinct so `w = n`; for `q ≤ 2n+1` the squares already run over
all `(q-1)/2` quadratic residues, and since they form a group closed under
inversion, `K(q,n) = -QR(q)`.

**This is why A089761 is not the engine `dickson-ladders` already has.**
A247965 kills *every* nonzero `k` mod each small prime, which forces its
terms to be multiples of the wheel modulus and leaves exactly one candidate
residue per period. Here only half the nonzero residues die, so the wheel
is a **residue table** of `∏(q - w(q,n))` entries rather than a single
multiplier. The two problems read like transposes and need different
machinery.

**The kernel.** The CPU engine materialises the dense `k` line and marks
arithmetic progressions into it. The GPU engine never forms the line: it
enumerates wheel residues and *tests* each candidate against a packed
forbidden-residue bitmap by Barrett magic-multiply, **bailing out at the
first kill**. That early exit is the performance argument — `w(q,n)` is 16
out of every `q` for `q ≥ 37`, so the expected number of tests per
candidate is 3.07 against the ~22 marks a marking sieve of the same depth
would pay. It also makes sieve depth nearly free: 4096 and 262144 measured
within 2% of each other.

**The wheel is factored.** A measured phase split put candidate generation
at 11% of the v1 kernel and the Barrett loop at 89%, so the lever was fewer
candidates, not cheaper tests. (It is 15.3% / 84.7% on the v3 kernel below,
which is what re-measuring a split after every structural change is for.)
But a one-level wheel over the primes to 37
would be 5.5×10⁹ residues (~44 GB). So the engine stores two tables and
recombines them per candidate by CRT:

    x = RES1[t] + W1 * ( (RES2[s] - RES1[t]) * W1^-1  mod W2 )

5,040 entries beside 1,088,640 give the wheel of all primes to 37 —
**6.6× fewer candidates per unit of line** than primes to 23 — out of two
tables that still fit in cache. Measured end-to-end, same window, same run:
**3.9×**.

**The warp pays the maximum, so the block compacts.** The test loop turns
out to be bound by instruction *issue*: adding 24 independent instructions
to its body costs 42% of the wall clock. That makes two things levers at
once, and they multiply. Fewer instructions per test — the remainder
correction is exact in 32 bits and needs only **one** conditional
subtraction below `2⁶³`, the per-prime constants are one 128-bit load
instead of three, and the six hottest primes (41…61) are baked in as
literals *and CRT-combined in pairs*, since “killed by 41 or by 43” is a
function of `k mod 1763` alone — six tests become three, against a table
of 981 bytes. And fewer tests per warp — a lane needs 3.07 tests but a
warp of 32 runs to the deepest of them, **16.06**, a 5.23× divergence tax.
So each thread takes 8 candidates, runs a branchless prefix on all of
them, and pushes the survivors into a **shared-memory queue**; one
`__syncthreads` later the whole block chews that queue with every lane
alive, then does it a **second** time. A block compacts 2,048 candidates to
~194 and then to ~24 — full warps where an uncompacted warp carried one
lane. Both compaction depths are *derived* from the survival curve rather
than hardcoded, because what a depth sweep finds is really a survival
fraction, and a coarser wheel reaches that fraction much sooner. None of it leaves the kernel: the launcher is unchanged.

The queues are sized from the *analytic* survival rather than from the
worst case, which means overflow is possible — so it is made **harmless**
rather than impossible: a candidate that does not fit runs its tail on the
spot, uncompacted, which is the same arithmetic and so the same answer.
That turns capacity from a correctness bound into a tuning constant, and it
matters: sizing both queues for the case that never happens measured
**0.818×**, because the shared memory halved the blocks an SM could hold,
while the same change sized properly is 1.169×.

The combining has a sharp limit, and it is the table: 1.19× at 1 KB and
1.18× at 33 KB, but **0.25× at 76 KB** and 0.39× at 536 KB, as the tables
fall out of L1. `LIT_GROUP_MAX` is the budget that keeps them inside it.
(The same idea is recorded as *rejected* in another project in this repo,
and it pays here for a reason worth naming: that kernel was bound by load
count, this one by instruction issue, so trading instructions for a load is
the right way round.)

Generation is amortised the same way. `k = base + r1 + W1·m` with `m = A[t]
+ C[s]`, so for a fixed `t` the quantity `base + r1` does not depend on `s`
at all — give a block eight second-level residues and one load, one index
computation and one 64-bit add serve eight candidates instead of one.

Measured against the v2 kernel, interleaved in one run with both engines
required to agree on every survivor: **7.505×**.

**Every primality decision here is a proof.** The largest value is
`k·n²+1`, and at the enforced ceiling `K_CEIL = 9×10¹⁸` with `n = 16` that
is `2.3×10²¹` — under huntlib's deterministic Miller-Rabin bound of
`3.317×10²⁴`. The whole enforced range is deterministic, for every filter
up to `n = 607` (gate G10). Unlike `dickson-ladders`, whose values pass
that bound before `a(9)`, this project never needs a probable-prime
qualifier.

## The odds model

Bateman-Horn over the `n` linear forms `f_i(k) = i²k + 1`, with the
singular series computed numerically from the same `w(q,n)` the sieve is
built from. Stated **before** any sweep (`model_results.json`):

| term | Q1 | median | Q3 | P90 |
|------|----|--------|----|-----|
| a(16) | 5.33×10¹⁴ | **2.18×10¹⁵** | 6.84×10¹⁵ | 1.58×10¹⁶ |
| a(17) | 1.27×10¹⁶ | **5.91×10¹⁶** | 1.92×10¹⁷ | 4.49×10¹⁷ |
| a(18) | 4.44×10¹⁷ | **1.99×10¹⁸** | 6.32×10¹⁸ | 1.46×10¹⁹ |

Quantiles for `a(16)` are measured from Alekseyev's bound, not from
`a(15)`: crediting the model for ground somebody else already cleared would
make every prediction optimistic.

**Validation (gate G11).** If the modelled intensity is right, its integral
up to the first occurrence is `Exp(1)` — mean 1. On the independently
searched knowns `a(8), a(9), a(10), a(11)` it is **1.51 / 0.03 / 0.54 /
1.47, mean 0.89**. Spread from near zero to about 1.5 on four draws is what
`Exp(1)` looks like; a model whose knowns all sat near 1 would be
overfitted, not validated.

**One vote per condition.** `a(11)` through `a(15)` are the same integer, so
scoring the model at all five would be scoring one event five times. Only
separately-searched terms are used.

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # 24 gates and drills; must end ALL GREEN (~12 s)
```

```bash
python score.py                # gates x fingerprinted benchmark (~35 s)
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py
```

It is indefinite by default, resumable, checkpointed every segment, and
stops cleanly on Ctrl+C with exit 130. `--to` caps the depth,
`--stop-on-discovery` exits on the first confirmed find, and `--gentle`
trades about 8% of the rate for a noticeably freer desktop.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle, a numpy CPU
  engine that marks the dense line with no wheel at all, and a CuPy engine
  that enumerates wheel residues and tests them. G9 pins the GPU stream to
  the CPU stream bit-for-bit on seven populated windows — both kernels,
  two filters, heights from `2×10⁹` to the enforced ceiling.
- **The benchmark checks itself.** `SCORE` and `SCORE1L` sweep the same
  window with the factored and one-level wheels and must return the
  identical fingerprint, so a bug in the CRT constants shows up inside the
  benchmark.
- **Every optimization is gated at the mechanism, not just end to end.**
  G14 checks the v3 machinery against its own definitions at the
  *production* configuration, which is the one G9 cannot reach with a dense
  CPU sieve: the split A/C generation tables must reproduce the one-table
  CRT on sampled pairs, each baked literal prime must carry the same kill
  set and bit offset as the packed bitmap it replaced, and the shared
  queue's capacity must equal the candidates a block owns, so "cannot
  overflow" is arithmetic rather than optimism.
- **Canaries.** The GPU stream rediscovers `a(8)`, `a(9)` and `a(10)` as
  first occurrences at their own filters before any claim is made.
- **The protocol is tested in both directions.** A genuine run-15 is
  accepted with a factor witness for its stopper; a fake run-16 claim on
  the same `k`, and `a(10)`'s `k` mislabelled as a run-15, are both
  rejected.
- **Ceilings raise rather than compute** — `K_CEIL`, the u32 wheel modulus,
  `RES_MAX`, the `gridDim.y` cap on the second-level wheel, and the
  `max(K_FLOOR, q2)` floor, all drilled.
