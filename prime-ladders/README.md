# prime-ladders — A084700 and A084701

> Every line of code in this project was authored by Claude (Anthropic's
> AI) at the repository owner's direction. The mathematics, the gates, the
> engines and this document are all machine-written; any results that land
> here will be machine-verified and human-reviewed. That audit trail is
> deliberate and it stays.

**A084700** asks for the least `k` such that `prime(i)·k + 1` is prime for
every `i = 1..n`, and **A084701** asks the same question of
`prime(i)·k − 1`. They are *prime ladders*: one unknown, `n` linear
conditions whose multipliers are the primes themselves — the shape of this
repo's square ladders with `i²` replaced by `prime(i)`, and an engine that
transfers almost unchanged. Thirteen terms of A084700 were published and
the last of them, `a(13) = 161,082,438,032,880`, was found by Phil Carmody's
GenSv siever in **March 2004**; A084701 has eleven, and its
`a(11) = 3,894,254,360,010` dates from **June 2003**. Neither frontier had
moved in twenty-two years, and neither entry carries a bound of any kind at
any open `n` — until this project's three campaigns, on 2026-09-02 and 03,
found **`a(14)` through `a(18)` of A084700**, the last of them
`a(18) = 416,266,897,501,398,851,227,320`, and **`a(12)` through `a(18)`
of A084701**, the last of them `a(18) = 23,562,434,281,685,500,120,920`
([RESULTS.md](RESULTS.md)).

**Status: PAUSED — open to others.** Paused on 2026-09-03 with A084700 at
`k = 4.16×10²³`, filter `n = 19`, `a(19)` open and 22% likely under the
proof ceiling, and A084701 at its own ceiling, `k = 4.95×10²²`, with its
`a(19)` open above it; anyone is welcome to extend either, and whoever
resumes runs the selftest and `score.py` first. **`a(14)`, `a(15)`,
`a(16)` and `a(17)` of A084700
were found and verified on 2026-09-02** by the first campaign, in 4.4
hours of device from `k = 10⁶`, and **`a(18)` on 2026-09-03** by the
second, 15.2 hours in from where the first stopped
([RESULTS.md](RESULTS.md)); they are the first new terms of the sequence
since 2004. The first campaign stopped at `k = 5.44×10²²` on the engine's
proof ceiling of the time, with `a(18)` open and only 24% likely to lie
under it, and the engine was rebuilt the same day as **v3**: the A084700
ceiling raised to `3.317×10²⁴`, with discoveries past the old crossing
proved by BLS75 certificate — `a(18)`, at `4.16×10²³`, is the first find
proved that way, fourteen of its eighteen values by certificate; the
wheel moved into unit space, to 53; and the constants re-swept on it —
**1.72× paired at the live filter**, `6.2×10¹⁸ k/s`
([BENCHMARKS.md](BENCHMARKS.md)). The full battery is green (41 gates and
drills, one of them re-checking the twelve finds from the bare definition)
and all six benchmark shapes are frozen. The A084700 cursor stands at
`k = 4.16×10²³` with the filter at `n = 19`, where the model puts only
22% of `a(19)` under the ceiling. **v3.1**
(2026-09-03) made the defaults the fastest configuration at every opening
the launcher has: the classification pool is sized from a measurement at
the campaign's own filter and re-sized at every promotion, the device may
not run ahead of it, and the compaction constant carries a per-filter
table -- 1.19–1.33× at the opening filters and 5.2× at `n = 19`, where
the `n = 18` constant sat on a cliff ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).
**The A084701 campaign ran on it the same afternoon, with no flags, and
found `a(12)` through `a(18)`** — `a(12)`, `a(13)`, `a(14) = a(15)` and
`a(16)` inside the first wheel period, seventeen minutes in, `a(17)` at 82
minutes, `a(18) = 23,562,434,281,685,500,120,920` at 118 — and reached
that family's proof ceiling of `4.95×10²²` two and a half hours after it
started, where it stopped with `a(19)` open and 99% likely to lie above
the ceiling ([RESULTS.md](RESULTS.md)). Those seven are the first new
terms of A084701 since 2003, and the family is now out of ceiling rather
than out of engine: its values' structure is on `N + 1`, which needs an
N+1 primality test huntlib does not have; with one, the ceiling would
rise to `3.317×10²⁴` and 27% of `a(19)` would be in reach. Both
campaigns are checkpointed where they stopped and resume with no flags;
the hunt is the owner's command.

## The problem

    A(s, n) = least k >= 1 with prime(i)*k + s prime for all i = 1..n

The conditions nest, so `A(s, ·)` is non-decreasing and a single lucky `k`
can settle several terms at once — which is exactly what happened at
A084700's `a(4) = 6` (it cleared `i = 5, 6, 7` for free and stopped at
`19·6 + 1 = 115`) and at A084701's `a(5) = 120` (three terms, stopped by
`19·120 − 1 = 2279 = 43 · 53`), and happened again at
`k = 165,784,683,394,437,030` on 2026-09-03: a run of 15 arrived while
A084701's `a(14)` was open, so `a(14) = a(15)`.

| | A084700 | A084701 |
|---|---|---|
| Sequence | [A084700](https://oeis.org/A084700) (`more`, `nonn`) | [A084701](https://oeis.org/A084701) (`more`, `nonn`) |
| Sign | `s = +1` | `s = −1` |
| Published terms | `a(1)..a(13)` | `a(1)..a(11)` |
| Published frontier | `a(13) = 161,082,438,032,880` | `a(11) = 3,894,254,360,010` |
| Found by | Phil Carmody (GenSv), **Mar 08 2004** | Robert G. Wilson v and Don Reble, **Jun 15 2003** |
| Author | Amarnath Murthy, Jun 08 2003 | Amarnath Murthy, Jun 08 2003 |
| **This project's frontier** | **`a(18) = 416,266,897,501,398,851,227,320`** — `a(14)`–`a(18)`, 2026-09-02/03, verified, [RESULTS.md](RESULTS.md); not yet submitted | **`a(18) = 23,562,434,281,685,500,120,920`** — `a(12)`–`a(18)`, 2026-09-03, verified, [RESULTS.md](RESULTS.md); not yet submitted |
| **Open, and next** | `a(19)` — 22% under the engine's ceiling | `a(19)` — the campaign swept to the family's ceiling, `4.95×10²²`, and `a(19)` is 99% likely above it |
| Upper bound | **none published, at any open n** | **none published, at any open n** |

Why they are open rather than merely unfinished: the density of qualifying
`k` falls like `1/(log k)ⁿ`, so each extra condition costs a further factor
of roughly `log k` worth of line. Both are conjecturally infinite for every
`n` — residue `0` survives every prime (`k ≡ 0 (mod q)` makes every value
`≡ s ≠ 0`), so the constellation has no fixed prime divisor at any `n`
(proved in `pladder_reference`), Dickson's conjecture applies, and a find
**confirms** the guiding conjecture and can never refute it.

The OEIS entries note that `a(n) ≡ 0 (mod 30)` from `n = 8`. That is not
an observation here, it is a lemma, and it is the whole reason this engine
is fast — see below.

## The mathematics of the engine

Fix a prime `q` and write `p_i = prime(i)`. If `q = p_i` for some `i ≤ n`
the form `p_i·k + s` is `≡ s (mod q)` and never divisible by `q`: the rung
whose multiplier is `q` itself kills nothing. For `p_i ≠ q`,
`q | p_i·k + s` exactly when `k ≡ −s·p_i⁻¹ (mod q)`, so the residues of `k`
that `q` kills are

    K(q,n,s) = { -s * prime(i)^-1 mod q : 1 <= i <= n, prime(i) != q }

and the engine sieves `k` against `K(q,n,s)` and nothing else. Inversion
and negation are bijections, so its size is

    w(q,n,s) = |K(q,n,s)| = #{ prime(i) mod q : i <= n, prime(i) != q }

— the number of **distinct residues the first `n` primes take mod `q`**,
proved in `pladder_reference.py` and gated three ways (G2b, G2c, G3: the
closed form, direct divisibility, and the engines' construction must all
agree, for both signs). Three consequences:

- **`w` does not depend on `s`**: `K(q,n,−1) = −K(q,n,+1)`. The two
  families have identical table sizes, identical survival curves, one
  singular series and one compiled kernel; only the table *contents*
  differ.
- **`w = n` for `q > prime(n)`**, so from the first sieve prime above the
  wheel every prime kills `n` of `q` residues — the steepest survival curve
  in this repo.
- **Forced divisibility.** When the first `n` primes cover *every* nonzero
  residue mod `q`, `w = q − 1` and the only surviving `k` are the multiples
  of `q`. That happens at

  | `q` | 2 | 3 | 5 | 7 | 11 | 13 |
  |---|---|---|---|---|---|---|
  | forced from `n =` | 2 | 4 | 8 | 10 | 14 | 27 |

  so `a(n) ≡ 0 (mod 30)` from `n = 8` — the entries' observation, proved —
  and **every candidate at the campaign filters is a multiple of 2310.**

**What that does to the wheel.** A wheel is a table of the residues mod
`W = ∏ q` that no wheel prime kills, and it has `∏ (q − w(q,n))` entries.
For the primes to 23 at `n = 14`, five of the nine factors are **1**:

| | prime-ladders, n = 14 | square-ladders, n = 18 |
|---|---|---|
| first-level residues mod `223,092,870` | **2,800** | 1,088,640 |
| second level (23, 37] | 7,344 | 4,560 |
| third level (37, 47] | 27,720 | 16,675 |
| wheel period `W` | `6.15×10¹⁷` | `6.15×10¹⁷` |
| candidates per unit of line | **`9.6×10⁻⁷`** | `1.3×10⁻⁴` |

Same primes, same period, same kernel — and 140× fewer candidates per unit
of line, which is what this project's line rate is made of. In `k` space
the wheel stops at 47 for the same reason it does in square-ladders: the
combined second modulus is a `u32` in the kernel's CRT arithmetic
(`2.76×10⁹` at 47, `1.46×10¹¹` at 53), and the engine raises rather than
wrapping. **v3 gets past it by the same lemma.** Every candidate at
`n ≥ 14` is a multiple of 2310, so the device sweeps `k' = k / 2310`
instead of `k`: the residues of `k'` that `q` kills are
`2310⁻¹ · K(q,n,s) mod q` (a bijection, so nothing about the survival
curve changes), the five primes of the unit leave the wheel altogether,
and 29, 31 and 53 come in under the same `u32` and `2⁶³` bounds — levels
`(..31]`, `(31, 41]`, `(41, 53]`, `W1 = 8.7×10⁷`, `W2 = 1.6×10⁸`, a period
of `3.26×10¹⁹` of `k`. At n = 18 that is **1.47× fewer candidates per unit
of line for the identical survivor set** (gate G17: the unit wheel returns
the v2 wheel's survivors, bit for bit, over a v2 period at the live
filter). The unit is fixed per family at the filter its campaign opens in
(2310 for A084700; 210 for A084701, whose opening filter n = 12 does not
yet force 11) and the engine refuses a unit that is not forced.

**The kernel is square-ladders' v5, transferred, and then re-tuned for
this density (v2).** The CPU engine materialises the dense `k` line and
marks arithmetic progressions into it, with no wheel at all. The GPU
engine never forms the line: it generates only the `k` that survive the
three-level wheel by CRT recombination and *tests* each against packed
forbidden-residue tables by Barrett magic-multiply, bailing out at the
first kill, with the divergence compacted three times inside the block
and the deep tail swept as *compaction rounds* over global queues — a
round too small to fill the device gives each item several lanes, because
the rare deep candidates were a latency chain rather than a divergence
tax, and that one finding was worth 3x on a phase that had been a quarter
of the device ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), v2).
Nothing in that kernel knows about the forms: every problem-specific object
— the wheel tables, the bitmap, the CRT-combined prefix groups, the
survival curve the compaction points are derived from — is built from
`killed_residues(q, n, s, unit)`, and the parity gate G9 pins the result
to the CPU engine bit for bit on 21 populated windows, both signs, one-,
two- and three-level wheels in `k` space and in unit space, from `k = 10⁴`
to `3.3×10²⁴` with the top windows above `2⁶⁴`.

**One thing was added: a window may start inside period 0.** A three-level
period is `6.15×10¹⁷` of line and both frontiers are inside the first one.
square-ladders never swept its period 0 (its cursor was adopted from an
earlier wheel), so its engine refused any window beginning at or below the
engine floor. Here `sweep` and `survivors_j` take `k_min`: the device
sieves the whole period and the host drops every survivor below `k_min`
before anyone sees it — exact, because a survivor above `k_min > q2` is a
survivor of a sieve whose every prime is below it, so "`q` divides the
value" still means "composite". The campaign opens at period 0 clipped at
`K_START = 10⁶`; below that the least-claim is monotonicity (`a(13)` is
`1.6×10¹⁴`), above it our own coverage. G9 pins the clipped stream, the
resume drill cuts the `(j, u)` cursor inside the clipped period, and the
canaries rediscover `a(8)` and `a(9)` of both families by sweeping period 0
from the floor.

**Candidates are carried as `(k, off)` from the first commit.** `k = base +
off` with `base` a host-side big integer that never reaches the device;
`base mod q` is folded once per launch, per prime and per CRT group, on the
host (G15: the stream does not depend on where the launch base was put, at
bases up to `10³⁰`). So no machine word bounds this search, and the
enforced ceiling is the family's **primality-proof validity bound**
(G10, tight to one `k`).

**Where the proofs come from.** The largest value is `prime(n)·k + s`, and
below the **proof crossing** `k_proof(n, s) = (3.317×10²⁴ − 1 − s) /
prime(n)` — `5.6×10²²` at `n = 17`, `5.4×10²²` at `n = 18` — it stays
under huntlib's deterministic Miller–Rabin bound, so every classification
the hunt makes there is a proof. The first campaign ran to exactly that
crossing and stopped. Past it the same seven-base chain is a strong
probable-prime test, and for A084700 a *discovery* is proved instead by
the value's own structure: `N − 1 = prime(i)·k` is completely factored
once `k` is, so BLS75 Theorem 1 (huntlib.certificate, as dickson-ladders
uses it) proves every value of the run on one factorization of `k`, and
every certificate is re-verified from scratch before it is written
(`certify_run`; the evidence file records the route and any value left
unproved). `a(18)` is the first find proved this way: its values from
`i = 5` on are past the bound, and its file carries fourteen
`bls75-thm1` certificates on the one factorization of `k`
([RESULTS.md](RESULTS.md)). The v3 ceiling is therefore the deterministic bound on `k`
*itself*, `3.317×10²⁴`: while `k` is under it every prime factor of `k`
is a deterministic-MR prime and the certificate is one level deep. Past
that a factor of `k` could need a subproof, which huntlib carries but
this engine does not assume — a new version, with gates at that height.
A084701's structure is on `N + 1`, which needs an N+1 test huntlib does
not have, so its ceiling stays at its crossing (`9.0×10²²` at `n = 12`,
`4.95×10²²` at `n = 19`) and every decision on that family is a proof —
all seven of its finds are certified by the deterministic test alone,
every value under the bound. Its campaign reached that ceiling on
2026-09-03 and stopped; an N+1 route (BLS75's `N + 1` theorems on the
factorization of `prime(i)·k`, complete once `k` is factored, exactly as
the `N − 1` route is for A084700) would lift it to the same `3.317×10²⁴`,
and is a new engine version with a certificate drill at that height. The
census is counted either side of the crossing; a `[MILESTONE]` line marks
the sweep passing it.

**Coverage is coarser than work, and the checkpoint carries both
(CONVENTIONS.md "Two cursors").** The wheel emits a period's candidates in
`(t, s, u)` order, so the line is contiguous only at a period boundary:
`swept to` advances one period at a time and is the only thing a
least-claim rests on, while the work cursor `(j, u)` advances every launch
so a crash costs one checkpoint interval (128 launches, under a second).
Values classified mid-period are held *in the checkpoint* and narrated in
`k` order when the period closes; a find costs at most one period of
over-sweep — five seconds at n = 18 on the unit wheel. **A v1/v2 cursor is
adopted, never accepted:** the unit wheel keeps every survivor the old
wheel kept but counts a 53× longer period, so only the claim "every `k`
below this is swept" carries over, re-denominated by flooring (the live
cursor's period 88434 of `6.15×10¹⁷` became period 1668 of `3.26×10¹⁹`),
and the overlap under the adopted `k` is re-swept as a cross-check —
neither counted nor narrated, and a discovery-grade run there is an
alarm, because the two wheels would then disagree about cleared line.

**The host classifies in a ramped pool sized from a measurement at the
campaign's own filter.** A survivor costs 13.1 µs with a base-2
strong-test screen confirmed by the deterministic chain at run ≥ 8 (a
failed base-2 test is a proof of compositeness, so the screen can only
overstate, and everything it reports at the census floor is recomputed;
49.6 µs without the screen, identical run lengths, drilled), and how many
arrive per second depends entirely on the filter: at A084700's opening
filter n = 14 the sieve leaves `4.8×10⁻¹³` survivors per unit of line, 1.07
core-seconds per second of device; at A084701's opening filter n = 12 it
leaves `1.6×10⁻¹¹`, 34× as many, 6.3 core-seconds per second; at n = 18 it
leaves `4.5×10⁻¹⁶`, 0.035. No constant serves all three, so the launcher
does not carry one: at start, and again at every filter promotion, it
sweeps the launches it is about to run, counts their survivors, times the
classification of a sample, and ramps ceil(need × 2) interpreters
(`size_pool`, drilled) -- on the machine the finds were made on, about
17 at n = 12, 4 at n = 14, 1 from n = 18 on.
The device may run at most 64 launches ahead of the pool: if the pool
ever binds, the device waits, and the `[STATUS]` line says `HOST-BOUND`
and by how much, instead of the backlog growing in memory while the
heartbeat prints the host's rate as the hunt's, which is what a fixed pool
of 3 did at n = 12 on 2026-09-03. The work cursor lags behind launches
whose survivors are still in the pool, so a crash never loses a survivor
it has not looked at. Priced alternatives are in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

## The odds model

Bateman–Horn over the `n` linear forms `f_i(k) = prime(i)·k + s`, with the
singular series computed numerically from the same `w(q,n)` the sieve is
built from — one series for both families, since `w` is sign-independent.
The series is large: the five forced primes contribute `(1/q)/(1−1/q)ⁿ`
each instead of `(1−n/q)/(1−1/q)ⁿ`, and `S(14) = 6.6×10⁵` against
`5.6×10⁴` for the `r·k + 1` ladder of A088250 at the same `n`. Forced
divisibility is a gift to the density as well as to the wheel; it is why
these terms are as small as they are for their `n`.

Stated **before** any sweep (`model_results.json`), measured from each
family's own frontier:

| term | Q1 | median | Q3 | P90 |
|------|----|--------|----|-----|
| A084700 a(14) | 5.57×10¹⁵ | **2.01×10¹⁶** | 5.68×10¹⁶ | 1.22×10¹⁷ |
| A084700 a(15) | 2.39×10¹⁷ | **9.32×10¹⁷** | 2.69×10¹⁸ | 5.81×10¹⁸ |
| A084700 a(16) | 1.31×10¹⁹ | **5.04×10¹⁹** | 1.44×10²⁰ | 3.08×10²⁰ |
| A084700 a(17) | 5.22×10²⁰ | **1.99×10²¹** | 5.63×10²¹ | 1.20×10²² |
| A084701 a(12) | 9.53×10¹² | **2.03×10¹³** | 4.45×10¹³ | 8.58×10¹³ |
| A084701 a(13) | 6.88×10¹³ | **2.41×10¹⁴** | 6.83×10¹⁴ | 1.48×10¹⁵ |
| A084701 a(14) | 4.67×10¹⁵ | **1.86×10¹⁶** | 5.47×10¹⁶ | 1.19×10¹⁷ |
| A084701 a(15) | 2.35×10¹⁷ | **9.26×10¹⁷** | 2.68×10¹⁸ | 5.80×10¹⁸ |

At the scored `2.5×10¹⁷ k/s` those depths are seconds through `a(15)`,
3.4 minutes to `a(16)`'s median and **2.2 hours to `a(17)`'s**
([BENCHMARKS.md](BENCHMARKS.md#wall-clock-at-the-scored-rate)). The
A084701 family's first four open terms were all predicted to sit inside
the first two wheel periods of the time, and they did — all four of
them, `a(15)` riding on `a(14)`, inside period 0 of the unit wheel.

**Validation (gate G11).** If the modelled intensity is right, its
integral up to the first occurrence is `Exp(1)` — mean 1. Pooled over both
families at the ten independently-searched knowns it is **mean 1.30**,
spread 0.19–3.97:

    A084700  a(8) 0.36  a(9) 1.58  a(10) 1.79  a(11) 0.31  a(12) 0.23  a(13) 0.54
    A084701  a(8) 2.08  a(9) 1.96  a(10) 0.19  a(11) 3.97

Pooling is not mixing evidence: it is one model, and each family alone
offers four to six draws, which cannot tell a factor-of-two error from
noise. Ten can, roughly.

**One vote per condition.** Both sequences have riders — A084700's `a(3)`
rides on `a(2)` and `a(5)`–`a(7)` on `a(4)`; A084701's `a(2)` on `a(1)`
and `a(6)`, `a(7)` on `a(5)`. A rider was never searched for, so its `E` is
identically zero and scoring it would manufacture agreement out of nothing.
Only terms that strictly exceed their predecessor are used, and only from
`n = 8`, above the exception zone.

**Read every median above as a floor.** The three ladder projects in this
repository have scored thirteen first occurrences between them at a pooled
optimism factor of **1.92×**, 95% interval **[1.12, 3.60]**, while each
census showed the modelled *intensity* right to a percent or two. Mean
count right, first occurrence late. Budget 2–3× the medians before
expecting a term, and treat a term that arrives on the median as luck.

**How the finds scored.** Each term measured from the one before it
(the window that was actually open when its search began):

| find | `E` at the find | `k / median` |
|------|-----------------|--------------|
| A084700 a(14) = `2.46×10¹⁶` | 0.79 | 1.22 |
| A084700 a(15) = `1.18×10¹⁸` | 0.74 | 1.10 |
| A084700 a(16) = `1.62×10²⁰` | 1.43 | 2.81 |
| A084700 a(17) = `2.45×10²¹` | 0.66 | 0.94 |
| A084700 a(18) = `4.16×10²³` | 1.21 | 2.21 |
| A084701 a(12) = `4.37×10¹³` | 1.37 | 2.16 |
| A084701 a(13) = `2.28×10¹⁵` | 2.85 | 6.44 |
| A084701 a(14) = `1.66×10¹⁷` | 2.67 | 6.17 |
| A084701 a(15) = a(14) | rider: no vote | — |
| A084701 a(16) = `1.67×10¹⁹` | 0.32 | 0.32 |
| A084701 a(17) = `9.05×10²¹` | 1.87 | 4.25 |
| A084701 a(18) = `2.36×10²²` | 0.09 | 0.11 |

Eleven scored finds (A084701's `a(15)` rides on its `a(14)` and casts no
vote): mean `E` **1.27** against the Exp(1) mean of 1 — A084700's five at
0.97, A084701's six at 1.53. The ratios to the median run from 0.11 to
6.4, mean 2.5× and median 2.2×: A084701's `a(13)` and `a(14)` both landed
past their P90 and its `a(18)` under its Q1, which is what Exp(1) looks
like on eleven draws — the pooled mean is the number the model answers
for, and the scatter is the reason to budget 2–3× the medians. For the
open terms, from each live frontier: A084700's `a(19)` Q1 `4.0×10²⁴`,
median `1.2×10²⁵`, Q3 `3.1×10²⁵`, P90 `6.2×10²⁵` — **22% under the v3
ceiling** of `3.317×10²⁴`; `a(20)` median `5.1×10²⁶`, 2% under it.
A084701's `a(19)`, from its `a(18)`: Q1 `2.9×10²⁴`, median `1.0×10²⁵`,
Q3 `2.8×10²⁵`, P90 `5.9×10²⁵` — **0.8% under that family's ceiling** of
`4.95×10²²`, which its campaign has already reached, and 27% under
`3.317×10²⁴` should an N+1 route raise the ceiling to A084700's. The
ceiling, not the rate, is what now bounds both families
([BENCHMARKS.md](BENCHMARKS.md#wall-clock-at-the-scored-rate)).

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # 41 gates and drills; must end ALL GREEN (~1 min)
```

```bash
python score.py                # gates x 6 fingerprinted shapes (~2.5 min)
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py               # A084700 (sign +1), the default
```

```bash
python launch.py --sign -1     # A084701 instead
```

Each family keeps its own checkpoint under its own config key, and neither
campaign will read the other's cursor. The A084700 campaign resumes from
its checkpoint at `k = 4.16×10²³`, period 12774 of the unit wheel, at
filter `n = 19` (the v2 cursor was adopted onto the v3 period, as above,
when the second campaign began). The A084701 checkpoint sits at that
family's ceiling — `k = 4.95×10²²`, period 1519, filter `n = 19` — so a
resumed `--sign -1` prints its banner, finds no period left under the
ceiling and stops. A fresh campaign (a family with no checkpoint) opens
at period 0, clipped at `k = 10⁶`, with the filter at the next open term,
a classification pool sized from a measurement at that filter and ramped
one interpreter at a time, and the frontier promoting itself as terms
land, the pool re-sized at each promotion — which is how the A084701
campaign ran, from `n = 12` to `n = 19` in 2.5 hours. The hunt is
indefinite by default, resumable,
checkpointed every 128 launches (no more often than each save's own cost
allows), and stops cleanly on Ctrl+C with exit 130. **No flag makes it
faster; the defaults are the measured optimum at every filter (CLAUDE.md
5g).** The throttles: `--to` caps the depth, `--stop-on-discovery` exits
once **this run** confirms a find, `--workers` overrides the measured
pool size (1 classifies in the main thread and idles the device while it
does), `--gpu-yield-ms` idles the device after every launch (1 ms against
a 10 ms launch is about 9% of the rate), and `--gentle` is the preset of
one worker and a 2 ms yield, about a sixth of the rate.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **The finds are re-checked from the definition.** G1b takes the twelve
  terms this project claims — five of A084700, seven of A084701 — as
  bare integers and, with sympy alone, confirms each reaches exactly its
  run (a `k` that carries two terms, A084701's `a(14) = a(15)`, exactly
  the last of them), continues the ladder from the published frontier,
  sits on the wheel and stops at a composite — independent of the engines
  and of the evidence files.
- **Three independent implementations.** A sympy-only oracle, a numpy CPU
  engine that marks the dense line with no wheel at all, and a CuPy engine
  that generates wheel survivors and tests them. G9 pins the GPU stream to
  the CPU stream bit-for-bit on 21 populated windows across both signs,
  three wheel depths, `k` space and unit space, and heights from `2×10⁹`
  to `3.3×10²⁴`, the top windows **above 2⁶⁴**, plus period 0 clipped at
  the engine floor on both. G17 pins the production unit wheel to the v2
  wheel over a v2 period at the live filter — the same 293 survivors.
- **A discovery past the proof crossing is proved, not tested.** The
  certificate drill proves the frontier's values by the deterministic
  route and a value past the bound by BLS75 Theorem 1 on the
  factorization of `61·k`, re-verifies it from scratch, and refuses it
  for `N + 2` and as a bare Miller–Rabin claim. Every certificate a
  campaign writes is re-verified before it lands.
- **The adopted cursor is drilled on the live cursor's shape.** A v2
  checkpoint at period 88434 must re-denominate to period 1668 of the
  unit wheel with `u = 0` and nothing pending, keep every find and
  counter, report the adopted `k` as swept, refuse to count or narrate
  the overlap, halt on a discovery-grade run there, and save under its
  own key.
- **The killed set is built three ways**, and the lemma the engine rests
  on is gated, not observed. The oracle walks every residue and tests
  divisibility; the engines invert and negate the rungs; the closed form
  counts distinct residues. G2b, G2c and G3 require all three to agree in
  both directions for every prime below 300 at six filters and both signs;
  G2c also asserts `K(q,n,−1) = −K(q,n,+1)`, the forcing thresholds
  (2, 3, 5, 7, 11 from `n` = 2, 4, 8, 10, 14; 13 only from 27), and that
  every published term obeys them.
- **The benchmark checks itself.** `SCORE2L` and `SCORE1L` sweep the
  *identical absolute window* with the wheel at (23],(37] and at 23 alone —
  33,263× as many periods — and must return the same 23,680 survivors and
  the same checksum, so a bug in the CRT lift shows up inside the
  benchmark.
- **Canaries.** The GPU stream rediscovers `a(8)` and `a(9)` of both
  families as first occurrences at their own filters, sweeping period 0
  from the engine floor with the prefix `[1, floor]` cleared by the
  oracle, so "first" is a claim about the line and not about a window.
- **The protocol is tested in both directions, on both families.** Each
  frontier term is accepted at its true run with a factor witness for its
  stopper; a run one too long, and an earlier term mislabelled as the
  frontier's run, are both rejected.
- **The classification is drilled against itself.** The base-2 screen and
  the all-bases chain must give identical run lengths on real survivors,
  and the pool's chunked answer must reassemble to the serial one.
- **Ceilings raise rather than compute** — both families' primality-proof
  caps, the engine floor and a clip at or below it, the flat wheel's size
  limit, the `u32` first-level modulus, the `gridDim.y` cap on the second
  level, the 32-slot residue list that bounds the filter `n` (v2; v1's
  `2³²`-bit doubled-bitmap ceiling went with the bitmap), a unit that is
  not forced at the filter, and a sign other than ±1. All drilled.
- **The cursor's unit is asserted, not just described.** The checkpoint
  stores `W` and the campaign refuses to read a cursor counted in a
  different period (OPTIMIZATION.md 2.9). Both families' cursor policies
  are put in front of every key they declare, by both readers.
- **The loop is built to the load rules.** The pool is ramped (drilled),
  sized from the measured 1.07 core-seconds per second, the ladder is
  cached on the frontier (75 reads at a standing frontier cost zero model
  rebuilds and a find costs exactly one, drilled), and the interrupt
  writes a snapshot taken at the last classified launch, pending values
  included (drilled).
