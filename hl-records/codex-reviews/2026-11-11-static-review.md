# hl-records: static mathematical review

> **Authorship:** Codex (OpenAI), 2026-11-11, at the repository owner's
> direction. The implementation and historical measurements retain their
> Claude attribution. This is a static mathematical analysis and an
> implementation handoff. No project code, tests, benchmarks, searches,
> CUDA compilation, or GPU queries were executed.

| Snapshot | Value |
|---|---|
| Repository HEAD | `83e5724ed335e68d5bba5592f3222af585db397e`, the last published commit, with unpublished local commits for another project on top |
| Initial working tree | Dirty. The entire `hl-records/` directory was untracked; shared documents and another project also had pre-existing changes. HEAD alone does not identify this implementation; the hashes in section 7 do. |
| Implementation | Engine v2; all five public Python roles and `hlc_model.py` |
| State | An owner-started hunt was running. The saved checkpoint was read briefly; neither it nor the process was changed. |
| Review edits | This report, the local review ledger, project README attribution/navigation, and the repository review index |
| Method | Source and stored-data inspection, independent mathematical derivations, primary-source checks, source hashes, and lightweight arithmetic |

Follow [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). All executable validation
and performance experiments below belong to a later implementation task.
The owner alone starts campaigns. Source line numbers refer to the hashed
snapshot and are accompanied by function names because lines can move.

## 1. Executive assessment and target family

**There are significant algorithmic opportunities.** The strongest are a
tighter unconditional rejection bound using already available local
characters, an exact descent to the fundamental discriminant before
class-group work, and an exact modular-root enumerator that can first
accelerate confirmation and then be evaluated as a sparse production
fallback.

The central performance fact is already measured in this project:
at `k = 10^12`, the prefilter leaves about **0.285%** of odd k to count,
but the flagged three-squares tabulation still takes **1.940 of 2.530
seconds per window**, about **77%**. It visits representations belonging
to the whole window to find those rare flagged values. Reducing the flag
count alone does not remove that traversal. A substantial next gain must
shorten class-group work, avoid parts of the representation walk, or
replace that walk with work on the unresolved discriminants.

Those timings are **Previously measured here**, from the 2026-11-11 v2
rate table in [BENCHMARKS.md](../BENCHMARKS.md), at floor 7.5 on one RTX
4090. They were not repeated during this review.

| ID | Priority | Recommendation | Evidence / origin |
|---|---|---|---|
| [HLC-001](#hlc-001-tighten-the-bound-with-local-euler-factors) | P2, first mathematical experiment | Tighten the E upper bound and reject directly from a lower bound on h | Proved bound; new application here; runtime unmeasured |
| [HLC-002](#hlc-002-descend-to-the-fundamental-discriminant) | P2, first structural experiment | Use the full conductor formula before group computations | Proved identities and exact factor extraction; new application here |
| [HLC-003](#hlc-003-enumerate-modular-roots-and-price-a-sparse-fallback) | P2, largest structural opportunity | Replace the all-coefficient exact enumerator; price a sparse or residue-specific fallback | Proved bijection and work bound; new algorithm here; crossover unknown |
| [HLC-004](#hlc-004-finish-the-squared-base-order-experiment) | P2, bounded follow-up | Evaluate the already proposed order-of-the-square algorithm | Known unfinished idea; the log estimates roughly 6%, not a measurement |
| [HLC-005](#hlc-005-price-selective-use-of-published-class-number-data) | P3, conditional alternative | Price selective use of the now-located published class-group data | Available dataset observed; transfer and I/O costs unmeasured |
| [HLC-006](#hlc-006-change-the-validation-contract-deliberately) | P1 prerequisite to a changed filter | Update health checks, independent expectations, census preservation and coverage migration together | Observed source dependencies; implementation safeguard |

The performance targets should be named by **height**: `10^12`, with
`3*10^11` retained for historical comparison and `3*10^12` for scaling.
The pre-run labels a(24) and a(25) are no longer the current open indices.
The production floor remains 7.5 after the opening, regardless of the
record, so the existing height measurements remain relevant.

## 2. Current mathematics and saved search state

### 2.1 Definition, representations and exceptional cases

There is one family, [A331940](https://oeis.org/A331940): successive k > 0
whose polynomial `x^2 + x + k` sets a strictly larger Hardy-Littlewood
constant. Even k has C = 0. For odd k put `n = 4k - 1 = 8m + 3` and
`D = -n`. These n are discriminant magnitudes, not sequence indices.

For n > 3, the source derives

```
C(k) = 4 sqrt(n) E(n) / (3 pi h(-n)),
E(n) = product over odd primes p of e_p(n),
e_p = 1 - 1/(p-1)^2  if (-n|p) = +1,
      1              if p divides n,
      1/(1-p^-2)     if (-n|p) = -1.
```

The n = 3 unit group changes the coefficient; it must remain a separate
case. Nonfundamental discriminants cannot be discarded: removing a
conductor prime's local factor can increase C. The project's example
`n = 163*41^2`, `k = 68501`, is a useful regression case.

The independent oracle enumerates primitive reduced forms literally
([hlc_reference.py](../hlc_reference.py), `class_number_forms`, line 82).
The CPU window engine sieves reduced forms; the GPU window engine counts
odd triples `x >= y >= z >= 1`, with weights 6, 3, 1. Both obtain
`T(n) = 3H(n)`, including imprimitive forms with their Hurwitz weights.
The host extracts the exact primitive class number using the conductor
formula. The production prefilter proves lower bounds from class-group
orders, genus theory, two-generator subgroup indices and a partial
conductor correction; undecided cases get an exact three-squares count.

The default window is `2^22` odd k, a span of `2^23` in k. Flagged
tabulation uses sub-windows of `3*2^18` counters. There is no fixed
congruence wheel. `PRE_MIN_N = 2^20` keeps the small range on full
tabulation. The campaign ceiling is `k = 10^13`; the arithmetic bound is
`n < 2^46`. Count storage is uint32, while products, plans and intermediate
form computations have separate bounds stated in
[hlc_gpu.py](../hlc_gpu.py), lines 60-77. No primality-proof crossing is
involved: this is a class-number/constant problem.

### 2.2 Stored coverage, with explicit freshness limits

At **2026-11-11 19:55:10 America/New_York**
(`2026-11-12T00:55:10Z`), a brief read of
`campaign_checkpoint.json` gave:

| Item | Stored value |
|---|---|
| `next_k` | 11,920,211,969 |
| Coverage claim | Every odd k strictly below `next_k` processed; even k excluded mathematically |
| Frontier | 30 terms: 11 known canaries and 19 discoveries |
| Latest stored term | a(30) = 11,410,046,357 |
| Latest stored C | 9.328963776429486263794142280993831 |
| `clock_s` / health checks | 3769.776440382 / 28 |

These are **Observed in source/data**, not fresh verifications or new
discoveries made by this review. The corresponding
[a(30) evidence](../evidence/hlc_record_a30_k11410046357.json) records the
three legs and a creation time of `2026-11-12T00:44:50Z`. The hunt may have
advanced after the read. Its unfinished work is not included in the saved
contiguous floor.

README, RESULTS and the evidence README still contain pre-run statements
that no campaign has run. This report records that discrepancy; it does
not publish or rewrite the running campaign's results. The model file is
explicitly a **pre-run** prediction conditioned on frontier 11 and
`k = 3*10^6`; preserve it as that historical prediction.

Using the stored record and the locally recorded literature anchor
`C(21,425,625,701) = 9.4146088`, the next record in this snapshot has the
upper bound `a(31) <= 21,425,625,701`. The earlier anchor at
17,959,429,571 is below the stored record and no longer supplies such a
bound. This is arithmetic on existing claims, not a new confirmation.

`Campaign.window` processes the returned candidates in increasing k before
advancing `next_k` (launch.py, lines 467-486). A durable save is normally
throttled by the heartbeat interval, rather than made at every roughly
three-second in-memory segment (`save`, lines 417-425). Only the saved
boundary can be used for migration; do not promise that a hard crash
always repeats just one three-second segment.

## 3. Findings

### HLC-001: Tighten the bound with local Euler factors

**P2. Proved mathematical reduction; new in this project's recorded
attempts. Runtime benefit is an Unmeasured hypothesis.**

Source: [hlc_search.py](../hlc_search.py), `E_bounds` (276), `C_bounds`
(291), `prefilter_setup` (531); [hlc_gpu.py](../hlc_gpu.py), `setup` (560),
especially its small-prime root lookups at 601 onward.

The universal bound `E <= pi^2/8` assumes every odd-prime factor takes
its largest possible value. For any finite selected set S, replace those
maxima with their known actual values:

```
E(n) <= E_up(n) = (pi^2/8) * product_{p in S} q_p(n),

q_p(n) = 1                         if (-n|p) = -1,
         1 - 1/p^2                 if p divides n,
         1 - 2/[p(p-1)]            if (-n|p) = +1.
```

**Proof.** The odd-prime product of `(1-p^-2)^-1` is `pi^2/8`.
For a split prime, dividing its actual E factor by this maximum gives
`(1-1/(p-1)^2)(1-1/p^2) = 1-2/[p(p-1)]`. For a ramified prime the ratio
is `1-1/p^2`; for an inert prime it is one. Every omitted ratio is at
most one. No truncation assumption or GRH is used.

For a group-theoretic lower bound `L <= h(-n)`, reject only when a
conservatively computed upper bound on

```
U = 4 sqrt(n) E_up(n) / (3 pi L)
```

is **strictly below** the required retention floor F. This also preserves
an exact equality `C = F` for the census. Rounding must enlarge U, never
shrink it. The n = 3 and nonpositive-floor paths remain explicit.

This direct h argument does not require the current `rho*kappa` factor.
That factor is needed to make an h lower bound imply rejection by the
existing T-based rule. A direct C bound is a stronger, different rule.

| Local information | Multiplier on the universal E bound |
|---|---|
| 3 split, equivalently n = 2 mod 3 | 2/3 |
| 3 ramified | 8/9 |
| 5 split | 9/10 |
| Both 3 and 5 split | 3/5 |

The device already looks up characters through 251 to select prime forms.
A first implementation can use only 3, 5, 7, then price the incremental
value of more factors. A 2/3 order threshold would reduce ideal balanced
BSGS work by about `sqrt(2/3)`, before step-cost and table-cap effects;
this is neither a flag-density estimate nor a 1.5x engine speedup.

**Handoff.** Derive a separate CPU necessary-condition function with
outward bounds, then a device implementation. Keep the literal oracle
unchanged. Decide on a fully specified post-count predicate so the new
raw survivor stream has an independent expectation, rather than being
defined only by which group proof happened to succeed. Price prefilter
time, flags by residue and total window time independently.

**Obligations and rejection criteria.** Every newly excluded k must have
an independently established `C < F`; preserve all census bins, near
events, known canaries and discoveries. Exercise conductor primes,
threshold-near cases, the small range and the ceiling. HLC-006 is required:
today's health checker would call some valid new exclusions an alarm.
Reject any implementation with an unsafe rounding case or a net slowdown.
Fewer flags without a faster full window are not a performance success.

### HLC-002: Descend to the fundamental discriminant

**P2. Proved identities and exact decomposition; new use of information
already computed. Speed and rejection rates remain unmeasured.**

Source: [hlc_search.py](../hlc_search.py), header lines 38-46,
`square_part` (223), `h_from_t3` (247), `prefilter_setup` (531);
[hlc_gpu.py](../hlc_gpu.py), `setup` (560), `prime_form` (631), `pre1` and
`pre2` (666, 722).

Write `n = d*f^2`, with d squarefree, and put

```
chi_d(p) = (-d|p),
Psi(f) = product_{p^e || f} p^(e-1) (p-chi_d(p)),
S(f)   = product_{p^e || f} [1+(p-chi_d(p))(p^e-1)/(p-1)].
```

For d > 3, the exact relations already used on the host are

```
h(-n) = h(-d) Psi(f),
T(n)  = 3 h(-d) S(f).
```

For d = 3, `T(n) = S(f)` directly; `h(-n) = Psi(f)/3` when f > 1,
while `h(-3) = 1`. The order class-number relation, including the unit
index, is also stated in Theorem 2.16 of
[Kezuka, The Class Number Problem](https://www.ma.ic.ac.uk/~buzzard/maths/research/notes/Yukako_Kezuka_MSc_Project.pdf).
The project-specific optimization here is to apply these identities
*before* group computations instead of using only the partial correction
kappa after choosing the nonmaximal group.

**Exact decomposition costs no residual semiprime factorization.** Trial
division through the cube root leaves at most two prime factors counting
multiplicity. If the residual is a square, its root is prime and enters
f. Otherwise it is squarefree and belongs entirely in d, even if the
base-2 probable-prime test mistakes a product of two distinct primes for
a prime. Record the stripped valuations instead of discarding them.

A first implementation can preserve the old raw survivor stream. Prove
`L_d <= h(-d)` in the smaller fundamental class group and reject only
when the old rule rejects the lower count `3 L_d S(f)`, evaluated with
safe arithmetic and the original `rho(n)`. The d = 3 case gives T exactly.
This uses the complete conductor factor, including all exponents and
large conductor primes. A later implementation can combine the descent
with HLC-001 using `L_d*Psi(f)` as its h lower bound.

**Why this is promising, and why it is not a uniform factor-f gain.**
The log's pre-kappa diagnostic at `3*10^11` had square factors in 2,668
of 4,192 flags; 1,956 had `9 | n` (round 1.7). This is a population
enriched for exactly the structure the formula resolves. Those figures
predate the current conductor correction and do not predict its remaining
population. Descending also removes conductor primes from the genus
factor. For f = p (conductor exponent one), with p not dividing d, away from the
one-prime edge cases, the genus-adjusted order target scales roughly by
`2/(p-chi_d(p))`: conductor 3 split gives no target reduction, conductor
3 inert halves it, and conductor 5 split halves it. If p divides d, the
genus rank does not decrease and the analogous factor is `1/p`.

**Handoff and correctness requirements.**

- Recompute the genus lower bound for d from odd valuations and the
  squarefree residual. Reusing the number of prime factors of n would
  overstate the genus factor and could lose a result.
- Build prime forms, keys and arithmetic for discriminant `-d`. Handle
  d = 3 directly and small d by an explicit exact path or fallback.
- For HLC-001, continue to use `(-n|p)` in E, not `(-d|p)`. At a conductor
  prime the first is zero even when the second is +1 or -1.
- Carry virtual lower counts in wide arithmetic. Although actual T has
  the existing uint32 bound, an intermediate `3 L_d S` formed while
  testing a threshold must not silently wrap or saturate incorrectly.
- In the old-rule version, compare the whole `(k,T)` survivor list to
  full tabulation. The flag set and its digests may change legitimately.
  Preserve the independent CPU and GPU implementations and literal oracle.

Validate valuations 1, 2, 3 and larger; primes on both sides of 251;
square and nonsquare residuals; ramified/split/inert conductor primes;
the d = 3 unit exception; and all numeric boundaries. Compare both
routes on the same inputs before choosing a default. Reject on any lost
survivor or if smaller group problems fail to repay their added setup.

### HLC-003: Enumerate modular roots and price a sparse fallback

**P2. Proved enumeration bijection and work bound. A new exact algorithm
here; the production crossover is an Unmeasured hypothesis.**

Source: [hlc_search.py](../hlc_search.py), `class_number_enum` (747),
`verify_find` (972, especially 1005-1015);
[hlc_gpu.py](../hlc_gpu.py), `tabf` (209), `tab_flagged` (1041).
The independent enumerator currently tries every positive odd b <= a for
every a <= sqrt(n/3), including even a that cannot work. This is
Theta(n) modular tests for one discriminant. The log's proposed GPU port
of that loop would retain this operation count.

**Exact replacement.** First obtain the fundamental d independently and
enumerate h(-d). Let `A = floor(sqrt(d/3))`. For each odd a <= A,
enumerate all roots of `b^2 = -d (mod a)` using prime-power roots and CRT.
Map each residue to its unique odd representative in `-a < b <= a`,
then compute `c = (b^2+d)/(4a)`. Retain `a <= c`, with b >= 0 if a = c,
and the primitive condition `gcd(a,b,c) = 1`. Count each retained form
once. The endpoint b = -a is excluded and b = a included. The unique
representative is in **(-a,a]**, not necessarily in (0,a].

**Proof of completeness and uniqueness.** Every reduced form of this
discriminant satisfies these conditions and supplies a root. Conversely,
every retained root supplies one canonical reduced primitive form.
Odd b gives `b^2+d = 4 (mod 8)`, so a and c must be odd; division by 4a
is integral once the root condition holds. The reduced inequality gives
`3a^2 <= d`. Thus no other a or b is needed. Recover the original h or T
with the exact conductor relations in HLC-002.

For squarefree d and an odd prime power dividing a: a nonramified split
prime power has two roots, an inert one none, a ramified prime to the
first power one root, and a ramified prime to exponent at least two no
root. Consequently the number of roots modulo a is at most
`2^omega(a) <= tau(a)`. Summed through A this is `O(A log A)` root outputs,
plus factor-table, modular-root and CRT costs, in place of the quadratic
all-b search. This bound uses descent to squarefree d; do not assert the
same bound for arbitrary n with singular prime-power roots.

At `k = 10^12`, the worst fundamental d is about `4*10^12`:

| Work or storage | Arithmetic estimate |
|---|---|
| A | about 1,154,700 |
| Odd a to visit | about 577,350 |
| Present all-a, odd-b tests | about `A^2/4 = 3.33*10^11` |
| Tests after only skipping even a | about `1.67*10^11` |
| uint32 smallest-prime-factor table through A | about 4.6 MB, reusable |

These quantities are not speedup factors: a root/CRT operation costs far
more than one remainder or one GPU bit test.

**First bounded implementation: confirmation.** Build an optimized CPU
enumerator in `hlc_search.py`, preserve the literal oracle, and compare
complete form sets on reachable cases before comparing just totals.
Independently factor the verifier's input and independently implement its
conductor reconstruction; do not trust device state or reuse the producer's
conversion helper. Compare the reconstructed h(-n) against literal
direct-n primitive enumeration on reachable conductor cases. This
addresses the existing roughly 14-minute extrapolation
for enumeration at `k = 10^12`, and may make the independent exact leg
feasible above the current `ENUM_MAX_N` skip. The original-definition
oracle remains unchanged. Cover zero roots, a = 1, b = a, a = c,
ramification, repeated conductor powers, d = 3 and the ceiling.

**Second experiment: sparse production resolution.** Apply the exact
enumerator only to flags, after HLC-001/HLC-002 have been priced. With
the historical 0.285% flag fraction, there are about 12,000 flags in a
window at `10^12`. A worst-case full odd-a scan for each is about
`7*10^9` leading-coefficient visits, before root computation. That could
still be slower than the measured 1.94-second tabulation. Measure the
complete sparse pass, its shared tables and dispatch cost; keep dense
tabulation as fallback if it wins. Do not ship based on operation counts.

**A more focused hybrid avoids the old zero-flags requirement.** Round
1.8 proposes omitting `n = 2 (mod 3)` only if another prover empties that
class. Instead, resolve its remaining flags exactly by the sparse route,
return its survivors separately, and tabulate the other classes. This is
safe even if the separate class contains genuine survivors.

For `n = 2 (mod 3)`, exactly one of x, y, z is divisible by 3. The limiting
modular fraction of all triples with this pattern is
`3*(1/3)*(2/3)^2 = 4/9`; a finite window's exact work share need not be
exactly 4/9. Jump over the excluded representations arithmetically, rather
than adding another reject branch to the unchanged walk. Merge disjoint
results in k order and preserve all exact T values. The historical 816
flags in this class out of 17,016 was before kappa at `3*10^11`; it is
motivation, not a current estimate.

Using the log's approximate 51% representation-loop share at `10^12`,
removing 4/9 of that component would save about **22.7% of a window before
extra costs**, not 4/9 of all tabulation time. The pair scan remains.
Reject the hybrid unless sparse resolution, jump arithmetic and merging
together repay the removed work. An unresolved class always falls back;
an empirical absence of records is never a proof to skip it.

### HLC-004: Finish the squared-base order experiment

**P2. Known unfinished idea, explicitly credited to
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 1.8.**

The current first pass finds the order of f and then uses the order of
`f^2`. Since `h = 2^(t-1) |G^2|`, a sufficiently large order of `f^2`
can prove rejection directly. For t >= 2, moving the order search to
the square approximately halves its target compared with the current
first-pass order bound. Balanced BSGS tables and walks then shrink by
about sqrt(2) in *step count*. Source: `prefilter_flag` at
[hlc_search.py](../hlc_search.py), line 619, and device `pre1`/`pre2`.

The log estimates about 0.15 s saved per 2.5-second window at `10^12`,
roughly 6%, or about three hours in its fixed-distance clock to `10^12`.
Those are the log's estimates, not an executed experiment. Two ordinary
prime steps to implement one squared-prime step can erase the gain;
specialized p-squared composition must cover nonunit cases correctly.
The one-prime genus case also needs its own handling.

Implement independently of the other reductions, compare the final
decision rather than merely an intermediate order, and measure general
composition, cheap-step and full-window costs. Reprice it after conductor
descent, which changes both t and the distribution of order targets.
Reject if cheaper order searches do not produce a complete-work gain.

### HLC-005: Price selective use of published class-number data

**P3. Reconsideration of a documented idea using newly located access
information. Deferred pending an I/O and trust-path price.**

Round 0.7 left published tabulations unpursued partly because their data
would have to be obtained. The
[LMFDB class-group dataset](https://www.lmfdb.org/NumberField/QuadraticImaginaryClassGroups)
provides fundamental discriminants and class numbers, including
`|D| = 3 (mod 8)`, in 4096 files per residue family, each covering a
`2^28` discriminant interval. It documents compressed files of 50-200 MB
and a delta-coded format with the class number explicitly present. No
data file was downloaded in this review.

**Project-specific consequence.** The covered bound `d < 2^40` supplies
every needed fundamental class number for original `n < 2^40`, hence
all odd `k < 2^38` (about `2.749*10^11`). HLC-002 also makes it useful
above that height: whenever `n/f^2 < 2^40`, the table plus S(f) gives T
exactly. In particular, every nonfundamental n in this family has f >= 3,
so all such n below `9*2^40` have covered fundamental discriminants.

This is an exact mathematical reconstruction, conditional on reading
the correct, trusted data. It is not automatically an economical engine:
the full relevant 4096-file family is roughly **205-819 GB compressed**
at the documented per-file sizes, before indexing. The historical v2
clock to about `2.7*10^11` is already only about eight hours. Selective
file access may be useful for independent validation or conductor-rich
fallbacks, but downloads, parsing and indexing could cost more than the
GPU work saved.

Any implementation must verify file identity, decoding, discriminant
ordering and independent sample counts; missing data must fall back,
never imply an empty interval. A lookup-based coverage claim must name
its external-data dependency and cannot be relabelled as independently
recomputed coverage. First price a narrow representative file range and
its expected reuse, without changing the current campaign. Reject bulk
adoption unless storage, I/O, provenance and time all justify it.

### HLC-006: Change the validation contract deliberately

**P1 prerequisite to changing rejection mathematics. Observed in source;
this is an implementation safeguard, not a claim that the current hunt
has missed a result.**

Three distinct contracts must not be conflated:

1. The **mathematical output**: records, near events, census from 7.5,
   designated canaries and complete ordered coverage.
2. The **raw `(k,T)` survivor stream** of the current universal rule.
3. The **internal flags and count digests** used in the frozen benchmark.

HLC-002 can preserve (1) and (2) while deliberately changing (3).
HLC-001 can preserve (1) while changing both (2) and (3). The present
code assumes more than (1):

- `Campaign._health_poll`, [launch.py](../launch.py), lines 383-409,
  demands that every prefilter rejection fail the *old* `survivor_mask`.
  A stronger valid C proof may fail this check. The health sample must
  carry or derive the appropriate rule and verify the new exclusion by
  independent host mathematics; do not merely disable the alarm.
- P1, P5 and P6 in [hlc_gpu.py](../hlc_gpu.py) compare counts, flags and
  old-rule streams. Keep original full tabulation available for bounded
  validation and define the new CPU expected predicate independently.
  For a changed raw stream, explicitly verify all removed entries are
  below F and all eligible entries and counts agree.
- `digest` and `fingerprint` (1246-1269) include the number of flags and
  their count digests. A stronger prefilter can change the fingerprint
  without changing any record or census value. Refreezing constants is
  the last step after independent validation, not evidence of it.
- `CONFIG_KEY` and v1 adoption, [launch.py](../launch.py), lines 80-95,
  describe the old rule. A new rule needs a versioned coverage statement
  and an explicit migration argument from the saved contiguous floor.

The migration argument is straightforward only after proving that both
engines cover every eligible k with the same census floor: carry the
saved `next_k`, terms and census, and replay any unfinished work from
that boundary under the new engine. A residue-specific hybrid must
finish every class before advancing the boundary, and merge candidates
before changing the record. Never reinterpret a partially processed
class as contiguous coverage. Evidence is already keyed by k through
[huntlib/evidence.py](../../huntlib/evidence.py), `record`, so replay can
remain idempotent.

When raw-survivor semantics change, version or segregate the cumulative
`survivors` counter and flag metrics. Preserve terms, census and coverage,
but do not present old-rule and new-rule raw counts as one comparable
metric. Include an old checkpoint with pending/replayed evidence in the
scratch migration drill, and verify the metric transition as well as
the mathematical outputs.

Do not raise F to the live record as a transparent optimization. The
launcher deliberately fixes it at `min(7.5, padded_record_lower_bound)`;
raising it loses documented census values and canaries. Preserve small
range rediscovery, nonfundamental values, strict record comparisons and
structural ties. Record the frozen workload and unchanged output portion
separately from intentionally changed internal checksums.

## 4. Implementation handoff and future validation

Recommended sequence, with each step independently revertible:

1. Build the HLC-001 host bound and HLC-002 conductor decomposition as
   independently checked mathematical components. Decide whether the
   first device experiment keeps the old T rule or introduces the new
   C rule; establish HLC-006's contract before timing either.
2. Implement and compare the reductions separately, then together. Use
   full tabulation and the original-definition oracle wherever reachable,
   and independent exact counts at higher targeted discriminants. Include
   adversarial conductor, genus, rounding and threshold cases, not only
   random samples. Keep a retained fallback for undecided inputs.
3. Build HLC-003's CPU confirmation enumerator. Compare complete reduced
   form sets at small sizes, primitive counts and conductor reconstruction
   at larger sizes, then the existing discovery accept/reject drills.
4. Measure a sparse exact fallback and the mod-3 hybrid on the actual
   post-reduction flag populations at `10^12` and `3*10^12`. Include root
   setup, shared tables, dispatch, merging and fallbacks. An empty or
   unusually easy synthetic flag set is not a representative workload.
5. Evaluate HLC-004 separately and revisit the remaining profile. Keep
   all declined results in OPTIMIZATION_LOG; only validated timings
   enter BENCHMARKS. Re-sweep structural tuning constants after a winner.
6. Before adoption, run the appropriate complete selftest and score
   battery, ceiling and planted-fault tests, split/unsplit comparisons and
   checkpoint migration drills in scratch state. Compare census and
   record outputs, not only a checksum. No review instruction authorizes
   starting or resuming an owner's hunt.

Timing must be paired and interleaved, include A/A noise checks, use the
same complete workload and stay within repository command-duration
limits. Keep CPU and GPU implementations independent; never optimize the
literal oracle to share the new root or conductor engine helpers. The
regular Python installation remains the project environment.

## 5. Work-count and conditional-time estimates

The following calculations use the stored `10^12` window split, holding
the prefilter at 0.590 s and tabulation at 1.940 s. They are **conditional
arithmetic**, not forecasts of any proposal's performance:

| Hypothetical change | Window time | Overall speedup |
|---|---|---|
| Existing measured split | 2.530 s | 1.00x |
| Tabulation becomes twice as fast | 1.560 s | 1.62x |
| Tabulation becomes four times as fast | 1.075 s | 2.35x |
| Tabulation costs zero, unattainable limiting calculation | 0.590 s | 4.29x |

This is why sparse exact work deserves investigation. It is also why a
large reduction in flags is insufficient if the same triples are still
walked. At higher heights the pair scan grows more costly; at lower
heights setup and confirmation can dominate differently.

The log's roughly 51% representation-loop / 25% pair-scan split and its
14% / 9% prefilter subdivision are approximate at `10^12`; the latter
subdivision was extrapolated from `3*10^11`. Only the total 0.589-second
prefilter and 1.940-second tabulation were directly measured there.

Discovery latency is a separate budget. `Campaign._record` waits for
`verify_find`, and `score.py` times fingerprints without classification or
discovery confirmation. The historical analytic leg was 25 s at `10^8`,
76 s at `10^9`, extrapolated to about 40 minutes at `10^12`; enumeration
adds about 14 minutes there. The log declined faster special functions
when the sweep took 16 days and expected about a dozen finds. V2's
2.3-day fixed-distance clock and the 19 stored discoveries make that
tradeoff worth revisiting, after the exact enumerator. The proposed
3-4x analytic-leg gain remains unmeasured and needs rigorous error work.

No new conditional record-walk forecast was generated. The eight-hour,
2.3-day and 107-day clocks in the history are fixed-distance estimates
from the prior rate law; they exclude unknown future confirmation costs
and are not promises of when the next open term will occur. Do not
multiply overlapping reductions or carry a single-height speedup across
the entire campaign without measuring its height dependence.

## 6. Alternatives examined, prior rejections and open questions

| Route | Assessment |
|---|---|
| Fixed wheel from historical residues | Unsupported unconditionally. Pointwise E/group bounds are sound; clustering of records does not exclude a residue class. No GRH assumption is introduced by this report. |
| Discard all nonfundamental n, or all repeated-character values | Unsafe for the existing task. Conductors can increase C, and exact ties still contribute to the census. Use exact reconstruction instead. |
| More generators or a larger subgroup-index cap | Sound lower-bound refinements, but a smaller flag set alone barely affects the dense walk. Revisit after measuring the residual population or to enable a sparse hybrid. |
| Rigorous analytic interval fallback | Worth a later proof/engineering experiment. The log's analytic fallback need not use unchecked rounding: a tail-and-rounding enclosure containing one integer determines exact h; ambiguous cases fall back. `class_number_analytic` currently does not certify all floating error, and its small distance from an integer is not such a certificate. |
| Segmented trial-factor sieve / cached setup | Correct in principle, but lower priority. The recorded setup-only cost is 0.0109 s per `2^22` inputs at `3*10^11`. Multiplying by the 1.367-window total setup calls gives about 0.0149 s, only 1.15% of that window before replacement overhead. The same percentage is not measured at `10^12`. |
| Full-window traversal with synchronized phases | Already built and rejected at 0.31x in round 1.5. New rejection mathematics does not itself cure the synchronization loss. |
| Folded bitmap over the full window | Already priced as slower around `10^12`, potentially useful above about `3*10^12`. Retain as an adaptive high-height alternative, not a newly discovered universal improvement. |
| Sorting membership jobs | Previously measured at 0.845x / 0.805x and rejected. Do not repeat without a changed scheduling mechanism. |
| More host workers / model-loop caching | Classification is about 1% at `10^12`; the model is already cached through `LiveLadder`. These do not address the principal cost. |
| Borrow a sibling prime-hunt wheel | The premise does not transfer. Prime hunts can exclude values with a composite required form; this hunt ranks constants and permits every odd k. Shared checkpoint, oracle and completed-coverage disciplines do transfer. |

One historical rejection needs a narrower statement. Round 0.1 says
FFT cubing requires the whole prefix in memory. Published out-of-core
NTT/CRT methods do handle class-number series exceeding RAM;
[Mosunov and Jacobson, sections 3-4](https://arxiv.org/pdf/1502.07953)
describe such a method for the applicable discriminant classes. Their
reported `D = 5 (mod 8)` computation to `2^40` used substantial disk
space and 64 processors. This establishes feasibility, not a performance
transfer to this windowed GPU hunt. A replacement would need its own
storage, restart, coefficient-bound and crossover design. It remains a
larger alternative, behind the local reductions and sparse experiment.

Unresolved questions for measurement are the post-reduction flag
distribution, the cost of modular roots on the actual hardware, whether
the mod-3 hybrid amortizes its setup, the effect of conductor descent on
BSGS divergence, and whether a certified analytic fallback can be made
cheaper than exact enumeration. None is settled by this static review.

## 7. Sources, snapshot hashes and execution record

The review read the original-definition oracle, CPU mathematics and
verification, GPU source and gates, launcher and drills, scoring, model,
stored model output, project documents, current checkpoint, representative
discovery evidence, and relevant `huntlib` checkpoint/evidence/rungs
behavior. It followed CONVENTIONS, CODEX_REVIEWS, CLAUDE, OPTIMIZATION and
INNOVATION, and used another project's review report and ledger as a
format example.

Source SHA-256 values, recorded before review edits:

| File | SHA-256 |
|---|---|
| hlc_reference.py | `1aaf2e101ea188f71e2a04ce9c55fb78c6595e16b4895db5ee65ba7e804c660e` |
| hlc_search.py | `ee7d01fbb300804a4887e38f51bdac2cce676c697bd6a71268be593c13747961` |
| hlc_gpu.py | `dbb11df5dc209f3c00c7219d8994662f5708e91d6814096bf19104703e1498b0` |
| hlc_model.py | `14c85aa47387eaca7bdf50d7990d162fc71d52808cf6373f30813ff96b6cdd84` |
| launch.py | `d0be99f9ae0f65c1cc93e87cc42c8ddd3a531479bfcfc6ee7e5089800495d409` |
| score.py | `a0003f58208967ece1e3cb6473a59aaa850752957a3a402b38589c83baa16ffa` |
| model_results.json | `86d915f7b94feebc37b359e8be3d16eed9e2427ad598edbbdb5c0496d872c2f9` |
| BENCHMARKS.md | `7c4b47bb5ef620aa59639060ca4b768ee46702b25fcf507e742fd9fe2a24c194` |
| OPTIMIZATION_LOG.md | `514fa2fdc2436abd248417279f822876ce560305ca209d68c8669355f1b722e0` |

External sources checked on the review date are linked beside the claims
they support: OEIS for the definition and public table; Kezuka for the
order class-number formula; LMFDB for published data access and format;
and Mosunov/Jacobson for out-of-core tabulation. The local mathematical
reductions and implementation proposals are this review's derivations.
An author-page link to newer class-number slides returned 404 and is not
used as evidence of an algorithm or speedup.

**Executed:** read-only file/Git inspection, source hashing, documentation
and primary-source browsing, lightweight arithmetic and Markdown edits.
**Not executed:** any project import, oracle, engine, model, launcher,
primality experiment, test battery, benchmark, profiler, GPU query or
CUDA compilation. No campaign was started, stopped or reconfigured; no
checkpoint, evidence, Python source or machine setting was written.
Documentation-only reviews do not run correctness gates.
