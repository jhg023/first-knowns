# linear-ladders — A088250 and its cluster

> Every line of code in this project was authored by Claude (Anthropic's
> AI) at the repository owner's direction. The mathematics, the gates, the
> engines and this document are all machine-written; any results that land
> here will be machine-verified and human-reviewed. That audit trail is
> deliberate and it stays.

**A088250** asks for the least `k` such that `r·k + 1` is prime for every
`r = 1..n`. It is a *linear ladder*: one unknown, `n` linear conditions
whose multipliers are the consecutive integers — the prime ladders of this
repo's prime-ladders project with `prime(i)` replaced by `i`, and the same
engine with one substitution. Fourteen terms are published and the last,
`a(14) = 11,429,352,906,540,438,870`, was found by Giovanni Resta in
**March 2017**; the entry carries no bound of any kind at any open `n`. Six
siblings share the engine, each with its own campaign: **A173750**
(`r = 2..n`), **A125838** and **A125839** (`r·k − 1` for `r = 2..n` and
`3..n`), **A164325** and **A164326** (`(2r−1)·k ± 1`, the odd
multipliers), and **A088651** (`r·k − 1`, `r = 1..n`). Every first
occurrence of A088250 also settles **A202778** (its exact-run version) at
the run's own index and **A071576** (`2ik + 1`) at half the value, and a
find on A088651 settles **A202779** the same way.

**Three new terms of A088250, and a bound** ([RESULTS.md](RESULTS.md)).
The A088250 campaign ran on 2026-09-03, from `k = 10⁶` to the family's
ceiling in 1.26 h, and found

    a(15) = 1,555,360,041,314,493,173,760
    a(16) = 87,117,680,854,368,555,070,680
    a(17) = 1,048,124,771,278,912,649,231,910

each verified three ways with a factor witness for the composite that
stops its run, every value certified (`a(17)` sits past the proof
crossing, and fourteen of its values carry BLS75 certificates), and each
re-verified from disk. Every run is exact, so the same integers are
`A202778(15..17)`, and their halves are `A071576(15..17)`. The sweep then
went on at `n = 18` to the ceiling and found nothing: **`a(18) >
3.3168×10²⁴`**, the first bound of any kind on this sequence at an open
index.

**Four new terms of A125838, and a bound.** The second campaign, 17
minutes to that family's ceiling the same evening, found

    a(15) = 45,187,548,280,664,790
    a(16) = 436,409,209,028,729,276,340
    a(17) = 44,387,933,133,290,055,609,300
    a(18) = 74,882,388,347,598,051,560,340

every value under the deterministic bound, every certificate the
seven-base test itself, each re-verified from disk; then **`a(19) >
1.7305×10²³`** by the sweep to the ceiling. `a(15)` is the integer the
literature already holds as A125839's `a(15)`, and each term is an upper
bound on A125839 at its index.

**Three new terms of A125839, and a bound.** The third campaign, 15
minutes to the same ceiling, found

    a(16) = 14,423,013,361,403,116,470
    a(17) = 771,355,748,787,892,768,500
    a(18) = 6,530,891,065,478,723,143,200

each under A125838's term at its index as the subset of conditions
requires, every certificate the deterministic test, each re-verified
from disk; then **`a(19) > 1.7305×10²³`**.

**Four new terms of A173750 on three integers, and a bound.** The fourth
campaign, 37 minutes to the +1 ceiling, found

    a(16) = 828,196,248,070,762,801,230
    a(17) = 67,335,095,107,785,754,679,430
    a(18) = a(19) = 147,316,106,448,079,863,444,150

the last a run of 19 found while `a(18)` was open, settling both at once
as this family's published `a(12) = a(13) = a(14)` did; every value under
the deterministic bound, each re-verified from disk; then **`a(20) >
3.3168×10²⁴`**.

**Two new terms of A164326, and a bound.** The fifth campaign, 14 minutes
to the lowest ceiling of the seven (`3.317×10²⁴ / 33` at `n = 17`), found

    a(15) = 392,547,927,582,515,694,990
    a(16) = 10,214,000,995,018,156,616,280

every certificate the deterministic test, each re-verified from disk;
then **`a(17) > 9.998×10²²`**.

**Three new terms of A164325, and a bound.** The sixth campaign, an hour
to the +1 ceiling, found

    a(16) = 1,284,243,585,711,408,422,100
    a(17) = 317,674,273,854,740,299,136,640
    a(18) = 511,721,589,397,871,969,516,400

the last two past the proof crossing and proved by BLS75 certificates
(12 and 15 of them), each re-verified from disk; then **`a(19) >
3.3168×10²⁴`**.

**One new term of A088651, and a bound.** The seventh campaign, 12
minutes to the crossing at `n = 17`, found

    a(16) = 43,263,866,546,732,976,414,270

which is also `A202779(16)`, every certificate the deterministic test,
re-verified from disk; then **`a(17) > 1.942×10²³`**.

**Two more terms of A164326, past the old ceiling, and a bound (v3).**
The eighth campaign — the first under the 10⁴⁰ ceiling below — resumed
that family from its v2 cursor and ran 7.5 hours overnight on
2026-09-04, finding

    a(17) = 2,071,342,181,735,785,633,264,590
    a(18) = 9,606,289,803,039,023,735,440,800

every one of whose 35 values lies past the deterministic bound: the
first discoveries this repository has proved by the **N+1 route**, BLS75
Theorem 15 on `N + 1 = (2r−1)·k`, all 35 certificates re-verified from
disk; then **`a(19) > 1.6049×10²⁵`** by the sweep to where it was stopped.

**v3 (2026-09-04): one ceiling of 10⁴⁰ for every family.** The v2
campaigns stopped where their *proofs* stopped — the deterministic
Miller–Rabin bound on `k` for the +1 families, the proof crossing for the
−1 ones, which had no certificate route at all. v3 adds the **N+1
certificate route** to huntlib (BLS75 Theorem 15: a Lucas sequence per
prime of `N + 1 = m·k`, one shared discriminant), makes both routes
**recurse into the factors of `k`** past the bound, and moves the ceiling
to where the *cost* of a certificate was measured rather than where a
test stops being one: `huntlib.ceiling.K_CEIL = 10⁴⁰`, at which a
worst-case `k` (the unit times two 18-digit primes) is factored and a
whole run proved in about a second. The wheel, the unit, the sieve and
the segment are v2's, so every fingerprint reproduces and every v2
cursor carries over whole: each campaign resumes at its v2 filter.

**Status: ACTIVE.** Twenty-two new terms across all seven families,
found and verified 2026-09-03/04 by eight campaigns totalling under
twelve hours of device, and a searched-empty bound on the next term of
each. Every campaign resumes from its cursor under the 10⁴⁰ ceiling; the
model puts A125839's `a(19)` and A088651's `a(17)` at 93% within a
night's sweep each, A164326's `a(19)` and the +1 families' next terms at
medians of `10²⁶` and above ([RESULTS.md](RESULTS.md), "What is open
now"). 44 gates and drills green, six benchmark shapes reproduced, every
resumed filter priced.

## The problem

    A(F, n) = least k >= 1 with m*k + s prime for EVERY multiplier m of
              family F at index n

The conditions nest, so every `A(F, ·)` is non-decreasing and a single
lucky `k` can settle several terms at once — A088250's `a(7) = a(8) =
512,820`, A173750's `a(12) = a(13) = a(14)`, A164325's `a(13) = a(14)`.

| family | forms | offset | published frontier | found by | opens at |
|---|---|---|---|---|---|
| [A088250](https://oeis.org/A088250) | `r·k + 1`, `r = 1..n` | 1 | `a(14) = 11,429,352,906,540,438,870` | Giovanni Resta, Mar 31 2017 | `n = 15` |
| [A173750](https://oeis.org/A173750) | `r·k + 1`, `r = 2..n` | 1 | `a(15) = 4,646,092,391,146,085,880` | Giovanni Resta, Mar 31 2017 | `n = 16` |
| [A125838](https://oeis.org/A125838) | `r·k − 1`, `r = 2..n` | **2** | `a(14) = 8,047,290,924,923,250` | Giovanni Resta, Mar 29 2017 | `n = 15` |
| [A125839](https://oeis.org/A125839) | `r·k − 1`, `r = 3..n` | **3** | `a(15) = 45,187,548,280,664,790` | Giovanni Resta, Mar 30 2017 | `n = 16` |
| [A164325](https://oeis.org/A164325) | `(2r−1)·k + 1`, `r = 1..n` | 1 | `a(15) = 10,718,654,377,787,155,800` | Giovanni Resta, Apr 01 2017 | `n = 16` |
| [A164326](https://oeis.org/A164326) | `(2r−1)·k − 1`, `r = 1..n` | 1 | `a(14) = 68,086,992,545,221,650` | Giovanni Resta, Mar 31 2017 | `n = 15` |
| [A088651](https://oeis.org/A088651) | `r·k − 1`, `r = 1..n` | 1 | `a(15) = 53,792,264,108,455,702,830` | Jens Kruse Andersen, May 02 2008 | `n = 16` |

Every entry was re-checked on oeis.org on 2026-09-03 before the tables
were frozen (the `%I` revision stamps match the local export of
2026-09-01). A125838 and A125839 carry `hard`; none has a b-file bound.

**Two entries ride on the finds without being hunted.**
[A202778](https://oeis.org/A202778) is the *exact-run* version of A088250
(`x·k + 1` prime for `x = 1..n` and composite at `n + 1`): it equals
A088250(n) wherever A088250(n) has run exactly `n`, and stays open at a
rider index (its `a(7) = 8,224,860` against A088250's 512,820, which has
run 8). [A071576](https://oeis.org/A071576) (`2ik + 1` prime for
`i = 1..n`) is A088250(n)/2 for `n ≥ 3`, because `k` is even from `n = 2`.
[A202779](https://oeis.org/A202779) is to [A088651](https://oeis.org/A088651)
what A202778 is to A088250 — the handoff for this project named A202779,
and A088651 is its monotone version, which is what an engine hunting
"run ≥ n" actually finds; `--family A202779` opens the A088651 campaign.
G2d asserts all three identities on every published term, and every
evidence file records what its find settles in them (`also_settles`).

Why they are open rather than merely unfinished: the density of qualifying
`k` falls like `1/(log k)ⁿ`, so each extra condition costs a further factor
of roughly `log k` worth of line. All seven are conjecturally infinite for
every `n` — residue `0` survives every prime (`k ≡ 0 (mod q)` makes every
value `≡ s ≠ 0`), so no constellation here has a fixed prime divisor at
any `n` (proved in `lladder_reference`), Dickson's conjecture applies, and
a find **confirms** the guiding conjecture and can never refute it.

## The mathematics of the engine

Fix a prime `q` and a multiplier `m` of the family at index `n`. If `q | m`
the form `m·k + s` is `≡ s (mod q)` and never divisible by `q`: that rung
kills nothing. For `q ∤ m`, `q | m·k + s` exactly when `k ≡ −s·m⁻¹ (mod q)`,
so the residues of `k` that `q` kills are

    K(q,n,F) = { -s * m^-1 mod q : m in mults(F, n), q does not divide m }

and the engine sieves `k` against `K(q,n,F)` and nothing else. Inversion
and negation are bijections, so its size is

    w(q,n,F) = |K(q,n,F)| = #{ distinct nonzero residues of the multipliers mod q }

— proved in `lladder_reference.py` and gated three ways (G2b, G2c, G3:
the closed form, direct divisibility, and the engines' construction must
all agree, for every family, every prime below 300 and six filters). Three
consequences:

- **`w` does not depend on the sign**: `K(q,n,−1) = −K(q,n,+1)`, so a
  family and its sign twin have identical table sizes, identical survival
  curves, one singular series and one compiled kernel.
- **Consecutive multipliers cover the residues fast.** For the `1..n`
  family `w(q,n) = min(n, q − 1)`: every prime `q ≤ n + 1` is **forced**
  (`k ≡ 0 mod q` is the only surviving residue), and every larger prime
  kills the maximum `n` residues. The forcing thresholds are closed forms
  per family (`1..n`: `q` from `n = q − 1`; `2..n`: `q + 1`; `3..n`:
  `q + 2`; the odd multipliers: `n = q`), proved as G2c. So A088250's
  `a(15)` is a multiple of `30030` and its `a(16)` of `510510`, A088651
  opens with 17 already forced, and every published term above the
  exception zone obeys its forced primes.
- **The wheel is therefore extreme.** At A088250's opening filter the
  (37],(47],(59] wheel in unit space holds `315,392 × 23,296 × 1,672`
  residues per period of `1.92×10²¹`: `6.4×10⁻⁹` of the line, 110× thinner
  than prime-ladders' opening wheel from the same primes, and `5.9×10⁻¹⁰`
  at `n = 17`. The kernel runs at `1.6–2.4×10¹¹` candidates per second at
  every opening, which the wheel turns into `8.4×10¹⁸` k per second at
  the densest −1 opening and `4.0×10²⁰` at A088250's `n = 17`.

**The kernel is prime-ladders' v3.1, transferred and re-tuned (v2).** The CPU engine
materialises the dense `k` line and marks arithmetic progressions into it,
with no wheel at all. The GPU engine never forms the line: it generates
only the `k` that survive the three-level wheel by CRT recombination and
*tests* each against packed forbidden-residue tables by Barrett
magic-multiply, bailing out at the first kill, with the divergence
compacted inside the block and the deep tail swept as compaction rounds
over global queues with several lanes per item. Nothing in that kernel
knows about the forms: every problem-specific object — the wheel tables,
the masks and residue lists, the CRT-combined prefix groups, the survival
curve the compaction points are derived from — is built from
`killed_residues(q, n, F, unit)`, and the parity gate G9 pins the result to
the CPU engine bit for bit on 22 populated windows across six families,
one-, two- and three-level wheels in `k` space and in unit space, from
`k = 2×10⁹` to `3.3×10²⁴` with the top windows above `2⁶⁴`.

**Unit space.** Every candidate at a campaign filter is a multiple of the
forced primes, so the device sweeps `k' = k / unit` with the kill sets
`unit⁻¹·K(q,n,F) mod q` (a bijection, so nothing about the survival curve
changes) and the unit's primes left out of the wheel. The unit is fixed per
family at its opening filter (30030 for six of the seven, 510510 for
A088651) and stays: a forced prime stays forced as `n` grows, so the unit
remains admissible at every promotion and the period `W` — the cursor's
denomination — never moves inside a campaign. When a promotion forces a
new prime (17 at A088250's `n = 16`, 19 at `n = 18`) that prime simply
keeps one residue in the wheel; the candidates are identical either way.
**The wheel reaches 59 (v2).** v1 ran (31],(41],(53] and had measured
the wheel to 59 at 1.00× at `n = 17` and 0.83× at A125838's opening and
declined it; v2 found both numbers were the configuration and not the
wheel — a group budget that stopped the wheel's first triple of sieve
primes (61·67·71) combining into one lookup, and a tail-queue cap that
sent 60% of a `2×10¹⁰`-candidate launch through the in-block fallback —
and re-measured it paired at **1.27× / 1.50× / 1.20× / 1.32×** at
`c = 15 / 16 / 17 / 18` forms and within 5% at `c = 14`
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v2). The same pass pinned two
things no fingerprint can see and that had been read as tuning cliffs:
the driver's shared/L1 carveout, now set explicitly (a few KB more shared
per block used to drop the group tables out of L1, 0.2–0.3×), and the
register allocation of the unrolled body, which the engine now measures
after compiling and guards (G18: every opening compiles to ≥ 8 blocks per
SM; v1 had shipped every `c = 16` opening at 5 without knowing).

**A window may start inside period 0.** A period is `1.92×10²¹` of line
and every family's frontier sits inside the first one. `sweep` takes
`k_min`: the device sieves the whole period and the host drops every
survivor below it — exact, because a survivor above `k_min > q2` is a
survivor of a sieve whose every prime is below it. The campaign opens at
period 0 clipped at `K_START = 10⁶`; below that the least-claim is
monotonicity (every frontier is above `8×10¹⁵`), above it our own
coverage. The canaries rediscover `a(8)` and `a(9)` (or the two nearest
terms a mini-hunt affords) of all seven families by sweeping period 0 from
the floor, in `k` space and in unit space.

**Candidates are carried as `(k, off)` from the first commit**, with the
launch base a host-side big integer folded once per launch into the
per-prime and per-group tables (G15: the stream does not depend on where
the base was put, at bases up to `10³⁰`; G9 pins the stream against the
CPU engine on two windows hard against `10⁴⁰`). No machine word bounds
the search; the enforced ceiling is the **measured certificate budget**,
`huntlib.ceiling.K_CEIL = 10⁴⁰` (G10, one number for all seven families).

**Where the proofs come from.** The largest value is `m_max·k + s`, and
below the **proof crossing** `k_proof(n, F) = (3.317×10²⁴ − s − 1) / m_max`
— `2.2×10²³` at `n = 15`, `1.7×10²³` at `n = 19` — every classification
the hunt makes is a deterministic Miller–Rabin proof. Past it the same
seven-base chain is a strong probable-prime test; the census is still a
count and a `[NEAR]` still a health check, and a *discovery* is proved
by the value's own structure: `N − s = m·k` is completely factored once
`k` is (`huntlib.certificate.factor_full`, the multiplier's own factors
folded in — `15 = 3·5`), so **BLS75 Theorem 1 on `N − 1`** (the +1
families) or **Theorem 15 on `N + 1`** — the N+1 test, a Lucas sequence
`U(P, Q)` per prime of `m·k` with one shared discriminant `D`, `(D/N) =
−1`, `N | U_{N+1}` and `gcd(U_{(N+1)/q}, N) = 1` (the −1 families) —
proves every value of the run on that one factorization. A prime factor
of `k` above the bound is admitted only with a **subproof** of its own,
found by the same machinery on whichever of `p ∓ 1` factors, so a
certificate is a finite tree whose leaves are deterministic tests. Every
certificate is re-verified from scratch before it is written
(`certify_run`), and the drill proves both routes at the crossing and
**at the ceiling** on both signs, with the recursion exercised and the
subproof shown unstrippable. What bounds `k` is therefore the *cost* of
that certificate per discovery — factoring `k` once, then a witness
search per value — and `huntlib.ceiling` measured it: a worst-case `k`
(the unit times a balanced semiprime) at `10⁴⁰` is factored in 0.2–3 s
and a run of values proved in a further second
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3). The crossing is logged
once per filter as a `[MILESTONE]` and never stops the run.

**Coverage is coarser than work, and the checkpoint carries both**
(CONVENTIONS.md "Two cursors"). The wheel emits a period's candidates in
`(t, s, u)` order, so `swept to` advances one period at a time and is the
only thing a least-claim rests on, while the work cursor `(j, u)` advances
every launch. Values classified mid-period are held *in the checkpoint*
and narrated in `k` order when the period closes; a find costs at most one
period of over-sweep — about a minute at the opening, five seconds at
`n = 17`. Because periods can close every few seconds at the deeper
filters, the period-close save and log line are rate-limited (a save
every few seconds would be tens of thousands of chances per campaign for
a scanner's handle to land in the rename window); the boundary snapshot
is still taken at every close, so an interrupt writes the latest one.

**The host classifies in a ramped pool sized from a measurement at the
campaign's own filter.** A survivor costs 14.5 µs with a base-2 strong-test
screen confirmed by the deterministic chain at run ≥ 8, and how many
arrive per second depends on the filter: 46,000 at A088250's opening
(0.66 core-seconds per second), 117,000 at A125838's (1.7), 6,900 at
`n = 17` (0.10). So at start, and again at every promotion, the launcher
sweeps the launches it is about to run, counts their survivors, times a
sample, and ramps `ceil(need × 2)` interpreters (`size_pool`, drilled) —
two at A088250's opening, three or four at the −1 openings, one from
`n = 16` on. The device may run at most 64 launches ahead of the pool; if
the pool binds, the device waits and the `[STATUS]` line says `HOST-BOUND`
and by how much. The loop is measured device-bound at every opening
(sieve plus tail rounds are 95–101% of the pipelined wall clock;
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).

## The odds model

Bateman–Horn over the forms `f_m(k) = m·k + s`, with the singular series
computed numerically from the same `w(q,n,F)` the sieve is built from —
one series per w-class, since `w` is sign-independent. The series is
*smaller* than the prime ladders' at the same `n` (`S(14) = 2.3×10⁴`
against `6.6×10⁵`) because consecutive multipliers kill more residues per
prime than the first `n` primes do; fewer `k` qualify per unit of line and
the terms are larger for their `n`, but the wheel thins the candidates by
exactly the same factors, so a unit of device time covers far more line.

Stated **before** any sweep (`model_results.json`, written 2026-09-03
and regenerated 2026-09-04 with the v3 ceiling in its `under_the_ceiling`
field; the predictions themselves are unchanged), measured from each
family's published frontier. The "under the ceiling" column is against
the **v2 ceilings** the campaigns actually ran to — the deterministic
bound on `k` for the +1 families, the proof crossing for the −1 ones —
which is what the finds below were scored against:

| term | Q1 | median | Q3 | P90 | under the ceiling |
|------|----|--------|----|-----|-------------------|
| A088250 a(15) | `7.1×10¹⁹` | **`2.0×10²⁰`** | `4.9×10²⁰` | `9.7×10²⁰` | ~100% |
| A088250 a(16) | `6.5×10²¹` | **`2.3×10²²`** | `6.2×10²²` | `1.3×10²³` | ~100% |
| A088250 a(17) | `4.7×10²³` | **`1.7×10²⁴`** | `4.5×10²⁴` | `9.2×10²⁴` | 68% |
| A088250 a(18) | `6.0×10²⁵` | **`2.1×10²⁶`** | | | 4% |
| A173750 a(16) | `6.2×10¹⁹` | **`1.9×10²⁰`** | `5.0×10²⁰` | `1.0×10²¹` | ~100%; a(17) `9.2×10²¹`; a(18) `1.8×10²⁴`, 66% |
| A125838 a(15) | `6.5×10¹⁷` | **`2.3×10¹⁸`** | `6.3×10¹⁸` | `1.3×10¹⁹` | ~100%; a(16) `1.7×10²⁰`; a(17) `9.1×10²¹`; a(18) 13% |
| A125839 a(16) | `8.2×10¹⁷` | **`2.7×10¹⁸`** | `7.0×10¹⁸` | `1.5×10¹⁹` | ~100%; a(17) `1.0×10²⁰`; a(18) `9.7×10²¹`; a(19) 18% |
| A164325 a(16) | `1.4×10²¹` | **`4.9×10²¹`** | `1.3×10²²` | `2.7×10²²` | ~100%; a(17) `7.7×10²³`, 85%; a(18) 9% |
| A164326 a(15) | `1.7×10¹⁹` | **`6.2×10¹⁹`** | `1.7×10²⁰` | `3.6×10²⁰` | ~100%; a(16) `4.8×10²¹`; a(17) 16% |
| A088651 a(16) | `6.8×10²¹` | **`2.3×10²²`** | `6.3×10²²` | `1.3×10²³` | 96%; a(17) `1.7×10²⁴`, 15% |

At the scored rates those depths are seconds and minutes through every
family's first open term and hours to A088250's `a(17)`
([BENCHMARKS.md](BENCHMARKS.md#wall-clock-at-the-scored-rate)).

**Validation (gate G11).** If the modelled intensity is right, its
integral up to the first occurrence is `Exp(1)` — mean 1. Over the 46
independently searched knowns of the seven families it is **mean 0.86**,
spread 0.05–3.06, per family:

    A088250 0.93 (6)   A173750 0.56 (6)   A125838 1.01 (7)   A125839 0.73 (7)
    A164325 0.79 (6)   A164326 1.22 (7)   A088651 0.73 (7)

A088250's own: `a(9) 2.09, a(10) 0.95, a(11) 0.14, a(12) 0.12, a(13) 0.05,
a(14) 2.23`.

**One vote per condition.** Every family has riders — terms equal to their
predecessor because one `k` cleared two rungs at once. A rider was never
searched for, so its `E` is identically zero and scoring it would
manufacture agreement out of nothing. Only terms that strictly exceed
their predecessor are used, and only from `n = 8`, above the exception
zone.

**Read every median above as a floor.** The four ladder projects in this
repository have scored their first occurrences at 1.9–2.5× their medians
on average while every census showed the modelled *intensity* right to a
percent or two. Budget 2–3× the medians before expecting a term, and treat
a term that arrives on the median as luck.

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # 44 gates and drills; must end ALL GREEN (~120 s)
```

```bash
python score.py                # gates x 6 fingerprinted shapes (~100 s)
```

```bash
python launch.py --status --family A088250   # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py               # A088250, the default
```

```bash
python launch.py --family A125838    # any of the seven; A202778/A202779 alias A088250/A088651
```

Each family keeps its own checkpoint under its own config key, and no
campaign will read another's cursor. **Every family's v2 checkpoint is
in the tree and v3 resumes it**: the v3 key accepts the v2 key (the
identical line — same wheel, unit, sieve depth and period `W`, every
fingerprint reproduced), so `python launch.py --family <name>` continues
at the filter after that family's frontier, from its v2 ceiling, with
its census and finds intact (drilled on all seven real checkpoints).
A fresh campaign (`--fresh`, only ever deliberately) opens at period 0,
clipped at `k = 10⁶`, with the filter at the next open term, a
classification pool sized from a measurement at that filter and ramped
one interpreter at a time, and the frontier promoting itself as terms
land, the pool re-sized at each promotion. The hunt is indefinite by
default, resumable, checkpointed at every period close (no more often
than every two seconds) and every 32 launches inside a period, and stops
cleanly on Ctrl+C with exit 130. **No flag makes it faster; the defaults
are the measured optimum at every opening (CLAUDE.md 5g).** The
throttles: `--to` caps the depth, `--stop-on-discovery` exits once
**this run** confirms a find, `--workers` overrides the measured pool
size (1 classifies in the main thread and idles the device while it
does), `--gpu-yield-ms` idles the device after every launch (1 ms
against a 5 ms launch is about 17% of the rate), and `--gentle` is the
preset of one worker and a 2 ms yield, about a third of the rate.

**What the first lines of a RESUMED campaign should say** (v3; the
numbers are the harness measurements in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3). For `--family A164326`:
a `[STAGE]` line `checkpoint MIGRATED from a164326-v2-... to a164326-v3-...`,
then `resume at period 52, u = 0 (k = 99,983,538,208,019,057,231,640)`,
the `a(17)` quantiles from the model, a `[MILESTONE]` saying the sweep
is already past the proof crossing `k_proof(17, A164326) = 1.005e+23`
with the certificate route named, and a pool line `classification pool:
1 workers (measured on ~150 launches, 1.00 s of device at 1.7e+20 k/s:
~6,000 survivors/s x ~13 us = 0.08 core-s per s, x2 margin)`. The first
`[STATUS]` at 30 s: `swept to 9.99835e+22` or a period or two above it
(a period is `1.92×10²¹`, about 11 s at this filter), `A164326 filter
n = 17`, a rate near `1.8e+20 k/s`, `census ... 16:1`, `finds 2`,
`pool 1`, and `next a(17) median 1.05e+24 (ETA ~1.5 h)`. The
line-per-second, the pool of 1 and the rung named are the three things
to check; a `HOST-BOUND` fragment or a rate under 90% of that is a
defaults bug.

**What the first lines of a FRESH campaign should say** (the rule 5g
acceptance test as it was run for v2, kept for `--fresh`). For A088250
with no flags:
the pool line `classification pool: 2 workers (measured on 25 launches,
1.00 s of device at 2.9e+19 k/s: 58,500 survivors/s x 13.1 us = 0.77
core-s per s, x2 margin)` (the selftest's wiring drill takes the same
measurement and printed exactly that). A period is `1.92×10²¹` of line,
about 65 s at this rate, so the first `[STATUS]` line at 30 s is inside
period 0: `swept to 0`, `period 0 [0, 1.9228e+21) 45%`, `A088250 filter
n = 15`, a rate near `3.0e+19 k/s`, `finds 0`, `pool 2`, `next a(15)
median 1.98e+20 (ETA inside the period being worked)` — every rung of
`a(15)` sits inside period 0, and a rung inside the period being worked
says so rather than carrying a time — and `P(a(15) under the claim) = 0%`,
because the coverage claim does not move until the period closes. The
second line (60 s) reads the same at ~90%. Then `period 0 complete: swept
to 1,922,760,350,154,212,639,070`, and `a(15)` (median `2.0×10²⁰`, 96%
inside period 0) has most likely been narrated as a `[DISCOVERY]` banner
with its `also settles` lines, followed by `filter follows the frontier:
n = 15 -> 16` and a re-sized pool of 1; the third `[STATUS]` then reads
`filter n = 16`, a rate near `1.4e+20 k/s`, `finds 1`, `pool 1`, `next
a(16) Q1 6.5e+21 (ETA …)` and a small `P(a(16) under the claim)`. Either
way: no `HOST-BOUND` fragment, the rate at the benchmark's for the filter
shown, and `next` naming the open term's rung. A rate under 90% of the
benchmark's, a `HOST-BOUND` fragment, or a `next` naming a settled term
is a defaults bug, not a flag to reach for.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle, a numpy CPU
  engine that marks the dense line with no wheel at all, and a CuPy engine
  that generates wheel survivors and tests them. G9 pins the GPU stream to
  the CPU stream bit-for-bit on 22 populated windows across six families,
  three wheel depths, `k` space and unit space (2310, 30030, 510510), and
  heights from `2×10⁹` to `3.3×10²⁴`, the top windows **above 2⁶⁴**, plus
  period 0 clipped at the engine floor. G17 pins the production unit wheel
  to a k-space wheel over one of its periods at the opening filter — the
  same 1,304 survivors.
- **The killed set is built three ways**, and the lemmas the engine rests
  on are gated, not observed. The oracle walks every residue and tests
  divisibility; the engines invert and negate the multipliers; the closed
  form counts distinct residues. G2b, G2c and G3 require all three to
  agree in both directions for every prime below 300 at six filters and
  all seven families; G2c also asserts `K(q,n,−1) = −K(q,n,+1)`, the
  forcing thresholds as closed forms, and that every published term above
  the exception zone obeys them. G3 refuses a unit one filter before it is
  forced.
- **The derived claims are gated on the literature.** G2d asserts
  `A202778(n) = A088250(n)` and `A202779(n) = A088651(n)` exactly at the
  indices where the monotone term has run exactly `n` (and that they
  exceed it at the rider indices), and `A071576(n) = A088250(n)/2` for
  `n ≥ 3`, on all 41 published terms; the protocol drill checks the
  `also_settles` records a find would write.
- **A discovery past the proof crossing is proved, not tested — on
  both signs, and at the ceiling.** The certificate drill proves the
  A088250 frontier's 14 values by the deterministic route; a value past
  the bound on each sign (`15·k + 1` at `k = 2.2×10²³` by BLS75 Theorem 1
  on `N − 1`, `19·k − 1` at `k = 1.7×10²³` by Theorem 15 on `N + 1`,
  each factored completely), re-verified from scratch and refused for
  `N + 2` and as a bare Miller–Rabin claim; and then at `k ≈ 10⁴⁰` on
  both signs a worst-case `k` (the unit times two 18-digit primes) and a
  `k` with a 30-digit prime factor above the bound, whose certificate
  must carry a subproof that cannot be stripped. huntlib's own gates
  drill the N+1 arithmetic (a tampered Lucas witness, a neighbouring
  `N`, a truncated factorization, a mislabelled theorem, a constructed
  composite) and the machinery at `10⁴⁰`. Every certificate a campaign
  writes is re-verified before it lands.
- **The benchmark checks itself.** `SCORE2L` and `SCORE1L` sweep the
  *identical absolute window* with the wheel at (23],(37] and at 23 alone
  — 33,263× as many periods — and must return the same 123 survivors and
  the same checksum, so a bug in the CRT lift shows up inside the
  benchmark.
- **Canaries.** The GPU stream rediscovers two published terms of every
  family as first occurrences at their own filters, sweeping period 0 from
  the engine floor with the prefix `[1, floor]` cleared by the oracle, in
  `k` space and in unit space (15 rediscoveries).
- **The protocol is tested in both directions, on every family.** Each
  frontier term is accepted at its true run with a factor witness for its
  stopper; a run one too long, and an earlier term mislabelled as the
  frontier's run, are both rejected.
- **The classification is drilled against itself.** The base-2 screen and
  the all-bases chain must give identical run lengths on real survivors,
  the pool's chunked answer must reassemble to the serial one, and the
  families whose rungs start at 2 or 3 must count from there.
- **Ceilings raise rather than compute** — the one `10⁴⁰` ceiling on
  both signs (tight to one wheel period; the last period under it is
  accepted and the next refused), the engine floor and a clip at or
  below it, the flat wheel's size limit, the `u32` first-level modulus,
  the `gridDim.y` cap, the 32-slot residue list that bounds the form
  count, a unit that is not forced at the filter, and an unknown family.
  All drilled.
- **The cursor's unit is asserted, not just described.** The checkpoint
  stores `W` and the campaign refuses to read a cursor counted in a
  different period (OPTIMIZATION.md 2.9). All seven families' cursor
  policies are put in front of every key they declare — the v3 key and
  the v2 key it inherits — by all three readers, no policy reads another
  family's key, and the v2-resume drill builds a campaign on each
  family's real v2 checkpoint and checks it continues under the new
  ceiling at the right filter with its finds and census intact.
- **The loop is built to the load rules.** The pool is ramped (drilled),
  sized from a live measurement at the campaign's filter (drilled, and
  re-sized inside the noise band without thrashing), the device is bounded
  to 64 launches ahead of it (drilled, with the wait timed), the ladder is
  cached on the frontier (75 reads at a standing frontier cost zero model
  rebuilds and a find costs exactly one, drilled), the period save is
  rate-limited (drilled), and the interrupt writes a snapshot taken at the
  last classified launch, pending values included (drilled).
