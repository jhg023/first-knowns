# shift-ladders — A130003 and A110096

> Every line of code in this project was authored by Claude (Anthropic's
> AI) at the repository owner's direction. The mathematics, the gates, the
> engines and this document are all machine-written; the results below are
> machine-verified and human-reviewed. That audit trail is deliberate and
> it stays.

**A130003** asks for the least `m` such that `m + 4^k` is prime for every
`k = 1..n`, and **A110096** asks the same question of `2^k`. They are
*shift ladders*: one unknown, `n` conditions that differ only by an
additive constant, and a killed set that is a **geometric orbit** rather
than the quadratic one of this repo's square and Dickson ladders. Eighteen
terms of A130003 were published and the last of them,
`a(18) = 1,158,174,141,556,287`, was found by Jens Kruse Andersen in **June
2007**; nothing had touched that frontier in nineteen years. A110096 had
sixteen, the last three from Bert Dobbelaere in April 2021. Neither entry
carries an upper bound of any kind, at any open `n`.

**Four new terms, in 18.1 hours of one RTX 4090:**

    A130003  a(19) =                13,268,589,982,417,023
             a(20) =             6,120,156,516,528,136,867
    A110096  a(17) =       305,948,728,878,647,722,725
             a(18) =       760,056,834,873,121,351,995

`a(19)` of A130003 landed **117 seconds** into the campaign, which is what
a nineteen-year-old frontier with no published bound below it looks like
once the engine is right. Both A110096 terms are above `2⁶⁴`. Every
primality decision in all four is a proof rather than a probable-prime
call. The exact integers, all values, the certificates and the factor
witnesses are in [`evidence/`](evidence/); the claims and the verification
are in [RESULTS.md](RESULTS.md).

**Status: PAUSED — open to others.** Both campaigns were stopped by the
owner on 2026-08-24, A130003 at `m = 8.95×10¹⁸` with `a(21)` open and
A110096 at `m = 3.62×10²¹` with `a(19)` open. The full battery is green
(30 gates and drills), the benchmark's five shapes reproduce their frozen
fingerprints, and both cursors resume in place.

At the rate each campaign measured, `a(21)` of A130003 is about 6 days of
sweeping to its median and `a(19)` of A110096 about 3 — read as floors
(see [the odds model](#the-odds-model)). Both numbers should be **1.8 and
1.4 days**: the campaigns ran at 29% and 41% of their own kernel, and the
missing time is not in the kernel at all but in `check_rungs` rebuilding
the progress ladder from the odds model once per segment. It is measured,
it is worth 3.35×, and the one-line fix is priced but not applied
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)) — **read that before resuming
either campaign.** Past those terms, A110096 runs into the
engine's primality-proof ceiling: the model puts `a(20)` below it with only
19% probability, so a further term on that family means wiring huntlib's
BLS75 certificates into the verification path. A130003 has room to `a(23)`.

## The problem

    A(b, n) = least m >= 1 with m + b^k prime for all k = 1..n

The conditions nest, so `A(b, ·)` is non-decreasing and a single lucky `m`
can settle several terms at once — which is exactly what happened at
A130003's `a(10) = 4503` (it cleared `k = 11, 12, 13, 14` for free) and at
five separate places in A110096.

| | A130003 | A110096 |
|---|---|---|
| Sequence | [A130003](https://oeis.org/A130003) (`nonn`, `hard`, `more`) | [A110096](https://oeis.org/A110096) (`nonn`, `more`) |
| Base | `b = 4` | `b = 2` |
| Published terms | `a(1)..a(18)` | `a(1)..a(16)` |
| Frontier | `a(18) = 1,158,174,141,556,287` | `a(16) = 143,924,005,810,811,655` |
| Found by | Jens Kruse Andersen, **Jun 08 2007** | Bert Dobbelaere, Apr 24 2021 |
| Author | Farideh Firoozbakht, May 30 2007 | Joseph L. Pe, Sep 05 2005 |
| Other link | Rivera, [Puzzle 403](http://www.primepuzzles.net/puzzles/puzz_403.htm) | Rivera Puzzle 379 cluster; A193109 |
| **Found here** | `a(19)`, `a(20)` | `a(17)`, `a(18)` |
| **Open, and next** | `a(21)`, empty below `8.95×10¹⁸` | `a(19)`, empty below `3.62×10²¹` |
| Upper bound | **none published, at any open n** | **none published, at any open n** |

Why they are open rather than merely unfinished: the density of qualifying
`m` falls like `1/(log m)ⁿ`, so each extra condition costs a further factor
of roughly `log m` worth of line. Both are conjecturally infinite for every
`n` — the constellation `{b, b², …, bⁿ}` is admissible at every `n`
(proved in `shiftladder_reference`), so Dickson's conjecture applies and a
find **confirms** the guiding conjecture and can never refute it.
A110096's entry records that argument (Charles R Greathouse IV, Oct 2011).

**A130003's frontier is the stale one, and it is stale by nineteen
years.** Rivera's Puzzle 403 — the entry's only link — was re-read when
this project was built: Andersen's table there ends on the same
`a(18)`, and the only bound on the page is Bernardo Boncompagni's
long-superseded `2.84×10¹¹`. Nothing anywhere was past it — and the OEIS
export was re-pulled on 2026-08-26, after the sweep, with both entries
still ending exactly where they did.

## The mathematics of the engine

Fix a prime `q`. Then `q | m + b^k` exactly when `m ≡ -b^k (mod q)`, so
the residues of `m` that `q` kills are

    K(q,n,b) = { -b^k mod q : 1 <= k <= n }

and the engine sieves `m` against `K(q,n,b)` and nothing else. Note what is
absent: no inverse, no quadratic character, no case on whether `q | m`. Its
size is exactly

    w(q,n,b) = |K(q,n,b)| = 1              if q | b
                          = min(n, ord_q(b))  otherwise

proved in `shiftladder_reference.py`: negation is a bijection, so `|K|` is
the number of distinct `b^k` for `k = 1..n`, and the powers of `b` cycle
with period `ord_q(b)`. Since `w ≤ q-1 < q` always, no prime divides every
value — the admissibility that makes this a hunt rather than a wild goose
chase.

**The two bases are not the same problem, and `ord` is the whole reason.**

    ord_q(4) = ord_q(2) / gcd(2, ord_q(2))  <=  (q-1)/2   for every odd q

while `ord_q(2)` reaches `q-1` at every `q` for which 2 is a primitive
root. So at `b = 2` and `q ≤ n+1` with 2 primitive mod `q`, `w = q-1`:
**every** nonzero residue dies and `m` must be *divisible* by `q`. From
`n ≥ 4` that already forces `3 | m` and `5 | m`, and with `m` odd every
term of A110096 above the exception zone is `15 mod 30` — an observation
A193109 records without proof, which is this lemma. At `b = 4` nothing of
the sort happens: 2 of 3 residues survive mod 3 and 3 of 5 mod 5.

The consequence is a wheel that differs by three thousand times between two
sequences that read identically:

| | A130003 (b = 4, n = 19) | A110096 (b = 2, n = 17) |
|---|---|---|
| flat table's primes | ≤ 29 | ≤ 37 |
| modulus `W` | 6.47×10⁹ | 7.42×10¹² |
| residues | 23,587,200 | 5,391,360 |
| bit planes carry the wheel to | 79 (3 planes) | 113 (5 planes) |
| plane survival `d2` | 1.70×10⁻² | 8.26×10⁻³ |
| **candidates per unit line** | **6.2×10⁻⁵** | **6.0×10⁻⁹** |

and that last row sets everything downstream: the line rate (four orders of
magnitude apart at candidate rates within a factor of three), the singular
series (A110096's is 12,000× larger), and how deep a table has to go before
it stops fitting. The two effects nearly cancel in cost per term, which is
why both families belong in one project rather than two. Note the
plane-survival row — the two families reach it by quite
different routes, one wheel stopping at 79 and the other at 113, because
`p2` is derived per configuration from a cost model rather than pinned per
base.

**The kernel.** The CPU engine materialises the dense `m` line and marks
arithmetic progressions into it. The GPU engine never forms the line: it
generates only the `m` that survive the wheel and *tests* each of those
against a packed forbidden-residue bitmap by Barrett magic-multiply,
bailing out at the first kill. A lane needs about three tests, which is
what makes sieve depth nearly free — and `q2` is 65536 in production for
exactly that reason. But a *warp* of 32 lanes runs to the deepest of its
32, which measured 13.96 against that mean of 2.78, so the tests are run in
branchless slices over a dense queue and the survivors compacted between
slices, every lane alive. The slice boundaries come out of the survival
curve, not out of a prime count.

The engine is v2 and it is **84.8× faster than v1 at base 4 and 44.6× at
base 2**, measured over a common absolute window with the two survivor
streams compared to each other, and every frozen fingerprint reproduced or
deliberately re-frozen ([BENCHMARKS.md](BENCHMARKS.md),
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).

**Candidates are carried as `(m, off)` from the first commit.** `m = base +
off` with `base` a host-side big integer that never reaches the device and
`off < per_launch · W` the only thing the kernel reduces; `base mod q` is
folded once per launch, per prime, on the host. So no machine word bounds
this search, and the enforced ceiling is the primality-proof bound
`k_ceil(n, b) = 3.317×10²⁴ − bⁿ` rather than `2⁶⁴`. That is
OPTIMIZATION.md 2.7 applied at the start instead of retrofitted:
square-ladders raised its ceiling twice, and the second time cost a
campaign stretch. G15 checks that the survivor stream does not depend on
where the launch base was put, at `m = 10¹²`, `2⁶⁴`, `10²⁴` and `3×10²⁴`.

**Every primality decision here is a proof, by construction.** The largest
value is `m + bⁿ`, and the offset is *additive*: `4²¹` is `4.4×10¹²`
against a bound of `3.317×10²⁴`, so the ceiling is essentially the bound
itself for both families. Gate G10 pins it tight to a single `m`, per
`(n, b)`. This project will not need a probable-prime qualifier for a very
long time.

**The wheel is two mechanisms, and the second one is why this engine is
fast.** The primes up to `p1` are a flat residue table, which is all v1
had; a table cannot hold more than that, and 23 is where it stops. The
primes above it go in as **bit planes over the period index**, which is a
different object entirely. Write `m = j*W + r`. Then

    q | m  <=>  (j + Binv_q · r) mod q  in  Binv_q · K(q),   Binv_q = W⁻¹ mod q

and once `r` is fixed that is a condition on **`j` alone**, periodic with
period `q`. So a group of primes above the flat wheel has one fixed
surviving-`j` set mod their product, and **one 32-bit load and one `and`
filter thirty-two consecutive periods**. Folding a prime into a plane costs
a few hundred KB, not a factor of `q` in a table, so the wheel reaches 79
at `b = 4` and 113 at `b = 2` — where a flat table at 47 would already have
asked numpy for 183 GiB.

Two properties make it fit *this* problem. The shift is **additive**, so
every residue's killed set is a translate of one fixed set and one `u32`
per residue per plane is the whole per-residue state. And **`W` does not
change**: the plane primes never enter the modulus, so a period still means
what it meant, coverage still advances every launch, a v1 cursor is
inherited rather than re-denominated, and every frozen benchmark window is
the same window. A factored multi-level table — the thing v1's log said to
build next, and what square-ladders does — would have multiplied `W` by
2.8×10⁹, giving a period of `6.1×10¹⁷` against an `a(19)` median of
`5.75×10¹⁶`: the coverage claim would have advanced in steps ten times
wider than the entire hunt.

## The odds model

Bateman-Horn over the `n` linear forms `f_k(m) = m + b^k`, with the
singular series computed numerically from the same `w(q,n,b)` the sieve is
built from. Stated **before** any sweep (`model_results.json`):

| term | Q1 | median | Q3 | P90 |
|------|----|--------|----|-----|
| A130003 a(19) | 1.40×10¹⁶ | **5.75×10¹⁶** | 1.98×10¹⁷ | 5.06×10¹⁷ |
| A130003 a(20) | 2.60×10¹⁷ | **1.42×10¹⁸** | 5.41×10¹⁸ | 1.42×10¹⁹ |
| A130003 a(21) | 8.43×10¹⁸ | **4.73×10¹⁹** | 1.77×10²⁰ | 4.57×10²⁰ |
| A110096 a(17) | 5.03×10¹⁹ | **2.03×10²⁰** | 6.06×10²⁰ | 1.34×10²¹ |
| A110096 a(18) | 4.34×10²¹ | **1.74×10²²** | 5.14×10²² | 1.13×10²³ |
| A110096 a(19) | 1.43×10²³ | **5.67×10²³** | 1.66×10²⁴ | 3.61×10²⁴ |

**Validation (gate G11).** If the modelled intensity is right, its integral
up to the first occurrence is `Exp(1)` — mean 1. Pooled over both families
at the ten independently-searched knowns it is **mean 0.88**, spread
0.10–2.65:

    A110096  a(10) 0.77  a(11) 0.82  a(12) 1.68  a(14) 2.65  a(15) 0.50
    A130003  a(10) 0.57  a(15) 0.24  a(16) 0.10  a(17) 1.07  a(18) 0.45

Pooling is not mixing evidence: it is one model, and each family alone
offers four or five draws, which cannot tell a factor-of-two error from
noise. Ten can.

**One vote per condition.** Both sequences are riddled with riders —
A130003's `a(11)`–`a(14)` are one integer, A110096 repeats at `a(2)`,
`a(4)`, `a(6)`, `a(8)`, `a(13)` and `a(16)`. A rider was never searched
for, so its `E` is identically zero and scoring it would manufacture
agreement out of nothing. Only terms that strictly exceed their predecessor
are used.

**How the finds scored** (out of sample, against the table above, each
measured from the floor its own search started at):

| term | found at | live median | E at the find | quantile |
|------|----------|-------------|---------------|----------|
| A130003 `a(19)` | `1.33×10¹⁶` | `5.75×10¹⁶` | 0.278 | 0.243 |
| A130003 `a(20)` | `6.12×10¹⁸` | `1.64×10¹⁸` | 1.426 | 0.760 |
| A110096 `a(17)` | `3.06×10²⁰` | `2.03×10²⁰` | 0.899 | 0.593 |
| A110096 `a(18)` | `7.60×10²⁰` | `1.97×10²²` | 0.042 | 0.041 |

Two early, one late, one on the nose: **2.64 expected hits for 4 actual**,
an optimism factor of **0.66×** with an exact 95% interval of
**[0.30, 2.43]**, which contains 1. And the census
([RESULTS.md](RESULTS.md#census)) says the intensity underneath it is right
to within 1% over 15,457 classified values on both families at once. On
its own four draws, this model is not measurably wrong in either direction.

**Read every median above as a floor anyway.** Four draws cannot separate
0.66× from 2×, and the three ladder projects in this repository have now
scored eleven first occurrences between them at a pooled optimism factor of
**2.06×**, 95% interval **[1.23, 4.13]** — still excluding 1, still with
each project's census showing the modelled *intensity* right to a percent
or two. Mean count right, first occurrence late. Their mean model quantile
is 0.69 against the 0.50 a correct model gives; the four finds above are
what pulled it down from 0.85. Budget 2-3× the medians before expecting a
term, and treat a term that arrives on the median as luck rather than as
calibration.

**The live ladder**, re-derived from the frontiers this project set. The
table above is the pre-sweep record and stays as it was; four of its six
rows are now settled terms, and the two that are still open — `a(21)` and
`a(19)` — are re-derived here from the floors those finds moved
(CONVENTIONS.md, "a rung retires with its term"):

| term | Q1 | median | Q3 | P90 | P(below the engine's ceiling) |
|------|----|--------|----|-----|-------------------------------|
| A130003 a(21) | 2.84×10¹⁹ | **8.45×10¹⁹** | 2.41×10²⁰ | 5.51×10²⁰ | 100% |
| A130003 a(22) | 4.17×10²⁰ | **1.93×10²¹** | 6.65×10²¹ | 1.64×10²² | 100% |
| A130003 a(23) | 1.38×10²² | **6.89×10²²** | 2.40×10²³ | 5.92×10²³ | 99.8% |
| A110096 a(19) | 1.52×10²³ | **5.82×10²³** | 1.68×10²⁴ | 3.64×10²⁴ | 88.5% |
| A110096 a(20) | 5.28×10²⁴ | **2.07×10²⁵** | 5.99×10²⁵ | 1.30×10²⁶ | **19%** |
| A110096 a(21) | 2.00×10²⁶ | **7.76×10²⁶** | 2.24×10²⁷ | 4.82×10²⁷ | **2%** |

That last column is the one to read. The ceiling is
`k_ceil(n, b) = 3.317×10²⁴ − bⁿ`, the primality-proof bound, and A110096's
values outgrow it two terms from here while A130003's do not: the base-2
family has about one more term in range, and going past it means proving
larger primes rather than making the engine faster.

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # 30 gates and drills; must end ALL GREEN (~60 s)
```

```bash
python score.py                # gates x 5 fingerprinted shapes (~90 s)
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py               # A130003 (base 4), the default
```

```bash
python launch.py --base 2      # A110096 instead
```

Each family keeps its own checkpoint under its own config key, and neither
campaign will read the other's cursor. Either command above resumes where
that family was paused — `m = 8.95×10¹⁸` at base 4, `m = 3.62×10²¹` at
base 2 — with the filter already promoted to the term it is hunting. The
hunt is indefinite by default, resumable, checkpointed every segment, and
stops cleanly on Ctrl+C with exit 130. `--to` caps the depth,
`--stop-on-discovery` exits once **this run** confirms a find, and
`--gentle` yields 2 ms after every launch for a noticeably freer desktop.
Its price is worth re-reading before you use it: the sleep measures ~2.5 ms
per launch on this machine against an ~11 ms base-4 launch, so about a
fifth of the rate rather than the third the help text claims. The
disagreement is recorded rather than overwritten
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)) — the two numbers may simply
be measuring different things.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle, a numpy CPU
  engine that marks the dense line with no wheel at all, and a CuPy engine
  that generates wheel survivors and tests them. G9 pins the GPU stream to
  the CPU stream bit-for-bit on six populated windows across both bases,
  from `m = 2×10⁴` to `1.8×10¹⁹`, the top two **above 2⁶⁴**.
- **Every v2 mechanism is checked against something that does not share its
  arithmetic (G16).** The bit planes are checked against plain divisibility
  in BOTH directions on thousands of (residue, period) pairs — a plane that
  killed too much would silently lose survivors, and a sparse parity window
  could miss it. The round schedule must come out as a survival *fraction*,
  so the same target has to produce different depths at `n = 19` and
  `n = 10`. All four queue capacities are forced to token size and the
  stream must be identical, which is what makes "capacity is a tuning
  constant, not a correctness bound" a checkable claim rather than a
  comment. And a launch too short to fill one block tile must spread the
  block across residues and still return the same stream.
- **The killed set is built three ways.** The oracle walks every residue
  and tests divisibility; the engines negate the orbit of `b`; the closed
  form says `min(n, ord_q(b))`. G2b and G3 require all three to agree, in
  both directions, for every prime below 300 at six filters and both bases.
- **The benchmark checks itself.** `SCORE` and `SCORE1L` sweep the
  *identical absolute window* with the wheel at 23 and at 13 — 7,429×
  as many periods — and must return the same seven survivors and the same
  checksum, so a bug in the CRT lift shows up inside the benchmark.
- **Canaries.** The GPU stream rediscovers A130003 `a(15)` and A110096
  `a(9)` and `a(10)` as first occurrences at their own filters, sweeping
  from the engine floor, with the sub-period prefix cleared on the CPU so
  "first" is a claim about the line and not about a window.
- **The protocol is tested in both directions, on both families.** Each
  frontier term is accepted at its true run with a factor witness for its
  stopper; a run one too long, and an earlier term mislabelled as the
  frontier's run, are both rejected.
- **Ceilings raise rather than compute** — the primality-proof cap, the
  engine floor, the Barrett bound on the wheel modulus, the flat table's
  own size limit (the b = 2 wheel reaches 1.29×10⁹ residues at p1 = 47, and
  asking for it must refuse rather than fail 183 GiB into an allocation),
  and the bit planes' total budget. All drilled.
- **The cursor's unit is asserted, not just described.** The config key
  names the wheel, which is documentation; the checkpoint stores `W` and
  the campaign refuses to read a cursor counted in a different period,
  which is the half that does not depend on the description being right
  (OPTIMIZATION.md 2.9). v2 leaves `W` alone, so a v1 cursor is inherited
  rather than re-denominated — and the cursor-policy drill puts every one
  of the three readers in front of a checkpoint written under each key.
