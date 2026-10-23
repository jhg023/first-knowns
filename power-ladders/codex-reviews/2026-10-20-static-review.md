# Power-ladders static mathematical review — 2026-10-20

**Author: Codex (OpenAI).** The review team examined this project only,
under [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). This was entirely static:
source, documentation, saved evidence, measurements and checkpoint reads,
plus finite arithmetic. No GPU use, project imports, models, searches,
primality experiments, tests, benchmarks or campaign changes occurred.
Only documentation was edited.

The main new search proposal extends the semiprime wheel's factor-count
argument through the remaining sieve. A related exact counting formula
supports a domain-aware wheel planner. Neither has a measured runtime gain.
The current semiprime hunt already includes the substantial 3.69× wheel
and 1.30× cofactor improvements; those are existing work.

The strongest evidence-backed one-day opportunity among the four families
is the previously documented A229902 plateau and its next two model targets.
The active A229630 hunt can complete substantial new coverage in a day,
but its old 11-hour median and 25-hour expected confirmation clock are not
current conditional forecasts. A229626's present segment takes about
86 hours at the recorded rate, so a deadline changes the planning problem.
No newly established optimization guarantees an additional term in a day.

## Evidence classes and snapshot

- **Proved here:** mathematical implications, exact CRT counts and
  counterexample classes derived below.
- **Observed:** source behavior and fields in saved evidence/checkpoints.
  Certificate flags are repository evidence, not independently rerun proofs.
- **Recorded measurement:** timings already in the optimization log.
  Chained rates and old-filter rates are explicitly distinguished.
- **Unmeasured:** proposed implementations, inherited width scenarios and
  any claimed effect on a future campaign.

The repository HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`.
The worktree includes later changes; the SHA256 table pins the reviewed
files. Links are relative to this report; line numbers below are snapshot
anchors, with symbols identifying the relevant code.

**The A229630 checkpoint was changing during the review.** Its pinned
snapshot was read atomically and says `saved = 2026-10-20 14:08:30`.
Its hash below describes that snapshot, not the eventual contents of the
live file. We did not stop the hunt, edit the checkpoint, or repeatedly
chase its advancing cursor.

## All families and actual frontiers

The definition is **at least n prime power values**, not an exact run:
the same least term can settle several consecutive indices. All floors
are inclusive. See [power_reference.py](../power_reference.py), module
contract and `RUNS_PAST` at 212, `FOUND` at 218.

| Entry | Conditions at index n | Actual recorded frontier | Next search |
|---|---|---|---|
| A229626 | Positive integer m; `2m^k−1` prime, k=1..n | a(11)=26985725415370251655 | n=12 |
| A229627 | Prime q; `2q^k−1` prime, k=1..n; q itself is an additional form | a(11)=1002522190109444576389 | n=12 |
| A229630 | Semiprime m, exactly two prime factors counted with multiplicity; same power conditions | a(10)=228902892109166911 | n=11 |
| A229902 | Positive integer m; `19m^k+1` prime, k=1..n | Published a(8)=1944616927560 has recorded run 9 | a(9)=a(8) follows from the recorded run; first distinct target n=10 |

[RESULTS.md](../RESULTS.md), lines 7 and 28–30, still says no campaign has
run. That statement is superseded by three checkpoints and seven discovery
files. The source `FOUND` table also remains empty, so a standalone model
or fresh opening based on it must not be mistaken for the resumed state.
This report makes no assertion about present OEIS submission status.

The seven individual evidence files record `certificates_verified=true`
and no unproved values:

| Family | Additional recorded terms | Evidence |
|---|---|---|
| A229626 | a(10)=10680411518375521; a(11)=26985725415370251655 | [a10](../evidence/A229626_a10_10680411518375521.json), [a11](../evidence/A229626_a11_26985725415370251655.json) |
| A229627 | a(9)=915805778084569; a(10)=691680697554493219; a(11)=1002522190109444576389 | [a9](../evidence/A229627_a9_915805778084569.json), [a10](../evidence/A229627_a10_691680697554493219.json), [a11](../evidence/A229627_a11_1002522190109444576389.json) |
| A229630 | a(9)=687860415949; a(10)=228902892109166911 | [a9](../evidence/A229630_a9_687860415949.json), [a10](../evidence/A229630_a10_228902892109166911.json) |

Their recorded proof routes total 73 certificates: 11 deterministic
Miller–Rabin certificates and 62 BLS75 Theorem 15 certificates. The
semiprime factors are respectively `7 × 98265773707` and
`17 × 13464876006421583`. These are recorded verified claims, not
fresh primality checks by this review.

No A229902 checkpoint or discovery evidence file was present. Its
run-nine plateau is already stated in `RUNS_PAST`, the reference gates,
and RESULTS lines 11–16; the latter records the nine-value certificate
drill and a factor 23 of the tenth value. Published minimality at n=8
plus primality through n=9 proves the plateau, conditional on those
existing claims. Producing its normal evidence artifact is a future
implementation/verification task, not a new search theorem.

## Saved coverage, rates and one-day limits

Write B for the exclusive committed coverage boundary: all eligible
values below B, above the campaign's applicable floor, have been classified.
The next eligible value may equal B. Partial launch count `u` is not a
numerical prefix. [launch.py](../launch.py), `swept_k` at 796–802, takes
the maximum of the closed period boundary and the carried floor.

| Snapshot | Filter; class; depth | W; periods per segment | j; u / launches | B |
|---|---|---|---|---|
| [A229626](../campaign_checkpoint_a229626.json), saved Oct 16 23:39:11 | n12; unit 1; 8192 | 1861574518861802745; 256 | 14; 831 / 3762990 | 27037605571656084405 |
| [A229627](../campaign_checkpoint_a229627.json), saved Oct 18 13:13:06 | n12; 1 mod 6; 8192 | 3723149037723605490; 256 | 768; 58303 / 174096 | 2859378460971729016320 |
| [A229630](../campaign_checkpoint_a229630.json), saved Oct 20 14:08:30 | n11; unit 1; 8192; p3 | 86584861342409430; 128 | 2306; 3710 / 32706 | 199664690255596145580 |

A229626's carried floor is B itself; its current jW is below that floor.
A229627's carried floor is 1906252307314486010880, below its new closed
boundary. A229630's carried floor is 55630773412498058775, also below B.
All three pinned `pending` lists were empty. Empty pending is not evidence
that an unfinished segment contains no later hit.

The current source handles all sorted pending records from a closed
segment and then carries the classified boundary on promotion:
`follow_frontier`, launch 974–1000, and campaign loop around 1253–1257.
It already avoids blindly restarting at a found term. This is not a new
suffix-reuse opportunity.

[BENCHMARKS.md](../BENCHMARKS.md), the wall-clock table from line 65,
and [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), rounds 5–7, provide:

| Relevant filter | Recorded usable rate evidence | Interpretation |
|---|---|---|
| A229626 n12 | About 1.54×10^15 m/s | Earlier 1.49×10^15 multiplied by measured aligned-read gain 1.032 at the actual n12 height |
| A229627 n12 | Aligned-read ratio 1.089 at q≈2.86×10^21 | No absolute current n12 rate found; 1.67×10^16 q/s belongs to n11 |
| A229630 n11 | About 3.1×10^15 m/s | Chained 2.25×10^15 × 1.30 × 1.057; not a new live measurement |
| A229630 n12 | About 8.3×10^15 m/s | Chained measurement for the next filter, not the present n11 hunt |
| A229902 n10 / n11 / n12 | 1.23×10^15 / 2.72×10^15 / 4.58×10^15 m/s | Historical configured-filter rates; no current checkpoint observed |

The frozen S229630L score of 2.513×10^15 m/s has a different work unit:
four branch sweeps each pay startup. The benchmark explicitly says its
ratio is not the steady-state gain. Likewise, `u/L` counts launches across
unlike branches, not equal-duration work; see `SemiprimeEngine` and
`sweep` in [power_gpu.py](../power_gpu.py), 5310–5428.

The following are scalar calculations from stored data, not forecasts:

- **A229626:** a full current segment is
  476563076828621502720 units, about **85.96 hours** at 1.54×10^15/s.
  Its tiny partial launch fraction does not bring closure inside a day.
  The old n12 median 2.479×10^21 is roughly 18.4 days of continuous
  travel beyond B at that rate, before confirmation rounding. POW-002
  gives a smaller-segment deadline option, not a one-day median.
- **A229627:** a full n12 segment is 953126153657243005440 units.
  A complete segment per day requires about **1.103×10^16 q/s**;
  an absolute current-filter rate is missing. Reaching the old n12
  median 2.145×10^24 from B in one day would require about
  **2.48×10^19 q/s** before closure/proof costs. The prior n11 rate
  must not be relabeled as n12 evidence.
- **A229630:** a full segment is 11082862251828407040 units,
  about **0.993 hours** at the chained rate. With fixed rate and no
  find, startup or proof costs, a day covers 24.167 full-segment work
  units. Depending on the unknown time already spent in the current
  branch sequence, that permits 24 or 25 closures, ending at
  **465653384299477914540** or **476736246551306321580**.
  This is coverage arithmetic, not a success probability.
- **A229902:** the saved n10 median 1.173×10^17 and n11 median
  4.340×10^19 correspond to the documented approximately **95 seconds**
  and **4.4 hours** at their stored rates. These are plausible one-day
  targets already available without a new algorithm, subject to the
  model, ordered coverage, startup and certificates. The n12 median
  1.385×10^22 corresponds to about 35 days. Later-index predictions
  share the old frontier floor; they are not independent conditional
  waiting times to add together.

The saved [model_results.json](../model_results.json) uses original
published frontiers. Its A229630 n11 median 1.1776×10^20 is now **below B**.
The log's “25 h” is an **expected confirmed-search clock** for about
2.8×10^20 line from the older cursor near 5.563×10^19, not a median
and not remaining time from this snapshot. No current conditional
probability or median was recomputed.

## POW-001: Extend the semiprime factor state beyond the wheel

**Status: new mathematical pruning proposal; unmeasured runtime.**

Round 5 already removes wheel residues containing two distinct small
prime divisors. Round 6 recognizes a wheel factor p and removes every
additional tested small factor from its cofactor. See optimization log
267–558, CPU `semi_cofactor_ok` at [power_search.py](../power_search.py)
220–237, and device `engine_kills` at power_gpu 995–1013.

What remains is the **zero-free wheel branch**: m has no wheel factor,
but can still have two factors among nonwheel sieve primes. At current
n11 it accounts for approximately 20.65% of wheel candidates; the other
79.35% already receive the cofactor sieve. That candidate share is not
a measured fraction of runtime.

Let D be the largest prime-test bound. If a semiprime m has both its
prime factors at most D, then m≤D². Therefore, for **m>D²**,

`Ω_{primes ≤D}(m) ≤ 1`,

where multiplicity is counted. Two distinct small factors are enough to
reject m; a repeated small factor also permits rejection above this floor.
For current D=8192, D²=67108864, far below the pinned active front.
The existing cofactor floor 89D=729088 is smaller and is **not** sufficient
for this stronger zero-free-branch rule. Preserve independent exhaustive
handling of the intervening exception interval.

For the distinct-factor part, keep disjoint candidate bitsets B0 and B1,
meaning zero or one tested small factors. Let Zq mark `m≡0 mod q` and
Pq mark survival of all ordinary power-form exclusions at q. Simultaneously:

```
B0' = Pq ∩ B0 ∩ ¬Zq
B1' = Pq ∩ ((B1 ∩ ¬Zq) ∪ (B0 ∩ Zq)).
```

Use the old B0 in both right-hand sides. A second zero disappears.
Initialize B0 with the zero-free wheel branch; one-zero wheel branches
already implement the stronger “no more factors” case. Carry the state
when extracting survivors into later rounds and the tail. A q² test
handles multiplicity; omitting it merely weakens pruning and does not
invalidate the distinct-factor rule.

Primes whose power forms have no roots still matter to the domain.
`_cofactor_primes`, search 215–218, currently omits them. Testing a selected
subset is safe but weaker; claiming the complete Ω bound requires all
the named primes and repeated-factor handling.

There is an exact density expression for any finite added prime set S.
Conditional on ordinary power-form survival, zero has probability
`zq=1/(q−wq)`. CRT gives the retained fraction

`∏(1−zq) · (1 + Σ zq/(1−zq))`.

This is a full-period candidate ratio, not an empirical rate or an exact
count in the current incomplete interval. Extra state operations may cost
more than the later work removed. The modest affected branch means the
proposal must earn its place; no large speedup is established.

**Future Claude handoff:** keep the oracle's original semiprime definition
and independent factorization. Derive CPU integer predicates separately
from the device masks, including m=D², prime squares, two distinct small
factors, no small factors, and factors at a prime with wq=0. Compare the
new complete survivor stream to the old stream projected through that
predicate, then compare both against original-domain solutions above the
proved floor. Version the branch/state layout and coverage floor. Raw
census and fingerprints may change because composites leave earlier;
justify that change with projected-stream parity, not a newly accepted
unexplained checksum.

## POW-002: Plan for the semiprime domain and for a deadline

**Status: new exact planner objective; no feasible faster replacement
established. Smaller-window scenario is unmeasured at the current filter.**

`semiprime_plan`, power_gpu 5258–5286, inherits the unrestricted plan,
inserts 2 in a level whose bounds permit it, then halves PB so the doubled
wheel keeps the same segment length. It checks branch capacities, but
does not optimize wheel subsets using the semiprime-domain count.

For a chosen wheel prime q let wq be the number of power-form roots.
Zero is always allowed by those forms. Put `aq=q−wq−1`, the number of
allowed nonzero residues. Here aq≥1 because residue 1 always survives.
For a wheel set Q, define `A=∏aq` and `H=Σ1/aq`. The exact count allowing
at most one zero is

`R(Q)=A(1+H)`;

the zero-free branch has A residues and the one-zero share is H/(1+H).
Adding a new prime q changes candidate density by

`[aq + 1/(1+H)] / q`,

whereas unrestricted planning uses `(aq+1)/q`. Thus the optimal wheel
ranking and the cofactor-sieved branch cost need not match the inherited
unrestricted plan. This supplies a mathematical objective, not a selected
new wheel or a timing result.

A future planner must price all four branches, startup, residual factor
state, tables and confirmation length, and retain the existing W1,
combined-W2, Wp, residue-count and wide-record bounds. The checks in
`semiprime_plan` are necessary but do not measure whether a candidate is
faster. No numerical search of possible wheels was performed here.
There is also a mathematical floor constraint: `SemiprimeEngine`,
power_gpu 5326–5332, rejects a wheel whose largest prime exceeds 89,
because its square exceeds the existing SEMI_FLOOR. A larger wheel prime
requires a new independently covered exception floor and an updated
largest-prime-times-depth cofactor bound, even if every word/table bound
fits.

There is also a distinct **fixed one-day objective**. For a fixed filter
and correctly conditioned hit model, success probability is increasing
in the fully classified endpoint. Maximize that endpoint by the deadline,
rather than only minimizing expected time to a future find.
The existing planner prices `expected_sweep` times density/cost:
power_gpu 667–798 and [power_model.py](../power_model.py) 163–186.

For A229626, keeping the same wheel but choosing PB32 would require
only **6.895×10^14 m/s**, 44.77% of the current rate, to close its first
32-period segment in a day. The inherited width constants at power_gpu
723–724 give `0.70/1.118≈0.626`, an illustrative **17.2-hour** full
segment. PB64's inherited `0.84/1.118` implies about 28.6 hours.
These are inherited, explicitly unmeasured and optimistic constants
(power_gpu comments 720–722), not a measured current n12 width curve.
Both remain wide
records at this W. The PB32 endpoint from j14 is
**85632427867642926270**, still far below the old Q1≈7.64×10^20.
Obtaining some confirmed coverage is materially different from making
a next term likely within one day.

Changing PB changes launch enumeration. Adopt from the numeric committed
boundary B, replay the uncommitted segment, and clip at B even when the
new j is nonzero. Preserve all prior evidence and carried claims. A
same-W change can still invalidate `u`; a different wheel also changes j's
denomination. The configuration fingerprint must include levels, unit and
class, branch order/state, PB/live periods, depth, pruning floor, launch
decomposition and record format.

Current adoption in launch 604–627 explicitly permits some replayed
partial census counts. That is a recorded policy, not a proof that counts
are unique. New work must either reconcile them or label replay overlap.
Discarding old partial pending/counters and replaying must be coordinated;
resetting only u while retaining records can duplicate classification.
None of this report authorizes changing the live campaign.

## POW-003: Condition the semiprime model on its smaller factor

**Status: constructive heuristic model repair, not a proved asymptotic
or a runtime optimization. No fresh numerical model was executed.**

`_density_curve`, model 95–105, multiplies the unrestricted power-tuple
series by `log log m / log m`. The module's lines 18–25 explicitly admit
the small-prime correlation this ignores. Semiprimes are less likely than
uniform integers to occupy zero modulo a fixed prime, while zero avoids
every power-form root. That changes the local normalization.

Let S_P be A229627's singular series at the same index n: the forms are
the prime variable itself and `2m^k−1`, k=1..n. Let wℓ count only the
power-form roots. Fix the smaller prime factor p and write `m=p r`,
with r prime and r≥p.

For ℓ≠p, multiplying r by p permutes nonzero residues. The r-prime
condition contributes root zero, so the branch has wℓ+1 roots, exactly
as in S_P. At ℓ=p all power values are −1, so only r=0 is excluded.
The exact local-series identity is therefore

`S_p = S_P · (p−1)/(p−w_p−1)`.

The corresponding fixed-p Bateman–Horn density in m coordinates is

`λ_p(m) ≈ S_p / [p log(m/p) ∏_{k=1}^n log(2m^k−1)]`.

The factor 1/p is the coordinate Jacobian. Sum only p≤√m to assign the
smaller factor once; squares are an endpoint case, not a reason to count
both ordered factorizations. The tuple is admissible: at ℓ≠p choose
r=p^−1 so m=1, and at ℓ=p choose r=1. For odd p the reciprocal
power polynomials are Eisenstein at 2. For p=2 the reciprocal binomial
has 2-adic Newton slope with denominator k, since gcd(k,k+1)=1,
which supplies the corresponding irreducibility argument. Equivalently,
every root of `X^k−2^(k+1)` has valuation (k+1)/k; a monic rational
factor of degree d would have a nonzero integer constant term of valuation
d(k+1)/k, forcing k to divide d and excluding a proper factor.

Summing fixed-p asymptotics uniformly up to a growing √m is an additional
heuristic, and doing it literally is expensive. A practical model needs
a finite small-p sum and a justified approximation to the remainder.
Under that heuristic the leading normalization is S_P, with finite-height
small-factor corrections, rather than the unrestricted series. It is
not valid simply to multiply all old waiting times by a constant.

For scale only, the stored n11 series are
`S_P=1454095.2340418` and `S_any=4498857.463009329`; their ratio is
about **0.3232**. This is finite arithmetic on saved constants, not a
threefold forecast correction: the p-dependent factors and finite-height
sum still matter. Revalidate a repaired model against all historical
terms and the new evidence before using it to rank campaigns.

The old validation has 16 published draws, pooled E≈12.03 and reported
Gamma lower-tail probability≈0.158. That does not validate the proposed
repair or calibrate the current conditional front. Also, unlike an
additive linear tuple, these power forms have varying root counts at
arbitrarily large primes. The generic “wq equals number of forms beyond
a cutoff” tail bound from linear/LCM reviews does not apply. QMAX=200000
is a truncation choice here, with no such error guarantee established.

## POW-004: Preserve unresolved domain and primality claims

**Status: static correctness findings; no demonstrated missed current
term. They are prerequisites for extending the search safely.**

There are two separate semiprime-domain rejection issues in
`is_semiprime_fast`, search 472–491.

First, optimization log 256–265 already notes that the early
`mr_is_prime(x)` rejection at line 480 can reject a semiprime that is a
probable-prime false positive above the deterministic MR bound. This is
known prior work, not a newly discovered optimization.

Second, the branch at 486–487 assumes that a residual R>1 after finding
one proved prime factor is composite. That is not the factor API's
contract. [huntlib/certificate.py](../../huntlib/certificate.py),
`factor_partial` 220–255, leaves **whatever bounded effort did not prove
and split** in R; `_proved` 172–174 deliberately accepts primes only
below `MR_VALID_BELOW`.

A counterexample class needs no numerical primality experiment. Take
an odd prime P with `MR_VALID_BELOW ≤ P < 10^40/2`, and set x=2P.
It is a semiprime inside the configured term ceiling. Its initial MR
test fails because x is even. Trial division extracts 2, while the large
prime P cannot be split and is not admitted by `_proved`. Thus
`fac={2:1}, R=P, omega=1`, and line 487 returns False. This proves the
domain predicate is incorrect on such inputs; it does **not** prove any
particular member also satisfies the power ladder.

Use a three-way domain result: proved member, proved nonmember,
unresolved. An unproved residual cannot silently become a composite
witness. Prove the remaining factor when possible; otherwise retain the
candidate or a durable unresolved-coverage barrier. The current m front
is below the approximately 3.317×10^24 deterministic bound, so these
large-domain defects do not establish a flaw in the pinned current
coverage. They matter well before the configured 10^40 ceiling.

Separately, `record_discovery` obtains `certs, unproved` at launch 902,
but mutates `found` at 948–949 and announces that the find stands even
with unproved values at 966–971. Powers exceed the MR bound much earlier
than their base m; current discovery evidence appropriately uses BLS
certificates. A future certificate failure must hold the relevant
settlement/promotion until the required prime values are proved.

For A229630 the domain itself also needs proof: two prime factors counted
with multiplicity, their product equal to m, and a proof for each factor.
The factor labels stored at launch 945–947 are not that proof by
themselves. `certificate.py` 423–455 can move an unproved claimed factor
into the residual while the remaining proved part still suffices for an
N±1 certificate. Therefore successful ladder-value certificates need not
prove every factor of m. The two recorded semiprime discoveries have
factor sizes below the deterministic bound; this is a future configured-
domain obligation, not an objection to those records. A229627 already
requests a separate certificate for its prime base at launch 374–377.

For an at-least index, a proved prefix can settle the indices it actually
proves; an unproved later value must not create a rider. A composite
stopper is needed for an asserted exact run length, but not to establish
membership in an already proved at-least prefix. The reference re-read at
launch 887 is capped at 64 despite its “NO cap” comment: reaching the cap
does not establish the actual stopping index.

The exact-run CENSUS-hiding issue from polynomial-runs does **not**
transfer wholesale. Here an overlong probable-prime run cannot turn a
true next-index hit into a shorter, irrelevant index: the conditions
nest. Keep the safeguard specific to unresolved domain rejection,
certification and any cap-dependent claim.

**Future validation:** independently exercise the factor API's unproved
prime residual, a genuinely composite residual, repeated prime factors,
and certificate failure after an apparently valid discovery. Verify that
no unresolved candidate is discarded from a claimed exhaustive prefix
and that no unproved rider enters `found`. Preserve the seven existing
complete certificate records and the oracle's independent original
definition. This is not permission to run these checks during a static
review.

## POW-005: Global forcing and family relations

**Status: mathematical assurance and reuse limits; no new pruning.**

The current forced classes can be justified globally, rather than only
by a finite prime scan. For the two unrestricted-power-form domains,
m=0 gives −1 and m=1 gives 1 for `2m^k−1`, so both residue classes
survive modulo every prime. No prime can force a single residue class
from these power forms alone.
For A229627 the domain excludes zero, but ±1 both survive every prime
q>3: at −1 the power values alternate −3 and 1. Only the existing
2 and 3 restrictions can collapse the nonzero choices.

For `19m^k+1`, residue 0 always survives; residue 1 also survives unless
q divides 20. Thus only 2 and 5 can force the existing class. At the
relevant depth the nonzero classes modulo 5 are excluded by exponents
1, 2 and 4. These witnesses prove absence of further forced primes;
they are **not** a restriction to the witness residues, which would
discard possible least terms. Preserve the prime-equals-sieve-prime
exception zone covered by `k_floor`, search 156–178.

Admissibility alone is not infinitude. The reciprocal polynomials for
the unrestricted families are Eisenstein at 2 or 19; with the local
witnesses, a prime-tuples conjecture for polynomial forms supplies the
usual conjectural infinitude, not Dickson's conjecture for linear forms.
For the semiprime family, the fixed branch m=3r, r prime, is admissible
and has the same reciprocal Eisenstein argument. No unconditional
infinite supply or extra thinning follows.

A229627 and A229630 are subsets of A229626's integer domain. Hence if
an unrestricted least term also satisfies one restricted domain, it
settles that restricted index too. A229630 a(9)=A229626 a(9) is already
recorded. The new unrestricted a(10) and a(11) have recorded prime-factor
multiplicities 3 and 7 respectively, so they supply no such rider.
Conversely, a restricted-domain find gives an upper bound for the
unrestricted sequence, not a leastness proof without exhaustive coverage.
The current coverage, filter and domain facts yield no new equality or
first term from this observation.

## Prior work, implementation priority and acceptance

The independent oracle, CPU discrete-log root construction, device tables
built from the shared killed-residue routine, exact root lists, window sieve, staged Fermat rejection and
classified-boundary promotion are already implemented. The following
must not be advertised as new:

- Round 5's at-most-one wheel factor, including even semiprimes, and
  round 6's one-wheel-factor cofactor sieve: measured and shipped.
- Wheel-prime square masks, including 4 and 9, and an earlier cofactor
  Fermat test: explicitly priced but unbuilt in optimization log
  515–536; roughly 1.05–1.06 and 1.03 respectively in that context.
- Round 7's aligned window read: shipped, with current-filter gains
  1.032–1.089. Recommending a generic window-read donor would overlook it.
- Perfect-power input exclusions: sparse and often caught by the leading
  Fermat stages; no meaningful additional current-density gain established.

For a later Claude implementation, resolve POW-004's proof obligations,
then assess POW-001 at the actual n11 height and its next n12 shape.
POW-002 should compare full branch costs and completed coverage, not
candidate counts alone. POW-003 is needed before interpreting semiprime
clock changes as credible probabilities. Keep the independent oracle
unchanged and add separately derived CPU/device checks.

[score.py](../score.py), lines 113–144, freezes actual n11 semiprime
work, but the unrestricted and prime-domain headline shapes are still
older n10/n9 openings. Preserve those historic checks and add current
shapes when evaluating changes. A mathematically justified earlier
domain rejection needs a projected-stream fingerprint, original-domain
parity and explicit census provenance. A changed wheel/branch/PB needs
a new complete enumeration identity and numeric-boundary migration,
not acceptance of an old `u` because its W happens to match.

No implementation or performance experiment was done by this review.

## Source and snapshot hashes

SHA256 values below are for the reviewed source/evidence snapshot.
The active A229630 hash is historical by design.

| File | SHA256 |
|---|---|
| power_reference.py | `2da8faf15065f73993332e63a7327e2feff7276abc9da7f5e4b4fbbd358a8dd0` |
| power_search.py | `a002da753ddc8a9bde2e5402a02ad8701b86f47289e0e23eb3fd34a6aebbbbd0` |
| power_gpu.py | `ef34a5a27572982fb981f93581a51976a0a709cbbb2fce112acaefa7dfb4b93b` |
| launch.py | `44ce03e8e7ee2a34e1618aea700cdf0c5a2c2412dd9c6971c8720b1b3820fa98` |
| score.py | `c2ca4b8b95b1bc2430d26faf5a0851ef3ac1c7887f9d88d86b52b2ff89a6855e` |
| power_model.py | `c03b230f3fc76459c32e4b3e2ba03edce5c6af2204c1aa3bad5eda904a2455d2` |
| model_results.json | `7a7a07dbca4f31fc562476b5b36723054a9fb37f792680f2b8796fb32372a5c4` |
| OPTIMIZATION_LOG.md | `652586eb6d582daf622beb8599fee78abf6699f3c010e3f798871b34a15754fe` |
| BENCHMARKS.md | `0ed2cca4bd1eef84e12162bd15a5fa1528250c9a33637ec1022c217a3abbd761` |
| RESULTS.md | `d59a39b10da7ecdb902941daa51a900f77386d617bf5b0db0d8ec40f141eeaf0` |
| ../huntlib/certificate.py | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
| campaign_checkpoint_a229626.json — Oct 16 snapshot | `2e95975bbd700786f52387b1ba0b562465110b42325f55876016fa9a431c2c49` |
| campaign_checkpoint_a229627.json — Oct 18 snapshot | `14d5b1a55384fe52353b7b732baeaf643005c429a593df8268749e6f25c16324` |
| campaign_checkpoint_a229630.json — Oct 20 14:08:30 snapshot | `7f134145b5081edf825acc94be57ac8b58249a4d916b42f4954e03e8a2c9d743` |
| evidence/A229626_a10_10680411518375521.json | `2caf8f468dd03a99703a1def7946682be576ead0ad6daf7d456111c8b3cce26a` |
| evidence/A229626_a11_26985725415370251655.json | `4a529beaa59e8af85c8745e4e52d06a144ab42761e2ca84073a184f7e3eac319` |
| evidence/A229627_a9_915805778084569.json | `dbdef2bf18c07e511499c365eb6cec1d3275adead78df004f7d1d2e2827f7e46` |
| evidence/A229627_a10_691680697554493219.json | `a256857620df0b3c61d071dd1a024ec9915ac34a76d03b9a0ba160c4a06a5716` |
| evidence/A229627_a11_1002522190109444576389.json | `622d8b72703cd12526a58bb85305cc3f9b3e1c45f1da4ccc5ab9c69756e0023b` |
| evidence/A229630_a9_687860415949.json | `21e8f9e61004cdeb38da76e6191029ddc3b62097e64db75098a2c1ec146aa90a` |
| evidence/A229630_a10_228902892109166911.json | `b4e4f7c265cb858198819ea00dc7a2f32d2c657700a0444f686372f12e33ba70` |
