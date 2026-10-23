# Primorial ladders: static mathematical review

**Author:** Codex (OpenAI). **Date:** 2026-10-20.
**Scope:** A115785, A115786 and A145743; all five public Python roles,
model, evidence, checkpoints and optimization history. The review team
examined this project only, consulting polynomial-runs as a specific
mathematical reference for PML-001.

This follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex is always
static in this role: no GPU use, project imports or execution, oracles,
models, tests, benchmarks, searches or primality experiments. Only
documentation was edited. Numbers calculated here use stored data and
explicit scalar formulas; historical certificates and rates were read,
not independently rerun.

**Conclusion.** No missed optimization establishes a one-day next term
for these campaigns. The engine already contains the modern periodic
window sieve and folded rounds. A new, modest work-sharing opportunity
exists between A145743's composite starts and the prime-start square
family A092120, but it helps their combined search, has a large initial
coverage gap, and is unmeasured. It is deferred here.

The square family's model omits its composite-start restriction. Correcting
that restriction lowers the BH intensity by roughly 7.5–8.2% near its
saved cursor; it makes the forecast less favorable. Source-level proof and
promotion safeguards also need attention before extending the hunt.
At the recorded/reference rates, the current conditional median distances
remain approximately **45, 6.6 and 5.0 days** for A115785, A115786 and
A145743 respectively.

## Definitions, evidence and the real frontier

HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`, with documentation
edits in the worktree. Source/data hashes are recorded below. Line
references name symbols as well as snapshot locations.

Let \(P_k=\prod_{i=1}^k p_i\). The definitions are:

| Family | Required prime values at index n | Domain | Current open index |
|---|---|---|---:|
| A115785 | \(p,p-P_1,\ldots,p-P_n\) | p prime; \(p\geq P_n+2\) | 20 |
| A115786 | \(p,p+P_1,\ldots,p+P_n\) | p prime | 21 |
| A145743 | \(m+4k^2,\ k=1,\ldots,n\) | m composite, \(m\geq4\) | 21 |

All three are **at-least** families: index n requires its first n
conditions and does not require a composite next value. The primorial
families have n+1 prime forms, including p; the square family has n forms,
excluding m. See [reference constants/domain/floors](../primorial_reference.py#L244)
and [is_term](../primorial_reference.py#L329).

All three condition sets are mathematically nested. A115785 is handled
operationally as a new line because its next primorial floor is far above
the current term and completed interval. This is not a non-nesting
theorem: a sufficiently large p could satisfy several indices. The
recorded negative-shift terms stop at their own index, and the latest
a(19) lies below \(P_{20}\), so no present next-line coverage transfers.
`x_floor` at [launch.py:136](../launch.py#L136) enforces the appropriate
floor; `record_discovery` can settle a range of indices.

The evidence records fifteen terms in fourteen discovery files:

| Family | Recorded new indices and values |
|---|---|
| A115785 | 16: 32702642630899786669; 17: 1923178323603035931703; 18: 117558515835200358637393; **19: 7858467306309706402625473** |
| A115786 | 17: 123718092985601; 18: 238468632242449727; 19: 177832544931278338301; **20: 276111714233825559827** |
| A145743 | 14: 955236815527; 15: 118059306695257; **16=17: 48192095115862063**; 18: 754953104966780647; 19: 306052304501173404673; **20: 86871442473592036108753** |

The ledgers are [A115785](../evidence/a115785_discoveries.json),
[A115786](../evidence/a115786_discoveries.json) and
[A145743](../evidence/a145743_discoveries.json).
[RESULTS.md:16–31](../RESULTS.md#L16) reports a separate historical
verification of all 255 certificates: 233 deterministic MR and 22 BLS75
Theorem 1, with none unproved. The files currently record
`certificates_verified=true` and empty `unproved` lists. The square
evidence also records composite factor witnesses.
This review did not rerun any certificate or primality check.

The source's [FOUND table](../primorial_reference.py#L181) remains empty.
The campaigns recover the discoveries from checkpoints, whereas fresh
reference/model operations still see the original literature frontiers.
`Campaign._known_top` at [launch.py:460](../launch.py#L460) also reads
`KNOWN`, so populating `FOUND` alone does not automatically change every
fresh campaign reader. Normalizing those readers and adding current
frozen workloads were already listed as owed work in
[RESULTS.md:296](../RESULTS.md#L296). Do not call them new speedups.
OEIS submission statements there refer to the October 5 export; the user
has since submitted most results, and no current website status was checked.

### Saved classified boundaries versus partial work

The snapshots are dated October 3 for the primorial entries and October 5
for the square entry. They match the documented paused state; no process
inspection or live hunt query was performed.

| Family / checkpoint | Filter; q2 | W; periods/segment | j; u / launches | Committed numerical boundary B |
|---|---|---|---|---|
| [A115785](../campaign_checkpoint_a115785.json) | 20; 32768 | 614889782588491410; 160 | 907383479; 317291 / 327360 | 557940830126698960967415392 = \(P_{20}+2\) |
| [A115786](../campaign_checkpoint_a115786.json) | 21; 16384 | 614889782588491410; 160 | 609; 16611 / 327360 | 374467877596391268690 |
| [A145743](../campaign_checkpoint_a145743.json) | 21; 16384 | 32589158477190044730; 160 | 2732; 2882 / 329472 | 89033580959683202202360 |

The two primorial plans use unit 6 and wheel levels
`[5,7,11,13,17,19,23]`, `[29,31,37]`, `[41,43,47]`.
The square plan uses `[5,7,11,13,17,19,23,37]`, `[29,31,41]`,
`[43,47,53]`, also unit 6. The first two records are narrow; the last
is wide. The forced classes are p≡1, p≡5 and m≡1 modulo 6 respectively.

All three `zone_n` fields match the current filter. A115785's finite
exception zone has been classified, but no new full device segment is
closed; the report conservatively uses its saved floor as B. On the
other two families, `cover_x=B` records the classified suffix of the
previous filter, carried after promotion. These are half-open sweep
boundaries, not a statement that a fractional launch is a numeric prefix.
Here the two B values are divisible by 6, hence outside their forced
class, which supports the documentation's strict `a(next)>B` phrasing.

Saved pending records number 2299, 1381 and 288, with maximum runs
13, 15 and 13 respectively. None is already a full current-filter hit.
The work cursor says which CRT launch stripes have been classified;
it does not prove a proportionally long numerical interval empty.
No speculative fractional coverage is added to B.

`follow_frontier` [launch.py:892](../launch.py#L892) already carries the
monotone families' classified suffix and resets A115785's line.
The finite `RUN_AHEAD=6` qualification to that carry is material; PML-003
describes the missing cap-hit safeguard rather than declaring the current
stored boundaries invalid.

## Rates, models and a one-day budget

[BENCHMARKS.md](../BENCHMARKS.md#L63) has measured **current-filter**
device/API rates 1.11×10^16 p/s for A115785 n=20 and A115786 n=21.
Their earlier completed campaign filters matched their prices at roughly
0.98–1.01×. The stopped-filter estimates 1.36×10^16 and 1.4×10^16
were inferred from launch fractions, explicitly not accepted line rates.

A145743's last measured campaign rate is 6.3×10^17 m/s at **n=20**,
using 39.2 active campaign hours; its wall-clock leg included approximately
six hours not running. There is **no n=21 rate**. Use that older rate only
as a stated scenario. `score.py` [SHAPES, line 87](../score.py#L87)
pins original openings n=16/17/14 and anchors, not all three actual fronts.
The six old fingerprints remain useful and must not be silently replaced.

The [saved model JSON](../model_results.json) predates the finds. Its
monotone-family later rows start at the old frontier and are not current
conditional forecasts. [RESULTS.md:258–277](../RESULTS.md#L258) records a
separate October 5 model evaluation from the real cursors; its rounded
numbers are the ones used below. No model was executed here.

| Current target | Recorded conditional median location | Remaining median distance / reference rate | One-day rate multiplier for that distance |
|---|---:|---:|---:|
| A115785 a(20) | \(P_{20}+4.32\times10^{22}\) | 45.0 days at 1.11×10^16 | 45.0× |
| A115786 a(21) | \(6.74\times10^{21}\) | 6.64 days at 1.11×10^16 | 6.64× |
| A145743 a(21) | \(3.59\times10^{23}\) | 4.96 days at prior n=20 rate 6.3×10^17 | 4.96× |

For the square family the recorded conditional Q1 is \(1.84\times10^{23}\):
its distance from B costs about 1.745 days under that same unmeasured
n=21 rate assumption. A 1.745× rate would only reach a historical-model
**25%** point in a day, not make a next term likely or guaranteed.
PML-002 lowers the relevant intensity.

The documented model day probabilities are 2%, 15% and 16%, before that
correction and before accounting for segment completion. The fourteen
independent new-term draws had mean E=1.62, with broad scatter
([RESULTS.md:152](../RESULTS.md#L152)). That is evidence of optimism,
not a deterministic multiplier to impose on every future waiting time.
The original benchmark's 66.1-day and 14.2-day figures are **expected
confirmed-find clocks** computed by `expected_sweep`, not the same
quantity as these median-distance clocks.

The current segment spans and reference clocks are:

| Families | Segment line S | Full segment time | Complete closures in 24 h, allowing unknown current partial-work credit |
|---|---:|---:|---:|
| A115785 / A115786 | 98382365214158625600 | 2.462 h | 9 or 10 |
| A145743 | 5214265356350407156800 | 2.299 h at the prior n=20 rate | 10 or 11 |

These bounds use only that the remaining first-segment time lies between
zero and one full segment, followed by equal full segments at the assumed
rate. They exclude startup, proof pauses, promotion and changing host cost.
They do not assign equal time to every launch. The corresponding complete
endpoints, if no find changes the filter, are:

| Family | Lower / upper 24-hour complete endpoint under this scenario |
|---|---|
| A115785 | 557941715567985888395045790 / 557941813950351102553671390 |
| A115786 | 1259909164523818899090 / 1358291529737977524690 |
| A145743 | 141176234523187273770360 / 146390499879537680927160 |

The almost-finished negative-shift segment is useful saved work, but
completing it does not close the roughly 45-day median distance. No
currently supported mathematical proposal supplies the multipliers above.

## PML-001: share the square-shift sieve with the prime-start sibling

**Disposition: Deferred.** New exact work-sharing formulation; no
implementation or runtime measurement. The current coverage gap and
separate proof requirements make it a longer-term combined-search idea.

The specific sibling [A092120 definition](../../polynomial-runs/poly_reference.py#L1)
asks for prime p with \(p+4k^2\) prime for k=0..n and
\(p+4(n+1)^2\) composite. Its current open index is 20, whereas A145743
currently seeks a composite m with shifts k=1..21 all prime.
Both therefore require the twenty positive shifts
\[
 x+4k^2,\qquad 1\leq k\leq20.
\]
A common sieve for those shifts can feed two separate branches:

- A proved prime x, with the first twenty shifts prime and shift 21
  composite, is a candidate for exact A092120(20). Longer prime runs can
  be classified against that project's other open exact indices.
- A proved composite x, with all twenty-one shifts prime, is a candidate
  for A145743(21), with its usual at-least riders.

Do not use the current composite-family **21-shift** sieve for both:
it would reject prime-start exact-20 hits whose 21st shift has a small
factor. Do not use the prime-family sieve for both either: its x-prime
filter removes legitimate composite starts. Domain and stopper tests
belong after the shared positive-shift sieve.

At a common wheel containing all primes through 53, let \(d_C\) be the
density for the common twenty positive shifts, \(d_M\) for composite
family's 21-shift sieve, and \(d_P\) for the prime-start 20 filter.
The finite CRT products give
\[
 \frac{d_C}{d_M}=\frac{23}{22}\frac{27}{26}\frac{33}{32}
 \simeq1.119591346,\qquad
 \frac{d_C}{d_P}\simeq1.547071678.
\]
For the first ratio only primes 43,47,53 gain a new distinct square root;
for the second, adding x as a prime form adds the zero root at wheel
primes above 20. Thus
\[
 \frac{d_M+d_P}{d_C}\simeq1.54
\]
is an ideal **aggregate generated-candidate** saving over two separate
wheel enumerations on the same interval. It is not a single-family
speedup, an exact final-survivor ratio or a measured runtime result.
The common sieve is looser than either separate sieve and needs more
classification and family-specific tail work.

There is an immediate coverage mismatch. The referenced
[A092120 checkpoint](../../polynomial-runs/campaign_checkpoint_a092120.json)
has B=266247275860816780530, whereas A145743 has
B=89033580959683202202360. Sweeping the difference at the sibling's
recorded n=20 rate 1.24×10^18 costs approximately **19.9 hours** before
any common range, excluding confirmation latency and startup.
Historical A145743 classification discarded prime starts rather than
retaining a separately proved prime-family search; it cannot backfill
that gap by reinterpretation.

A future joint enumerator needs a branch activation boundary and
independent durable coverage/evidence/census for each family. Never jump
both to the larger B. Keep both definition oracles separate. Validate
projected complete streams against each original search on identical
absolute intervals, deliberately including prime exact-20 cases killed
by the 21st-shift sieve. A changed common sieve changes raw census
selection, so preserve original census provenance rather than silently
merging counts.

The prime branch inherits the exact-run proof barrier analyzed in the
[polynomial review](../../polynomial-runs/codex-reviews/2026-10-20-static-review.md#pol-001):
PRP overstatement can alter an exact index. The composite branch inherits
PML-003's domain proof requirement. This proposal does not authorize a
sibling campaign or imply that a stored new term has been found.

## PML-002: model the composite-start domain

**Disposition: Proposed.** The local-factor calculation is exact;
converting it to a density is conditional on Bateman–Horn.
This corrects forecasts, not search speed.

`_density_curve` [primorial_model.py:94](../primorial_model.py#L94) uses
only the n prime shifts \(m+4k^2\). It does not remove starts m that are
prime, although the oracle and classifier reject them.
The corrected composite-start intensity is the difference between the
all-shift intensity and the intensity with **m also prime**:
\[
 a(m)=\frac{S_n}{\prod_{k=1}^n\log(m+4k^2)},\quad
 b(m)=\frac{S_n^+}{\log m\prod_{k=1}^n\log(m+4k^2)},\quad
 a_{\rm composite}(m)=a(m)-b(m).
\]
It is not \(a(m)(1-1/\log m)\), since the shift conditions are correlated
with the primality of m.

For n=21 and an odd prime q, the ordinary root count is
\[
 w_q=\begin{cases}
 (q+1)/2&q\leq21,\\
 (q-1)/2&21<q\leq43,\\
 21&q>43.
 \end{cases}
\]
At q=2 the count is one. The zero residue is already killed when q≤n,
because k=q occurs; at odd q>n it is absent and adding the form m kills
one additional residue. Consequently \(R=S_n^+/S_n\) has local factors
\[
 R_q=\begin{cases}
 q/(q-1)&q\leq21,\\
 q/(q+1)&21<q\leq43,\\
 1-\dfrac{21}{(q-1)(q-21)}&q>43.
 \end{cases}
\]
For general n, q=2 is also an already-present zero root, including n=1;
do not apply the odd-prime rule blindly at that endpoint.

An explicit product over primes through 257 gives
\(R_{257}=4.35144708865\).
For omitted q>Q=257,
\[
 -\log R_q\leq \frac{21}{q(q-22)},\qquad
 \sum_{q>Q}-\log R_q\leq\frac{21}{Q-22},
\]
where the second bound replaces primes by all integers and uses an
integral majorant. Therefore
\[
 3.9794624673\leq R_\infty\leq4.3514470887.
\]
At the saved square-family cursor \(\log m\simeq52.8433\), the ratio
\(b/a=R/\log m\) is approximately **7.53–8.23%**. The corrected BH
intensity is approximately **91.8–92.5%** of the current model there.
This is not a measured rejection rate or a newly evaluated quantile.
It cannot by itself explain the historical mean E=1.62.

Future model work should keep the original predictions as historical
artifacts and produce a separately labeled corrected version, conditioned
on actual saved coverage. Construct the augmented singular series
independently, test the q=2/zero-root cases, and compare the difference
against nonnegative count semantics. A low-height heuristic subtraction
that becomes negative must be flagged as model failure, not treated as
a theorem that no terms exist. At the present height there is no such
near-cancellation.

## PML-003: proof-safe settlement, domain tests and carried coverage

**Disposition: Proposed.** These are source-level correctness obligations,
not speedups. The recorded required-value certificates are complete;
no historical missing term is demonstrated.

### Unresolved certificates must hold settlement and coverage

`record_discovery` obtains `(certs, unproved)` at
[launch.py:821](../launch.py#L821), but writes `found`, evidence and a
discovery banner even when `unproved` is nonempty. Lines 884–889 explicitly
say the find stands on the three probable-prime/verification legs.
A measured success rate of 46/46 bounded certificates in the old ceiling
experiment does not prove every future attempt succeeds.

Require proof of every value needed for a settled index before accepting
that index. Persist an unresolved candidate and keep the relevant
leastness boundary behind it if bounded proof work fails. It is valid to
settle only an initial fully proved run, retaining higher unresolved
conditions, but never present unproved riders as proved. Test failure
injection before `found` mutation, evidence acceptance, promotion and
checkpoint advancement. Current A115785 n20 and A115786 n21 already
need certificates for some values even though their smallest values or
starting primes can be below the MR bound.

### Composite-domain rejection is not one-sided above the MR bound

For A145743, [in_domain_fast](../primorial_search.py#L241) uses
`not mr_is_prime(m)`, and [sprp_run](../launch.py#L352) discards an
MR-passing m at lines 384–385. Below the deterministic bound
\(M=3317044064679887385961981\), that is an exact domain decision.
Above it, an MR-passing composite could be rejected as prime before
independent verification. This has the opposite error direction from a
PRP test on a required prime value.

Use a three-way domain result: proved prime, proved composite, unresolved.
Reject m for being prime only with proof; accept composite membership with
a checked nontrivial divisor or a reproducible failed strong-test witness.
Keep an unresolved relevant candidate eligible for further classification
or behind a durable coverage barrier. Merely requiring certificates after
DISCOVERY does not repair candidates discarded before that path.
The current square boundary and conditional median are below M, so this
is a configured-domain future obligation, not a current demonstrated miss.

### A finite run cap does not prove every promoted suffix

Classification uses cap \(C=n+6\)
([run_cap](../launch.py#L582)), while the first discovery is reread up to
64 ([record_discovery](../launch.py#L801)). Suppose that discovery advances
the frontier to f>C. Another pending candidate may have true run >f
but saved run C because it hit the old cap. `handle` then sees C<f and
routes it to CENSUS; the pending list is cleared and the whole old segment
is carried at [lines 1158–1169](../launch.py#L1158).
This is not a proof that the later candidate fails the new filter.

Before carrying, extend every unresolved cap-hit whose tested depth is
no longer sufficient for the new frontier. Store the tested cap with
pending records, distinguish a real composite stopper from a cap return,
and resolve every possible new-index hit or replay the relevant remainder.
At f=C, NEAR verification may fail closed on a longer run; the silent
CENSUS counterexample specifically uses f>C. An oracle cap of 64 is
finite too: a cap hit is a lower bound, not a proved exact stopper.
The historical recorded runs do not exhibit this failure.

### Adoption must reconcile partial records, not just reset u

`Campaign.__init__` [lines 522–532](../launch.py#L522) resets u when
segment size or launch count changes. `load` has already restored
`pending` and partial `survivors`
([lines 691–713](../launch.py#L691)). Replaying from u=0 without removing
or reconciling those records can duplicate census and work counts.
Equal total launch count also does not prove equal launch enumeration.

A new plan needs an enumeration fingerprint including n, family, unit and
class, wheel prime ordering/levels, width/live periods, chunking and
sieve configuration. Adopt from the numerical committed boundary,
replay any required floored overlap with duplicate-count suppression,
and discard or reconstruct only uncommitted caches and accounting.
Preserve committed discoveries, certificates and census provenance.
Defaults have not changed in this review; the issue is safe future
adoption, not evidence of corruption in the saved campaigns.

## PML-004: bound model tails and complete the admissibility argument

**Disposition: Proposed.** Mathematical assurance, without new pruning.

### Primorial shifts have a finite exceptional collision set

For either sign, take m=n+1 forms with constants
\(0,\pm P_1,\ldots,\pm P_n\). At q>Q=200000>p_n, a collision between 0
and \(P_i\) is impossible. A collision between two nonzero constants
requires
\[
 q\mid P_j/P_i-1,\qquad 1\leq i<j\leq n.
\]
Let \(\Delta=\prod_{i<j}(P_j/P_i-1)\), without computing or factoring that
large integer. A collision class of size c loses c−1 distinct roots,
which is at most its number of pairs and hence at most its contribution
to \(v_q(\Delta)\). Thus \(m-w_q\leq v_q(\Delta)\).

Relative to the generic local factor
\(G_q=(1-m/q)/(1-1/q)^m\), the positive collision correction satisfies
\[
 \log(A_q/G_q)\leq\frac{v_q(\Delta)}{q-m}.
\]
The generic tail has log in \([-m^2/(2(Q-m)),0]\).
Using \(\sum v_q(\Delta)\log q\leq\log\Delta\) gives
\[
 -\frac{m^2}{2(Q-m)}
 \leq\log T\leq
 \frac{\log\Delta}{(Q-m)\log Q}.
\]
A scalar upper bound, using only the first n primes, is
\[
 \log\Delta<
 \sum_{t=2}^n(t-1)(n-t+1)\log p_t.
\]
At the actual filters this yields:

| Filter | m | Conservative lower / upper bounds on omitted log product |
|---|---:|---|
| A115785 n20 | 21 | −0.001103 / +0.001798 |
| A115786 n21 | 22 | −0.001211 / +0.002119 |

For A145743, shift differences are \(4(j-i)(j+i)\), whose odd prime
factors are at most 2n. For q>2n all n roots are distinct, so at n21
the omitted log product lies in
\([-21^2/(2(200000-21)),0]\), approximately [−0.001103,0].
These bounds control Euler-product truncation, not the BH conjecture,
integration, the composite-domain omission or first-occurrence scatter.
None can explain away a five-to-forty-five-day median distance.

### Forced classes and composite-domain infinitude

The existing root bounds imply no further single forced residue modulo
any prime q≥5. Primorial roots number at most \(\pi(q)<q-1\); square
roots number at most \((q+1)/2<q-1\). Only the implemented parity and
mod-3 classes are forced, outside their prime-equality exceptions.
The source's [assert_unit](../primorial_search.py#L205) already enforces
squarefreeness, so the repeated-prime unit defect from some older projects
does not apply here.

Unrestricted admissibility alone does not prove a composite-start
subsequence. For a conditional infinitude argument for A145743, fix an
odd prime \(\ell>n\) and set m=\(\ell t\). The forms
\(\ell t+4k^2\) are primitive; modulo q≠ell, scaling permutes the existing
allowed residue classes, and modulo ell every \(4k^2\) is nonzero.
They are therefore admissible linear forms. Dickson's conjecture predicts
infinitely many t making them all prime, and every t>1 yields composite m.
This completes the domain argument but does not justify restricting a
least-term hunt to one chosen factor ell.

## PML-005: a bounded larger-wheel option and a conditioned planner

**Disposition: Deferred.** The current primorial filters have 38 allowed
residues modulo 53. Adding that prime to the current wheel therefore
reduces generated candidates by exactly \(53/38\), approximately 1.39474,
over complete CRT periods. This is a candidate-count result, not a rate.
The engine already considers larger wheels; the new result is a concrete
way to cross its current table cap, with quantified costs.

For either primorial sign at its current filter, this full-53 partition
has the following arithmetic:

| Level | Primes | Modulus | Allowed residues |
|---|---|---:|---:|
| 1 | 5,7,11,13,17,19,23,37 | 1,375,739,365 | 21,086,208 |
| 2 | 29,31,41 | 36,859 | 13,200 |
| 3 | 43,47,53 | 107,113 | 37,696 |

The combined second modulus is 3,948,078,067<2^32, and device
\(W'=5,431,526,412,865,007,455<2^{63}\). Both
[`R1_MAX_BIG`](../primorial_gpu.py#L305) and
[`RES_MAX`](../primorial_gpu.py#L738) must rise from 2^24 to at least
21,086,208, a **25.6836%** increase. Raising only the planning cap does not
remove the constructor limit. A first level through 29 has 16,220,160
rows, but its complementary modulus exceeds 2^32; it is not a smaller
cap-only solution. The displayed noncontiguous layout is supported by the
existing split construction and its level ordering.

Wide records are required. The physical period becomes
32,589,158,477,190,044,730, 53 times the current primorial period.
A 32-period segment spans 1.04285e21 and needs at least **1.207e16/s**
to close within 24 hours from its start. A 160-period segment spans
5.21427e21 and takes approximately **130.5 hours** at the recorded
1.11e16/s. Even treating the entire count reduction as a runtime gain
would leave that full segment above 93 hours. These are arithmetic
scenarios, not forecasts for an implemented wheel.

Memory also changes materially. In the packed case the device phase
table uses \(4R_1\lceil G/2\rceil\) bytes for G window groups.
[Construction](../primorial_gpu.py#L2728) first allocates a uint64
G-by-R1 array and then a uint64 packed array before conversion/copy.
At an **illustrative**, unmeasured G=30, the device phase table alone is
about 1.18 GiB and those two host arrays total about 7.07 GiB, excluding
copies, residues and other tables. The actual proposed plan's G,
allocation peak, window depth and confirmation clock must be priced.

An alternative decomposition keeps **all eight** surviving classes modulo
210: two allowed classes modulo 5 and four modulo 7 inside the forced
mod-6 class. Removing 5 and 7 from level 1 gives modulus 39,306,839 and
2,635,776 rows per class, with
\(W'=155,186,468,939,000,213\). The conservative 96-period bound
\(97W'+32768<2^{64}\) fits the current narrow offset arithmetic.
This is not extra forcing: plain `unit=210` remains invalid, affine
class offsets need explicit support, and all eight streams must close
the same absolute interval before coverage advances. The combined
96-period interval spans 3.12856e21, approximately 78.3 hours at the old
rate, or 56.1 hours even under ideal count-to-rate scaling. It therefore
does not establish a one-day improvement either.

There is also a separate planning input problem:
[`plan`](../primorial_gpu.py#L699) takes `reference.floor_x(fam,n)` and
prices `expected_sweep` from that floor. `FOUND` is empty, so at current
n21 the plus and square reference floors fall back to 2 and 4, rather
than their recorded frontier or committed boundary. The campaign's
displayed model receives its frontier separately; this is a distinction
between planner inputs and forecasts, not evidence that the present
enumeration is wrong. A future planner should price the actual remaining
interval and deadline, freeze the selected configuration, and include its
inputs in caching/adoption provenance. No replacement plan has been
measured; the current roughly two-hour segments already limit the possible
benefit from adjusting confirmation latency alone.

Validate either representation on identical absolute intervals, with every
class, exception and output accounted for. Preserve the independent
oracle and PML-003's proof/cap/cursor requirements. Do not multiply the
1.39474 count factor by inherited width or wide-record rates and present
the result as a measurement.

## Existing work, limitations and future acceptance

The [optimization history](../OPTIMIZATION_LOG.md) records the modern
plus-two engine taken whole and measured on these forms. Periodic window
patterns, subset three-level CRT wheels, wide records, lazy folded
rounds, generated sparse tails and overflow fallbacks already exist.
`ROUND_FOLD=True` at [primorial_gpu.py:1709](../primorial_gpu.py#L1709)
replaced the retained `ROUND_WINDOW` alternative; a generic transfer
of the latter is not a new improvement.

The recorded local change was the extraction/queue rule, approximately
1.057× at A115785 n19. Hoisted validity masks lost at 0.978×;
window/queue/depth alternatives were already swept or priced. The greedy
wheel generator at [line 553](../primorial_gpu.py#L553) is not an exhaustive
optimization proof. PML-005 establishes arithmetic options under changed
bounds or class enumeration, but this review establishes no demonstrated
faster current wheel. Do not turn the existence of unsearched subsets
into a speedup estimate.

Any future explicit-level proposal must preserve all arithmetic and
enumeration constraints: W1,W2<2^32, device W′<2^63, R2,R3≤65535,
root capacity 32, and the appropriate narrow or wide offset bound.
Constructor list comparisons at lines 2476/2487 are lexicographic;
arbitrary noncontiguous levels need deliberate activation/validation,
not an assumption that every nonempty list is used.

Neither sign reflection nor a change to offset \(v=p-P_n\) equates
positive least terms across the primorial families. The latter is already
used correctly by [model.expected](../primorial_model.py#L102) to resolve
the narrow band above the negative-shift floor. Square-root/Legendre
membership formulations do not create an extra exclusion beyond the
exact killed sets and have no demonstrated cheaper device realization.

Before later implementation, normalize the recorded frontiers with
provenance, retain all historical fingerprints, and add actual n20/n21/n21
workloads on fixed absolute intervals. Fix PML-003 with failure and
cap-hit cases, and keep independent definition oracles. Preserve the
per-filter exception-zone coverage (`zone_n`); do not transplant the
primorial-ap low-pass defect, which has a different control flow.
Resolve the already-recorded stale `a(21) Q1` rung label separately from
coverage—it is not an additional bound.

Accept a performance change only with future evidence covering full
classification, proof acceptance, completed boundaries and correct
projected streams. This report authorizes no runtime work or campaign
start. The current outcome is modest deferred work sharing, a larger-wheel
option with substantial costs, more honest odds, and concrete correctness
prerequisites.

## Snapshot hashes

SHA256 values pin files read on 2026-10-20. Project README navigation was
edited separately and is not part of this source/data snapshot.

| File | SHA256 |
|---|---|
| `primorial_reference.py` | `0c117a6ce34c522b882adf259fb04aaab666be73fcedb091fae62e07eac597af` |
| `primorial_search.py` | `8fc4c4ff9e86e3840a38e82c4196e28d15daabf0e2f2e539da07a62ff871e9d7` |
| `primorial_gpu.py` | `191a729bc4b64ae75ddc731205967a95515d0336f78ff646bec7eab97dc6fa05` |
| `launch.py` | `970083d306d5dad7205c4f29f239624a899b881bc76f3941b8b0ed3055af15f1` |
| `score.py` | `17760af13b5d701f80030d06d2e4074588e822e0bb519c3f948f88318f86f344` |
| `primorial_model.py` | `622d291854113fa14f93285741a8fc276d43112e015c1b4d95f55d0c89b50b80` |
| `model_results.json` | `3913435cfd9b7289ace90c8e386c0376354748a08cd2845c8216e93c078f1d81` |
| `campaign_checkpoint_a115785.json` | `b72be4476da4f6c867d078f1798d8bdd0ab7db7378d743f04afe4aff7b07c5c4` |
| `campaign_checkpoint_a115786.json` | `5920af6fe278775c512b18f5b300e4cbd13b02421d6883912ea435ff05677d76` |
| `campaign_checkpoint_a145743.json` | `18b15284ee0e9cd4ce1223a6006cf22350ae4b90cc47ab4779555231abf275ee` |
| `evidence/a115785_discoveries.json` | `15568db00d655c797fbd562bf7eb96ab116e0950b160eac0173628a5e4fef90f` |
| `evidence/a115786_discoveries.json` | `d55ae4c1770ca61f029a141940e5e5b1e154679a7281711597bd47502f2225c6` |
| `evidence/a145743_discoveries.json` | `4177b435853e51cbed980a95e1eaa3056ef83afac4ecfe759dd8cecf0d915504` |
| `evidence/A115785_a19_7858467306309706402625473.json` | `6a0d80763e053525ed9f8fe791253d38bee4ad7d70c2cc0e25a185d406ef28c6` |
| `evidence/A115786_a20_276111714233825559827.json` | `daafb16111aade2018acfc89b795ccd65f3fefbe635182cbcfcb9d43875c2202` |
| `evidence/A145743_a20_86871442473592036108753.json` | `97b1401b9083a19dd52b182f956a388afbe9dedad5845720025aa63d5a4c6940` |
| `OPTIMIZATION_LOG.md` | `d7da6caa7198ff5edb35629f9c6c935be6b7fa9f500a516225144fa12a555357` |
| `BENCHMARKS.md` | `41846ebaa4d4d12ecdd12db74de468caa5f296c0255a461bccaee924c6afd9d5` |
| `RESULTS.md` | `4edeb12bca0a5107d2f8da2e514c924c2d5aef5114c722d5d38140128dd1b6df` |
| `../huntlib/certificate.py` | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
| `../polynomial-runs/poly_reference.py` | `cac1c856ab0cc3b8a7108403c9f4c0cbd50d6c2368c1ec245f4fae726cee62d2` |
| `../polynomial-runs/campaign_checkpoint_a092120.json` | `299ec5d79c82f343eea979b82826b164cd982c74fb2a06a5e3aa75d895e1dead` |
| `../polynomial-runs/codex-reviews/2026-10-20-static-review.md` | `882b6957d20d9a8a29cd3bfb0c0e7e8aa257167428bdb7344c93f24c35dfa608` |
