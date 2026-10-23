# Plus-two cliques: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A083518 and A083519.
**Status:** mathematical analysis and implementation handoff.
Workflow: [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

The review team examined this project only, with complementary mathematical,
implementation and evidence checks. Source, documentation, checkpoints,
evidence and stored model results were read. Hashes and lightweight
arithmetic were computed. No project engines, models, oracles, primality
experiments, tests, benchmarks, campaigns or GPU operations ran.

## Assessment

**The most useful opportunity is a change in what the planner optimizes.**
For A083518, the saved plan cannot complete even its first unresolved
segment within one day at the recorded actual-prefix v3 rate: about
**43.3 hours remain**. A candidate found during that day would not yet
have the coverage needed to certify it as the least. A shorter completed
interval can make a one-day result possible even with lower throughput.

**PTC-001** gives exact throughput thresholds for that tradeoff. It does
not claim a measured faster engine or a one-day median. A 32-period plan
would need at least 37.5% of the recorded 160-period rate to close once
within a day; a 64-period plan needs 75.0%. The inherited width model puts
64 periods almost exactly on the deadline, but those ratios have not been
measured on this actual prefix and v3 implementation.

**PTC-002** bounds the omitted singular-series normalization within roughly
-0.091% to +0.380% at the current prefixes, too small to explain a large
clock reduction. **PTC-003** supplies a short complete proof of the
documented absence of further forced primes. **PTC-004** refines a sound
segment-reuse idea that was already explicitly priced and declined.
No new large candidate-density reduction has been established.

Labels below distinguish **proved mathematics**, **observed source/data**,
**previously measured here**, **old model assumptions**, **unmeasured
proposals**, and **heuristic probability estimates**.

## The two definitions and their actual fronts

A083518 starts at a(1)=3 and chooses the least integer a(n)>a(n-1) for
which a(n)*a(i)+2 is prime for every i=1..n-1. A083519 starts at
**a(0)=1**, with i=0..n-1. It is essential to preserve that offset:
A083519's a(18) imposes 18 conditions, and its open a(19) imposes 19.
The open A083518 a(20) also imposes 19.

There is **no self condition** a(n)^2+2. A083518's a(2)=5 already
demonstrates why adding one would change the sequence: 5^2+2=27.
There are no riders or exact-run derived sequences here. Each discovery
adds a new multiplier, so the next filter depends on the value just found.
A full run at filter n is capped at n and has no composite next-rung
stopper. See [plus2_reference.py](../plus2_reference.py), lines 1–44,
101–108, `FAMILIES` at 142 and `forms`/`nforms` at 275–284.

| Family | Original published frontier in the source | Project's last recorded term | Open term |
|---|---|---|---|
| A083518 | a(13)=77597861913 | [a(19)=517222792129337171163](../evidence/A083518_a19_517222792129337171163.json) | a(20) |
| A083519 | a(10)=8403613179 | [a(18)=1352093682658200396075](../evidence/A083519_a18_1352093682658200396075.json) | a(19) |

The 14 discovery files cover A083518 a(14)..a(19) and A083519 a(11)..a(18).
All have `certificates_verified=true` and empty `unproved` lists.
[RESULTS.md](../RESULTS.md), lines 16–31, records their independent
verification on 2026-10-02: 209 certificates, comprising 143 deterministic
Miller–Rabin and 66 BLS75 Theorem 1 certificates. Reading these flags and
the verification account is not a new independent verification.

The final evidence files contain their full prefixes, verification fields
and least claims. A083518's least claim at lines 398–400 begins at
3650348055212814106; A083519's at lines 488–490 begins at
19935451450502600260. Eligibility follows from the primality proofs;
minimality also depends on exhaustive coverage from the previous term+1,
the justified forced class, and every preceding prefix term being correct.

The source `FOUND` table remains empty (reference line 197).
Resumed campaigns register checkpoint finds before building their real
filters: `Campaign._register`, [launch.py](../launch.py), lines 764–770.
A standalone model or fresh campaign without those checkpoints sees the
older published frontier. Normalizing this evidence into the permanent
frontier is an existing open task, not a newly discovered speedup:
RESULTS lines 242–254 and OPTIMIZATION_LOG lines 859–873 explicitly say
so. Updating `FOUND` alone is insufficient because opening/frontier
consumers and offset drills also read the published table.

The repository's statements about OEIS submission status refer to its
2026-10-02 export. This static review makes no claim about current online
publication status.

## Checkpoints, partial work and current measurements

Both checkpoints were saved on 2026-10-02 inside the first segment after
their last discoveries. Both have unit=6, residue=3, q2=65536, a wide
survivor record and a 160-period segment. The physical candidate is
`x=3+6*z`; all W and rate figures below are already in published-term
units, not z units.

| Field | [A083518 checkpoint](../campaign_checkpoint_a083518.json) | [A083519 checkpoint](../campaign_checkpoint_a083519.json) |
|---|---:|---:|
| Engine / plan | v2 / p2, accepted by v3 | v3 / p2 |
| Current filter | 20 | 19 |
| Wheel | primes through 59 except 41 | primes through 53 |
| W | 46896593906200308270 | 32589158477190044730 |
| j | 11 | 41 |
| u / launches per segment | 209513 / 5392200 | 49396 / 1774080 |
| Saved boundary jW | 515862532968203390970 | 1336155497564791833930 |
| k_start=previous term+1 | 517222792129337171164 | 1352093682658200396076 |
| cover_x | 0 | 0 |
| Pending records / maximum run | 205756 / 16 | 16308 / 15 |

Snapshot anchors are lines 2–38 of each checkpoint. Each saved boundary
is below its k_start, so neither proves a newly empty contiguous interval
above the last term. Partial u values, about 3.89% and 2.78%, describe
stripes across the whole segment, not numerical prefixes. No saved
pending record is a full run: there is no already classified new term
hidden in these buffers.

This interpretation follows `state`, `swept_k` and the closed-segment
loop in launch lines 896–938, 982–998 and 1454–1472. The class 3 modulo
6 is a theorem and already used. Sieve exclusions are only valid above
the prime-equals-value exception floor; retain `k_floor` and independent
prefix handling in [plus2_search.py](../plus2_search.py), lines 127–138.

The current rates need two different evidence labels:

- **A083518:** 4.1e16 term-units/s was the actual v2 campaign rate.
  **4.63e16** was measured on the actual n20 prefix with v3, paired against
  v2 on the same plan and launches. This is the appropriate stored v3
  baseline here, not the stand-in n20 row.
- **A083519:** **9.7e16** was the actual n19 v3 campaign rate. The
  **1.45e17** v3 benchmark row was on a stand-in prefix. Its approximately
  1.5× higher rate cannot be promised at the real prefix. The history
  records an unresolved campaign/stand-in gap, with ambient desktop use
  and plan differences not disentangled.

Sources: [BENCHMARKS.md](../BENCHMARKS.md), “Engine v3 against v2” and
“The campaigns against these prices”;
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), lines 699–745 and 828–856.
All are historical measurements, not timings made in this review.

### Mean cost, median location, and confirmed least term differ

RESULTS lines 216–227 records the actual-prefix medians 1.17e22 and
4.81e22, and expected confirmation work 2.58e22 and 9.42e22. Its
6.4/11.3-day figures are **expected confirmation costs**, not travel
times to the medians. Some README prose describes them as median costs;
the explicit RESULTS definition is the one used here.

| Quantity from stored values | A083518 at 4.63e16 | A083519 at 9.7e16 |
|---|---:|---:|
| Raw travel from last term to model median | about 2.80 days | about 5.58 days |
| One full 160-period segment | 45.0 hours | 14.9 hours |
| Remaining work to first closure from saved u | **43.3 hours** | **14.5 hours** |
| Segments needed to reach the rounded median | 2 | 9 |
| Remaining clock to close through that median | about 3.68 days | about 5.58 days |
| Expected confirmation work / rate, from the original floor | about 6.45 days | about 11.24 days |

Arithmetic uses S=160W, f=u/L, and `(m-f)*S/rate` for m complete
segments. Median travel uses `(median-last term)/rate`. These calculations
assume constant historical throughput and exclude startup, verification
and replanning time. The final row has not been reconditioned on the
partial observations; it reproduces the original stored expected cost.
No new model integration was performed.

After one additional day at these rates, A083518 closes **zero** segments.
A083519 closes **one**, reaching the exclusive boundary
6550420853915198990730; its second segment does not close within the day.
Thus the stored “P(found) in a day” figures of 25% and 16% cannot simply
be read as chances of a **confirmed least term** in that day under the
saved execution plan. In particular, A083518 has no such first-closure
opportunity at the baseline rate. No corrected probability is invented
here; any future probability must be evaluated at a completed boundary.

<a id="ptc-001"></a>
## PTC-001 — optimize completed coverage at the one-day deadline

**Status: proved objective correction and arithmetic thresholds;
destination performance unmeasured.**

`plan`, [plus2_gpu.py](../plus2_gpu.py), lines 674–711, minimizes the
model's **expected** clock to a confirmed find. It calls `expected_sweep`
at line 701 and trades longer segments against throughput. That is a
reasonable long-hunt objective, but it is not the user's fixed deadline.

For a fixed real prefix, let B_P(T) be the fully justified numerical
coverage boundary under plan P at time T. The event that the least term
lies below B is monotone in B under any distribution. Therefore,
for a fixed one-day budget, choose the plan with the largest credible
**completed B_P(24h)**, accounting for startup, discarded partial work,
verification allowance and the cost of migration. This observation needs
no fresh Bateman–Horn computation. It does not authorize promoting u's
fractional progress to a numerical boundary.

For A083518, keeping its wheel but starting a fresh h-period segment at
j=11 gives these exact rate thresholds to close once in 86400 seconds:

| h | Minimum term-units/s | Fraction of the recorded 160-period v3 rate | First completed exclusive boundary |
|---|---:|---:|---:|
| 32 | 1.737e16 | 0.375 | 2016553537966613255610 |
| 64 | 3.474e16 | 0.750 | 3517244542965023120250 |
| 96 | 5.211e16 | 1.125 | 5017935547963432984890 |
| 128 | 6.948e16 | 1.501 | 6518626552961842849530 |
| 160 | 8.685e16 | 1.876 | 8019317557960252714170 |

The formula is hW/86400. These conservative thresholds restart the short
segment rather than assuming that the old partial cursor is reusable.
Preserving the present 160-period cursor would still need about **1.80×**
the recorded rate just to close its first segment in a day. That is not
the factor needed to reach a median, which is a separate target.

The inherited `CREL_WIDTH` values at GPU line 638 give
R32/R160=0.70/1.115 and R64/R160=0.84/1.115. If those old ratios happened
to hold at the actual v3 prefix, fresh closure times would be about
**14.3 hours** and **23.9 hours**. They are illustrative scenarios,
not measurements. The 64-period case has virtually no margin for startup,
rate variation or verification. The 32-period case covers less numerical
line and may reduce expected long-run efficiency; its value is that it
can plausibly deliver one completed interval within the deadline.

The project already measured that the width curve is stale on v3:
OPTIMIZATION_LOG lines 767–780 records 128 periods at 0.920 of the
160-period candidate rate, and 224 periods up to 1.067. The 224-period
plan nearly tied on **expected** clock while lengthening a segment 40%.
That old rejection is consistent with the history; it does not answer
the different one-day objective. No actual-prefix v3 32/64-period
measurement was found.

### Two implementations have different coverage and cost requirements

**A fresh PB32/PB64 plan:** rebuild at the real prefix and use a distinct
enumeration fingerprint. Changing PB can change first-level chunk sizes
and the meaning of u (GPU lines 2731–2779). Conservatively reset partial
work and reconcile/drop old pending records together with their
uncommitted survivor accounting. Preserve all committed finds, evidence
and census. The current load path resets u when segment units differ
but retains pending (launch lines 727–746 and 971); copying that behavior
unchanged can duplicate classification and census on replay.

**A restricted prefix of the existing PB160 job:** with the same wheel,
depth and exact launch decomposition, every previously completed launch
covered every one of the 160 periods. It therefore already covered the
first h periods. Completing `sweep(j,j+h,u_from=old_u)` can preserve that
work, provided old pending records are partitioned at H=(j+h)W and only
records below H are considered for this closure. Later records cannot
be announced as least terms. Persist the active endpoint h/H: otherwise
a crash followed by an ordinary 160-period resume would skip unswept
suffix work from launches that were completed only on the short prefix.

The latter route is supported mathematically by the loop structure at
GPU lines 3815–3848, but **does not automatically get PB32/PB64 speed**:
the PB160 pattern work can remain. The existing `seg_cap` merely caps the
number of windows batched; at GPU lines 2769–2770 its minimum is one.
Setting `seg_cap=32` on a 160-period window does not create a 32-period
segment. Cost and coverage need to be tested as the actual implementation,
not inferred from the parameter name.

For A083519, the existing plan already has a one-day closure opportunity.
A deadline-aware comparison may still improve its completed boundary, but
the actual-prefix 9.7e16 campaign rate must be the baseline. Substituting
the 1.45e17 stand-in rate would claim unmeasured additional coverage.

<a id="ptc-002"></a>
## PTC-002 — bound the singular-series tail without factoring the prefix

**Status: proved model assurance; no additional sieve pruning.**

The model truncates its product at Q=200000 (`QMAX`, model line 69;
`log_singular`, [plus2_model.py](../plus2_model.py), lines 153–174).
Unlike consecutive multipliers, the enormous clique terms may have
prime divisors or collide modulo primes beyond Q. A blanket assertion
that every larger q has 19 distinct roots would be wrong.

Let a_1<...<a_c be the real positive prefix, with c=19 for both current
filters, and define the nonzero integer

`D = (product_i a_i) * product_(i<j) (a_j-a_i)`.

For odd q, a coefficient divisible by q contributes no root to a_i*x+2.
The number of such missing roots is at most the q-adic valuation of
`product a_i`. Among the other coefficients, inversion and scaling by
-2 are bijections; a residue class of k equal coefficients loses k-1
distinct roots, at most the number k(k-1)/2 of colliding pairs.
Each pair contributes to the valuation of its difference. Consequently
`c-w_q <= v_q(D)`.

Write `A_q=(1-w_q/q)/(1-1/q)^c` and
`G_q=(1-c/q)/(1-1/q)^c`. For q>Q>c,

`0 <= log(A_q/G_q)
    = log(1+(c-w_q)/(q-c))
    <= v_q(D)/(q-c)`.

Since `sum_(q>Q) v_q(D)*log q <= log D`, the positive correction is at most
`log D/((Q-c)*log Q)`. The generic negative tail has

`log G_q = -sum_(r>=2) (c^r-c)/(r*q^r)`,

so the same integer-series bound used for consecutive forms gives
`sum_(q>Q) log G_q >= -c^2/(2*(Q-c))`. Combining the two,

`-c^2/(2*(Q-c)) <= log(S_infinity/S_Q)
                 <= log D/((Q-c)*log Q)`.

No factorization or numerical model integration is required. Every factor
of D is at most a_c, so `log D <= c(c+1)/2 * log a_c`.
At the two saved prefixes the resulting log upper bounds are approximately
0.003713 and 0.003788; the common lower bound is -0.000902586.
Thus the normalization error is bounded within approximately
**-0.091% to +0.380%**. This is a conservative bound, not a measured error.

The model's much larger uncertainty is its first-event heuristic and the
unknown coefficients beyond the next term. `model_results.json` is the
pre-run historical forecast with stand-ins, not the current conditional
forecast. RESULTS lines 114–145 rescored the actual finds: 14 draws with
E sum 13.15, mean 0.94, and substantial individual scatter. That is limited
support for the intensity scale, not a guarantee of any next location.
The report's current medians come from RESULTS, not a rerun model.

<a id="ptc-003"></a>
## PTC-003 — a complete proof that no prime above 3 is forced

**Status: proof assurance for an existing claim, not a new restriction.**

For any prime q>=5, a valid positive clique prefix cannot contain both
residue classes 2 and -1 modulo q. Representatives a>=2 and b>=q-1
would be distinct and satisfy
`a*b+2 >= 2*(q-1)+2 = 2q`,
while q divides a*b+2. The pair value would be composite, contradicting
the prefix definition. In particular, there is no “value equals q”
exception to this argument.

The involution f(r)=-2/r exchanges 2 and -1. If one of those coefficient
classes is absent, its image under f is a nonzero candidate class that
no prefix form kills. Candidate class 0 also survives every odd q.
Therefore every q>=5 leaves **at least two** candidate classes and can
never become forced, at any future valid prefix.

At q=3 the classes 2 and -1 coincide, so the proof deliberately does not
apply. The existing seed terms force x=0 mod3; parity forces x=1 mod2.
Together these give x=3 mod6. The mod5 allowed sets are already preserved
by the seed and its closure: {0,2,3} for A083518 and {0,4} for A083519.

The reference docstring at lines 82–93 makes the global no-further-forcing
claim using involution pairs and exceptions, while G2d at lines 632–673
checks existing indices and bounded primes. The argument above supplies
a short all-prime proof without needing to bound exceptional pairs.
It explains why the complete forced unit stays 6 and why the linear
project's “extract more forced primes” opportunity does not transfer.

Do **not** use the exhibited surviving class as the only candidate class:
it is an existence witness, not a classification of all survivors.
Current exact killed sets already remove every small-prime obstruction.
Admissibility is not a proof that these greedy sequences are infinite.

<a id="ptc-004"></a>
## PTC-004 — completed-segment suffix reuse is sound, already known

**Status: deferred; refine the existing proposal rather than claim novelty.**

OPTIMIZATION_LOG lines 513–518 already states this theorem, prices the
projected saving at about 22 minutes of a later A083518 search (0.2%),
and declines it. The present source's stronger wording that the old
filter says “nothing” about the suffix is nevertheless mathematically
misleading (`follow_frontier`, launch lines 1170–1204).

Let an old segment [L,H) be completely classified under prefix P, and
let x be its first independently verified full hit. Every eligible
next term y in (x,H) must satisfy all old forms plus the new form x*y+2.
It therefore lies among the old **full-run records**, not among all
integers. Old candidates rejected by a sieve factor or failed strong
test remain excluded under the larger prefix.

Keep the sorted old full-run suffix, test x*y+2, and independently verify
and certify a surviving least y against the entire enlarged prefix.
Append y and repeat if needed. If the suffix is exhausted, H becomes
a justified bound for the final enlarged prefix. This is an induction
on added terms; it does not require a fresh GPU sweep of the entire
old segment. Existing pending records already contain every full run,
so retaining all pre-primality-test survivors is unnecessary.

This construction requires a **closed** old segment, atomic prefix/cache/
coverage provenance and crash-safe replay. An unproved probable hit
cannot be used as an accepted new coefficient. Changed sieve depths may
alter the censored census: preserving discovery coverage does not imply
reproducing the new filter's census. Keep old-filter provenance or reconcile
counts separately and count each committed event once.

The present loop breaks at the first discovery and clears pending
(launch lines 1462–1470), so this is unimplemented. It cannot accelerate
the first closure or first discovery at either current frontier, and
neither checkpoint currently contains a full-run candidate. Its published
0.2% estimate was on projected filters, not a new price on today's
actual next prefix, which does not yet exist.

Mid-find truncation is also already priced separately: OPTIMIZATION_LOG
lines 502–512 and 781–782 estimate about 3–3.5% at day filters. PTC-001's
fixed deadline and initially shorter completed prefix should not be
confused with that existing expected-time proposal.

## Disposition and future implementation handoff

No larger modular forcing, cross-family affine equivalence, self-primality
condition or term rescaling supplies a proved new search reduction.
The two greedy prefixes diverge, and replacing either with the other's
conditions would change its least-term definition. The fixed modulo-5
classes, subset wheels, period-window sieve, wide records, periodic
small-prime windows, folded rounds and generated first tail rounds are
already implemented. Generic recommendations to add them would count
historical gains again.

The source already rejects nonsquarefree explicit units
(`assert_unit`, search lines 231–265). Its period decoding also supports
the non-power-of-two PB160 shape. The corresponding issues found in some
other projects are not present here and should not be transplanted as
findings. The remaining kernel ideas in the optimization history are
mostly small phase costs, not evidence of an order-of-magnitude gain.

A future Claude implementation should first make the current prefixes
available with their evidence provenance, while preserving original
literature separately and the independent oracle. Add current n20/n19
frozen workloads: [score.py](../score.py), `SHAPES` at lines 104–120,
still pins the original n14/n11 openings and older anchors.

For PTC-001, validate actual shorter-prefix coverage against the dense
CPU sieve on equal absolute intervals, both families, x=3 mod6, high
bases, the exception floor and both interrupted-resume paths. Retain the
independent oracle and independently constructed CPU checks. A changed
PB, active endpoint, wheel decomposition or candidate ordering requires
a complete enumeration fingerprint; matching segment length and number
of launches alone is insufficient for an arbitrary changed stream.

Validate pending partitioning, committed versus uncommitted statistics,
least-claim boundaries, certification failure, and promotion before
measuring. Preserve existing fingerprints; any intentionally changed
workload needs a new independently justified fingerprint. Then compare
**completed boundary within 24 hours**, including startup and confirmation,
as well as ordinary end-to-end rate and expected clock. This report
performs none of those executions and authorizes no campaign start.

## Source snapshot

Read on 2026-10-20 at Git HEAD
`f8fdb200c56a54aa5e207c146882f7d2d7b87224`. The workspace was already dirty;
these SHA-256 values pin the inspected working files. Source line numbers
refer to this snapshot. The project README navigation was edited
separately by the coordinating reviewer and is not hashed here.

| File | SHA-256 |
|---|---|
| plus2_reference.py | `b8cbb2e2d7ee2c6b344fa4525f8e74ed5826f89cc7df80c5b7db2ead6a5fc274` |
| plus2_search.py | `1dce6fd0e1cef222097229552f4483b5b72482cb2035823804c6a111d5ee0618` |
| plus2_gpu.py | `82d0fdd9995cdf6bd1eeb4385ef281e361446a92ba31d57dd67c0621c593ce10` |
| launch.py | `dd7c99fa435e7d7d93cceadaef542daa51c9bb0e5a306913de18c614fdb72d1b` |
| score.py | `c4119bb0277658da72ee5cb29e04073b05630ac8ebdb8af2331f28c595712997` |
| plus2_model.py | `8bb64a730a56e4a47e74f1a749febf122d62ebf0e42e3898f6e8c6f0cf22d747` |
| model_results.json | `bc1cbd4a39222fd1d6ed2ff6ac5ff988aef0144dc142536d6ac8e14a9a7ca3b8` |
| OPTIMIZATION_LOG.md | `744dfeefb96d5b764f1e7c1e8f84e2135f7308a23b8b0a6a6fa194ce75bcb036` |
| RESULTS.md | `f67d81fd8b24a5dd5ab9f9f804ff317c57bd6cdf8a18a77ae1d9a754ba8e5db4` |
| BENCHMARKS.md | `d3f75282d4c241f0364ad53a7c77bf557211ab931460b96f3f56194e97f3fc92` |
| campaign_checkpoint_a083518.json | `93d394186c08eda696a0cc9be6179990de7fe89fe73c74cbbdd5339a4822c758` |
| campaign_checkpoint_a083519.json | `5be987df6db95960463728cb1dea7d662e20ff3d805484e11c835a67ed2166dd` |

Only this report and its review index were authored by this reviewer.
The hunt implementation, model outputs, evidence and checkpoints were unchanged.
