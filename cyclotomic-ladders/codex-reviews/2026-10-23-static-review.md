# Cyclotomic-ladders: static mathematical review

> **Authorship:** Codex (OpenAI), 2026-10-23, at the repository owner's
> request. The implementation and its historical records retain their
> Claude attribution. This report contains analysis and proposals for
> Claude, not implementations, measurements, verification results, or
> newly discovered sequence terms.

| Snapshot item | Recorded state |
|---|---|
| Repository HEAD | 35f48897eac28a5ec0ac4f60c3ce2e3a92d8708c |
| Initial working tree | Root README.md modified; cyclotomic-ladders/ entirely untracked |
| Snapshot qualification | The revision does not contain this project's source; SHA256 hashes below identify the actual reviewed files |
| Families | A070737, A072942, and the proposed A233512 rider |
| Method | Static source, documentation, stored data, primary sequence definitions, proofs, and lightweight arithmetic |
| Execution | No project imports or execution, searches, primality experiments, tests, benchmarks, profiling, CUDA compilation, GPU queries, or campaign actions |
| Deliverables | This report, the [Claude validation plan](2026-10-23-validation-plan.md), and [finding ledger](README.md); documentation navigation updates |
| Governing workflow | [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md) |

## Assessment

The useful new work is specific to cyclotomic mathematics: carry lower
bounds through the divisibility order on A072942; express its forbidden
residues as a single subgroup; exploit negation symmetry for every current
even-index target; and attempt certificates from already proved factors
before doing optional factorization. In particular, the n = 78 search
already has enough in-run factors to attempt proofs of Phi_13 and Phi_26
without factoring Phi_4 or Phi_12.

None of these results establishes a runtime gain. The source already
contains the modern window sieve, generated tail rounds, separate period
and offset records, and device Fermat stages. Recommending those mechanisms
as new transfers would repeat work already done. The shared 60/90 sieve
suggested in the optimization log has much less overlapping class-space
work than its eight common forms initially suggest.

Before optimization acceptance or the owner's first campaign, address
proof settlement, the strictly increasing rider, and capped pending runs.
These have direct first-occurrence consequences. No historical missed or
false term is demonstrated: this snapshot has no campaign discoveries or
checkpoint data.

| ID | Priority / disposition | Main conclusion |
|---|---|---|
| [CYL-001](#cyl-001-divisor-floors-and-inherited-coverage) | P2 / Proposed | Proven inclusive floors and completed no-hit intervals transfer along divisor-set inclusion |
| [CYL-002](#cyl-002-subgroup-roots-and-paired-residue-tables) | P2 / Proposed | A072942 roots have count gcd(n,q-1); even-index roots admit exact paired lookup |
| [CYL-003](#cyl-003-try-known-factors-before-optional-factorization) | P2 / Proposed | Attempt Phi_13/Phi_26 certificates from in-run factors first; reuse factor and proof work |
| [CYL-004](#cyl-004-proof-failure-must-not-settle-an-index) | P1 / Proposed | Unresolved certificates must hold settlement and leastness; the ceiling claim needs stronger evidence |
| [CYL-005](#cyl-005-a233512-needs-its-own-strict-floor) | P1 / Proposed | Known agreement with A070737 does not justify automatic future plateau riders |
| [CYL-006](#cyl-006-preserve-per-index-identity-and-requested-scope) | P1 / Proposed | Equal-x discoveries must coexist in the ledger; an explicit index must retain its scope |
| [CYL-007](#cyl-007-capped-runs-and-coverage-migration) | P1 / Proposed | A cap hit is unresolved, not an exact run; replay must reconcile partial accounting |
| [CYL-008](#cyl-008-freeze-the-workload-before-comparing-speed) | P1 / Proposed | The first baseline must pin the actual workload as well as count/xor |
| [CYL-009](#cyl-009-condition-the-model-and-qualify-its-calibration) | P2 / Proposed | Correct the interpretation of pooled calibration, model tails, floors, and cost estimates |
| [CYL-010](#cyl-010-price-shared-divisor-searches-before-building-them) | P3 / Deferred | Common forms alone do not establish a useful shared 60/90 search |

Evidence labels used below follow the repository workflow: **Proved** is
an implication within stated assumptions; **Observed in source/data** is
not execution confirmation; **Previously measured here** refers only to
an existing record; **Unmeasured hypothesis** is a proposed benefit;
**Model-derived estimate** is planning arithmetic, never a guarantee.

## Current mathematics and search state

A070737 minimizes x subject to primality of Phi_k(x) for k = 1 through n.
Its solution sets nest, and its terms may plateau. Its published frontier
is a(10) = 13,533,264,289,711,320; the configured first open filter is 11.
A072942 minimizes x subject to primality of Phi(d,x) for every divisor d
of n. Consecutive indices need not be related, but divisibility does relate
them. Both have x >= 3 because Phi_1(2) = 1. The definitions and published
tables agree with the retrieved primary pages
[A070737](https://oeis.org/A070737) and
[A072942](https://oeis.org/A072942).

The scheduled A072942 order is 66, 78, 88, 48, 80, 60, 72, 84, 96, 90
([TARGETS](../cyclotomic_reference.py#L210)). These are independent
per-index cursors, currently initialized at 3. The ten gaps are taken from
the frozen a-file transcription in [FAMILIES](../cyclotomic_reference.py#L144).
The OEIS page links that a-file, but it was not retrievable through the
review's web tool; its full transcription was not freshly authenticated.
Reading the stored terms is not a new verification of their leastness.

[A233512](https://oeis.org/A233512) is a different recurrence: the next
argument must be strictly larger than the preceding argument. The page's
Mathematica program advances the argument after each appended term. Its
initial 3, 4, 6, 150, 1,068,630, 6,770,610 bridge to the known strictly
increasing portion of A070737, but that does not prove permanent agreement.

| Component | Observed in this snapshot |
|---|---|
| Oracle | Direct SymPy polynomial values/primality; independent residue walk and roots-of-unity construction |
| CPU engine | Dense x or forced-class line; primitive-root order construction and ordinary integer modular arithmetic |
| GPU engine | Subset CRT wheel to 89, up to three levels; bit windows, compaction, generated tails, then six device Fermat forms |
| Campaign sieve depth | PRP_Q2 = 8192, distinct from the CPU default 65536 |
| Window budgets | WINDOW_TABLE_BYTES = 20 KiB; pairs-table budget PAT_BYTES_MAX = 16 KiB |
| Candidate representation | x = unit times class-space coordinate, r0 = 0; host big-integer base with device offsets and separate period where needed |
| Exception zone | The sieve refuses x <= q2+1; the host prefix path covers small values at each relevant filter |
| Forced unit | Product of primes q <= n+1 for A070737; product of primes with q-1 dividing n for A072942 |
| Configured ceilings | x < 10^40; root-list bound 128 gives A070737 n <= 20 and an advertised A072942 list bound n <= 128 |
| Project-produced coverage | None: no campaign checkpoint files and no files in evidence/ at review time |
| Findings | FOUND is empty; no project discovery is being reverified here |
| Performance baseline | FROZEN is empty; all eleven score shapes lack expected count/xor |

Sources: [CPU bounds and representation](../cyclotomic_search.py#L94),
[planner](../cyclotomic_gpu.py#L725),
[GPU construction](../cyclotomic_gpu.py#L3054),
[prefix and campaign logic](../launch.py#L636), and
[score shapes](../score.py#L100).

The deterministic MR boundary applies to each polynomial value, not x.
The stored model gives crossing x = 284 at A070737 n = 11; README and
launcher prose say 258. Lightweight exact arithmetic confirms
Phi_11(283) = 3,306,752,438,254,122,446,702,213 below the shared bound
3,317,044,064,679,887,385,961,981, and Phi_11(284) =
3,425,431,640,760,499,512,446,701 above it. No primality test was involved.
All other forms through 11 have smaller degree, so this identifies the
crossing for that filter. The opening frontier is far beyond it.

The [round-0 log](../OPTIMIZATION_LOG.md) records compilation/layout
observations and one A070737 n = 11 pool-sizing sample: 12,100 host
survivors/s at 323 microseconds each, or about 3.91 core-seconds per
second. It does not provide a full scored or paired optimization baseline.
Its descriptions of every constant as inherited hypotheses remain relevant.

## CYL-001: divisor floors and inherited coverage

**Priority P2; Proposed. New reduction. Proved set inclusion; runtime
benefit unmeasured and currently likely small.**

If d divides n, every divisor of d is a divisor of n. Therefore every
A072942 solution at n is a solution at d, and a(n) >= a(d). This is an
exact implication including the small-value zone; it does not assume that
a divisible polynomial value is composite. The floor is **inclusive**:
plateaus are possible. Set

    L(n) = max of known a(d), over proper divisors d of n.

The stored table yields the following bounds without a search:

| Open n | Witness d | Inclusive L(n) |
|---:|---:|---:|
| 48 | 24 | 1,035,844,571,580 |
| 60 | 30 | 81,206,805,256,038 |
| 66 | 22 | 1,793,172 |
| 72 | 36 | 24,380,304,369,772,260 |
| 78 | 39 | 21,962 |
| 80 | 40 | 16,066,737,508,140 |
| 84 | 42 | 143,657,627,809,878 |
| 88 | 44 | 36,352,614,120 |
| 90 | 30 | 81,206,805,256,038 |
| 96 | 24 | 1,035,844,571,580 |

The next confirmed a(48) also bounds a(96). More generally, a completed
interval certified to contain no solutions for d contains no solutions
for n whenever d divides n. An unfinished fraction of a wheel period
does not provide a contiguous interval. An unresolved proof candidate in
that interval also prevents a no-solution claim.

There is a cross-family relation: if lcm(1,...,r) divides n, an A072942
solution at n satisfies the first r A070737 conditions. Thus its least x
is at least A070737 a(r). Conversely, an A070737 solution through r
satisfies A072942 at every index n <= r, providing an upper bound there.
For today's targets the displayed proper-divisor floors dominate the
applicable published initial-ladder floors. Do not add them as independent
speed factors.

The current [reference floor](../cyclotomic_reference.py#L391),
[launcher x_floor](../launch.py#L158), and
[model floor_for/plan_floor](../cyclotomic_model.py#L188) return 3 for
every divisor index. Implement a provenance-bearing floor service outside
the definition oracle, consume it in the campaign and model, and record
the supporting least terms or completed interval in evidence. The oracle
must still evaluate the original definition, including small x.

**Price.** Against the stored median depths, the largest static fraction
removed is about 1.54e-6 for n = 48, then 6.81e-7 for n = 88. All other
fractions are smaller. These are line-distance fractions, not measured
time gains. The chief immediate benefits are correct reuse and removal of
unnecessary startup prefix work; segment rounding may erase any clock
saving. Future inherited coverage may be more valuable.

**Acceptance.** Exercise equal-term divisors such as a(2) = a(4) = 4;
reject a floor of a(d)+1. Compare eligible solutions below/at/above the
floor with the independent oracle; preserve explicit canary rediscovery
windows even when the optimized production floor passes them. Do not
pretend that skipped ranges contribute observed census counts. When a
wheel changes, start from a floored whole-period boundary and clip at the
proven numerical floor, with no gap or duplicate committed accounting.

## CYL-002: subgroup roots and paired residue tables

**Priority P2; Proposed. New exact representation. No new candidate
exclusion and no measured speedup.**

The factorization

    x^n - 1 = product of Phi(d,x) over d dividing n

implies, over the field modulo any prime q,

    some required Phi(d,x) is 0  <=>  x^n = 1.

The nonzero residues form a cyclic group of size q-1. With
g = gcd(n,q-1), the killed set is the unique subgroup of size g, and

    w(q,n) = g;
    K(q,n) = {h^j : 0 <= j < g},  h = primitive_root(q)^((q-1)/g).

This remains true when q divides n; repeated algebraic factors do not
change the set of roots. Residue 0 survives. It independently recovers
the existing forcing theorem: all nonzero residues die exactly when
q-1 divides n. For A070737, the existing reduced-order union remains
necessary; a single gcd does not describe its initial interval of indices.

The current [_orders/_xkills/w_fast](../cyclotomic_search.py#L231) loops
over each attained order and its coprime exponents. A divisor-family
specialization can compute the count by one gcd and generate the subgroup
with one exponentiation followed by g-1 modular multiplications. This
primarily removes construction/model work, not steady-state sieve tests.
Keep the original-definition oracle and its polynomial residue walk
independent of this specialization.

### Negation symmetry gives a stronger device experiment

Every current A072942 target is even. For odd q, n even implies
(-x)^n = x^n, so K = -K. Scaling into the class x = unit*t preserves
this symmetry because r0 = 0 and q does not divide unit. Primes dividing
unit are already excluded from the tail. Consequently membership can be
tested using the canonical representative

    c = min(r, q-r),  0 <= r < q,

with one table entry per pair. No nonzero residue is self-paired at odd q.
This halves the number of distinct root representatives exactly; the
allocated list is padded to a multiple of 16 with a minimum of 16, so its
allocation need not halve. It does not halve the candidate stream or
justify identifying positive x values with negative ones.

At PRP_Q2 = 8192 every held odd prime is below 8192, so c <= 4095. The
existing 4096-bit mask can therefore become **exact for every held prime**
in this specialized path. The current [TEST macro](../cyclotomic_gpu.py#L2595)
uses an exact mask only below 4096 and otherwise scans a padded root list
on a mask hit. The [mask/list builder](../cyclotomic_gpu.py#L3305) is the
matching construction point. Fold after the full candidate remainder,
including its period/base contribution, has been reduced; folding the
offset alone is invalid.

**Scope matters.** Most earlier tail rounds may already use the generated
exact tables over [0,2q), built by [_tail_tables](../cyclotomic_gpu.py#L4439).
They do not perform the generic list scan. The constructor deliberately
leaves the final round generic ([tail_lit selection](../cyclotomic_gpu.py#L3730));
overflow fallbacks also use generic testing. The first experiment targets
those paths, whose cost share is unknown here. Extending pairing to the
generated lazy tables could reduce about 2q bits to about q/2 bits, but
requires a canonical correction and folding arithmetic. That is a
separate memory-versus-instruction experiment, not another automatic gain.

A direct subgroup-power test is another exact alternative: in class space
test (unit*t)^g = 1 modulo q, or t^g = unit^(-g). A binary chain needs at
most floor(log2 g)+popcount(g)-1 modular multiplications. For g <= 96 this
is a small bounded chain, but even several reductions can cost more than
a cached mask; treat it as a lower-priority comparison for deep, large-g
tails rather than an assumed winner.

**Bounds and tests.** Guard the even-index, odd-prime, zero-affine-class
assumptions. Test r = 0, 1, q-1, both sides of q/2, q near 4096 and 8192,
larger sieve depths, all current target units, narrow/wide records, and
forced overflow paths. Compare raw survivors exactly. Do not fold the
translated bit-window phase without a separate derivation. Do not extend
the advertised index range merely because paired lists fit: the device
Fermat reconstruction takes a uint32 unit
([enqueue](../cyclotomic_gpu.py#L4400)). Wider range support needs that
scalar, coefficient restrictions, limb counts and every record bound
checked, not only the root-list length. No current-target unit overflow
is established by this review.

## CYL-003: try known factors before optional factorization

**Priority P2; Proposed. New shortcut resolving part of a documented open
idea. Algebraic sufficiency proved; successful bounded witness search and
runtime improvement remain to be tested.**

[certify_run](../launch.py#L476) builds all factors of each Phi_k(x)-1,
calling bounded factorization on out-of-run polynomial values before
calling certify_value. The round-0 log explicitly asks for a cheaper
certificate route at n = 66, 78, 88. For n = 78, two required forms already
have sufficient known factors:

    Phi_13(x)-1 = x Phi_2(x) Phi_3(x) Phi_4(x) Phi_6(x) Phi_12(x)
    Phi_26(x)-1 = x Phi_1(x) Phi_3(x) Phi_4(x) Phi_6(x) Phi_12(x).

The forms 1, 2, 3, 6 occur earlier in that divisor run. Once those values
and the prime factors of x are proved, choose

    F_plus  = x(x+1)(x^4+x^2+1),  for N = Phi_13(x);
    F_minus = x(x-1)(x^4+x^2+1),  for N = Phi_26(x);
    R       = Phi_4(x) Phi_12(x).

For F_plus, its square minus Phi_13 has positive coefficients at degrees
3 through 11, zero coefficients at degrees 2 and 12, and only -x-1
remaining below. It is positive for x >= 2. Thus F_plus > sqrt(N).
For x >= 3, F_minus >= (2/3)x^6, while Phi_26(x) < x^12, so
F_minus^3 > N. Every production n = 78 candidate is even, hence F is
even. For even x, R is coprime to either F: R is coprime to x; any common
factor with x+1 or x-1 divides 2; reduction against Phi_3 and Phi_6 also
leaves only possible factors of 2, while all four polynomial factors are
odd. An implementation should still check the exact gcd.

This meets the factor-size and coprimality hypotheses of the existing
BLS75 Theorem 1 route for Phi_13 and Theorem 5 route for Phi_26. It still
requires the witnesses, the Theorem 5 discriminant condition, proved
prime factors, and independent certificate verification implemented in
[certify_value](../launch.py#L427) and
[the shared verifier](../../huntlib/certificate.py#L623). Algebra alone
does not label an arbitrary candidate prime or guarantee that bounded
witness selection succeeds.

**Implementation sequence.** Gather already certified factors first;
try the appropriate theorem before factoring optional residual values;
only escalate on failure. Cache factorization and subproofs by exact
integer within the discovery transaction, including certified factors of
x. Return that factorization with the certificate bundle: currently
[record_discovery](../launch.py#L1050) factors x again after certify_run
already did so. Failed certificate attempts must follow CYL-004.

This resolves the specifically stated need to factor Phi_4/Phi_12 for
the Phi_13 route, and helps Phi_26 too. It does **not** establish an easy
route for every n = 78 form, nor for Phi_11/Phi_44 in n = 66 or 88.
The shared library already tries N+1/Lucas routes in suitable fallback
calls; simply proposing N+1 again is not a new algorithm. No sufficient
new algebraic N+1 route for those remaining hard forms was established.

**Acceptance.** Pin factor identities by independent polynomial
multiplication; verify certificates through the existing independent
checker; inject wrong factors and stripped subproofs. At successful
n = 78 cases, count optional factorization calls and require none for
Phi_4/Phi_12 when the early route succeeds. Measure complete discovery
proof time, not just one modular witness. Keep unresolved cases explicit
and do not weaken the oracle or substitute probable prime factors.

## CYL-004: proof failure must not settle an index

**Priority P1; Proposed. Observed source behavior and proof obligation.
This is a prerequisite, not a speed proposal.**

[record_discovery](../launch.py#L1042) receives unproved values, stores
certificates_verified = false, then nevertheless updates found, writes
ordinary discovery evidence, increments discoveries, and emits DISCOVERY
([commit path](../launch.py#L1089)). It explicitly says a find with
unresolved proofs stands on the three screening legs. [follow_frontier](../launch.py#L1120)
then closes a divisor index or promotes the ladder. The README's claim
that discovery values are proved before acceptance is stronger than this
control flow.

Above MR_VALID_BELOW, the MR and BPSW legs are probable-prime checks; the
alternate residue sieve does not supply a primality proof. A candidate
whose certificate failed remains unresolved. It must not become a proved
least term or supply a stronger certified floor for later searches.
This is especially relevant here because high-degree forms cross the
deterministic bound at very small x.

Introduce a durable pending-proof state and a leastness barrier before
mutating proved found, closed, promoted, or derived state. A later
solution cannot be called least while an earlier candidate is unresolved.
Ordinary compositeness rejections and work beyond the candidate can be
retained, but must not be reported as a proof that the whole interval is
empty. A fully proved initial ladder prefix may settle its own indices;
higher unresolved conditions remain pending.

The certificate ceiling claim also needs qualification. The source
describes x < 10^40 as measured for every project route. The mandatory
synthetic high-factor check in [_certificate_drill](../launch.py#L1694)
proves Phi_2 at a generated x; it does not force x close to 10^40. The
Phi_3/Phi_4 extensions may skip composite values or failed proofs, and
the high-degree open-family routes are not all mandatory successes.
The drill injects a large factor's subproof directly, whereas production
certify_run initially adds x's factors without building those subproofs.
The fallback may recover them, but the drill does not establish that path.
Treat representation coverage, tested certificate routes, and worst-case
factoring cost as separate statements.

**Acceptance.** Force one certificate failure after all screening legs
pass; require no settlement, ordinary discovery, derived rider, or
certified floor advancement whose claim requires that unproved condition.
A separately proved initial prefix may settle only its justified indices.
Restart, resolve the remaining proof, and commit once.
Exercise every used high-degree route at representative and ceiling
heights in a later authorized session, with failure branches mandatory.
If a stopper lacks a factor, retain a reproducible compositeness witness
and precise evidence labeling; a comment promising a failed MR base is
not the same as storing that base.

## CYL-005: A233512 needs its own strict floor

**Priority P1; Proposed. Proved counterexample to an inference, not a
claim that a future plateau actually occurs.**

Let A(n) denote A070737 and B(n) the strictly increasing recurrence in
A233512. Then B(n) is the least eligible x with x > B(n-1). If A(n) is
proved and A(n) > B(n-1), B(n) = A(n), because there is no smaller eligible
x at all. If A(n) <= B(n-1), that inference is unavailable.

The [G1d check](../cyclotomic_reference.py#L662) proves agreement of the
stored prefix and verifies strict increase only through the known n = 10.
It cannot prove strict increase for future A070737 terms. Yet
[also_settles](../launch.py#L528) assigns every settled n >= 5 to the rider.
If a new x settles A070737 a(11) and a(12) simultaneously, B(11) may equal
x, but B(12) must be strictly larger. The second automatic rider is false
under the documented recurrence. A233512 can later rejoin A070737 if the
strict-floor condition is re-established; neither permanent agreement
nor permanent divergence follows.

Track the proved rider prefix and its strict predecessor separately.
Emit only the riders justified by that recurrence and available leastness
evidence. A primary plateau must leave the remaining rider indices open,
or trigger separately authorized work over their actual intervals. Do
not relabel the derived sequence or silently change its definition.

**Acceptance.** Use synthetic primary plateaus and independently computed
small strictly increasing sequences. Require at most one same-x rider
within a newly settled plateau and verify a later rejoining case. A test
that merely expects every primary settles row in also_settles perpetuates
the incorrect inference.

## CYL-006: preserve per-index identity and requested scope

**Priority P1; Proposed. Observed source behavior. Two bounded per-index
correctness changes for the later implementation phase.**

A072942 uses one family ledger ([ledger_path](../launch.py#L243)), but
[evidence.record](../launch.py#L1091) keys its entries only by x. The
[shared upsert](../../huntlib/evidence.py#L51) removes every previous row
at that x. Distinct indices may have the same least x: the frozen table
already contains a(1) = a(3) = a(7) = 3 and a(2) = a(4) = a(8) = 4.
Nothing excludes a plateau between open divisor-related indices such
as 48 and 96. Separate evidence JSON files would survive, but the common
ledger would lose an earlier term.

Choose an identity containing the family and settled index, or merge
equal-x records with all index-specific conditions and proof provenance
preserved. Replaying one index must neither duplicate it nor remove
another. A shared-helper change affects other projects and needs an
explicit compatibility analysis; a project-local representation may be
the narrower implementation.

Separately, CLI help describes --index as selecting one open index, but
the [outer campaign loop](../launch.py#L2651) sets args.index to None
after that index closes and proceeds through TARGETS. Preserve whether
the operator explicitly selected an index, and exit after its completion
in that mode. This does not require starting a real campaign to test:
use controlled campaign doubles in the later implementation session.

**Acceptance.** Record two indices at the same x, replay both, and verify
both records and all OEIS indices survive. Interrupt between evidence,
ledger, and cursor commits. Exercise explicit-index completion, default
TARGETS progression, already-closed resumes, and stop-on-discovery
independently.

## CYL-007: capped runs and coverage migration

**Priority P1; Proposed. Observed control flow with a concrete loss
scenario; no historical loss demonstrated.**

[filter_forms/sprp_run](../launch.py#L545) read A070737 through n+6 and
return a bare length. A return at the cap means at least that length.
At segment completion, [pending values](../launch.py#L1417) are handled
in numerical order against the changing frontier. The first discovery
is reread through n_max, currently 20, but subsequent pending records
retain their old capped lengths.

Consider n = 11, cap = 17. The first pending candidate has true run 18
and is stored as 17; record_discovery expands it and advances the frontier
to 18. A later candidate with true run 19 is also stored as 17. handle
now classifies it as CENSUS and never rereads it. The pending list is
cleared, and follow_frontier carries the complete old segment to filter
19. The later first occurrence has been skipped. This scenario needs no
claim about the existence of particular numerical candidates: the
coverage implication used by the control flow is invalid for permitted
classification results.

Store tested depth and whether an actual composite stopper was found.
Resolve every cap-hit whose depth is insufficient for the new frontier
before frontier-dependent taxonomy or coverage carry. Alternatively
replay the unresolved suffix under a sufficient filter. Do not treat
raising RUN_AHEAD as a proof. The allegedly uncapped reread is also
bounded at 20. Current verify already MR-tests Phi_21 as the stopper and
fails closed if it passes; it does not accept an exact run of 20 without
checking that value. A clean terminal/cap policy is still needed, and
blindly building filter 21 after a genuine run of 20 is unsupported.

Future optimization migration has another trap. On changed segment or
launch decomposition, [Campaign.__init__](../launch.py#L720) resets u to
zero while [load](../launch.py#L907) has retained partial pending,
survivor and census state. Redoing the work while preserving those
partial counts can duplicate accounting. The current accepted predecessor
list is empty and no campaign exists, so this is a future adoption
requirement, not evidence of current checkpoint corruption.

**Acceptance.** Create same-segment candidate fixtures with true lengths
cap-1, cap, cap+1, and the supported maximum, marking only lengths at or
above the cap as capped; verify exact settled-index vectors against an
independent full classification. Test a PRP overstatement that makes the
oracle length smaller as a separate rejection case. Split
and resume every variant. Fingerprint enumeration by filter, ordered
wheel levels, unit/class, live periods, width, chunking, sieve and device
screen. Carry only committed numerical coverage; replay floored overlap
with duplicate suppression and reconciled partial accounting.

## CYL-008: freeze the workload before comparing speed

**Priority P1 for performance acceptance; Proposed. Known unfinished
baseline plus a new workload-definition issue.**

All eleven shapes are unfrozen ([SHAPES and FROZEN](../score.py#L100)).
No valid SCORE exists in the stored ledger. Establishing this baseline
belongs to Claude's later authorized runtime work; this review did not
run the first score or infer its results.

Freezing only count/xor is insufficient here. [_campaign_row](../score.py#L139)
resolves the wheel anew from the live planner, and
[resolved_shapes](../score.py#L206) derives j0 from the wheel and chooses
residues from the current nu and chunk count. A planner or launch-size
optimization can therefore change the represented workload itself.
Re-freezing that new output must not be presented as an engine speedup.
Also, [work_for](../score.py#L167) prices a partial residue slice as an
equivalent line using density; that is a work unit, not contiguous
certified campaign coverage.

Pin a complete resolved manifest: family/filter, exact height/absolute
interval or exact enumeration slice, ordered wheel levels, unit, q2,
window/live periods, device predicate, counts, checksum and independent
provenance. Keep a stable engine comparison separate from a planner
comparison over identical absolute intervals. Establish expectations
independently of the engine under test, using the dense CPU path where
feasible and independently enumerated decomposition for large sparse
workloads. Small-window parity alone does not independently establish a
large-window fingerprint copied from the GPU.

**Acceptance.** Freeze campaign rows and the three fixed anchors in their
actual source locations; FROZEN lookup currently applies only to campaign
rows. Run both public validation entry points later: score.main omits
launcher/standard campaign drills included by launch.selftest. Require
every shape and exit status zero; the printed headline SCORE occurs
before later shapes have all been checked. Publish new planner workloads
as additional versioned rows while preserving historical fingerprints.

## CYL-009: condition the model and qualify its calibration

**Priority P2; Proposed. Source/data facts and mathematical limitations;
no replacement numerical forecast is claimed.**

The model uses Bateman-Horn over the actual forms, exact local root
counts, and the logarithms of polynomial values. These are appropriate
ingredients. Its [pooled Gamma test](../cyclotomic_model.py#L315), however,
treats 54 transformed first arrivals as independent exponential draws.
The divisor families share forms and contain nested solution sets; the
ladder also nests. Independence has not been justified. Furthermore
[independent_knowns](../cyclotomic_model.py#L285) selects terms at least
10^4 but for A072942 computes intensity from 3. Even under a marginal
Poisson model, selection conditional on no arrival before 10^4 changes
the applicable transformed waiting time to the residual intensity after
that threshold. The quoted Gamma tail probability is an exploratory
diagnostic, not a calibrated acceptance probability.

Keep historical predictions. For future model work, state the selection
and dependence assumptions, use diagnostics not falsely labeled
independent, and condition forecasts on proven floors and completed
no-hit intervals from CYL-001. An inherited solution-free class changes
the conditioning information as well as the amount of work. Do not divide
an old median clock by a candidate reduction and call it a new conditional
median. If a primary term has an unresolved certificate, it is not a
proved conditioning floor.

### The singular-series tail is not a finite-collision linear tail

For q above all form indices, the root count is

    w(q,S) = sum of phi(k) for k in S with k dividing q-1.

For A072942 this equals gcd(n,q-1). It keeps varying in residue classes
at arbitrarily large q; there is no cutoff after which w equals the
number M of forms. For sufficiently large q, the log local factor is

    (M-w(q,S))/q + O((M^2+w(q,S)^2)/q^2).

Thus the generic O(M^2/Q) tail bound used in some linear-shift sibling
reviews cannot be transplanted. The first-order cancellation depends on
prime distribution in arithmetic progressions. Cutoff sensitivity is a
useful numerical diagnostic but not a rigorous error bound. A rigorous
acceleration/bound would require an arithmetic-progression or character
factorization with its own hypotheses and proof. That work is deferred
unless model sensitivity makes it valuable.

### Reconcile stored values and cost provenance

README forecast values do not exactly match model_results.json. The
stored n = 11 Q1 is 1.11905e19, versus 9.1e18 in prose; the stored
A070737 n = 13 median is 1.59160e25, versus 1.7e25. The model writer
predicts successive ladder indices from the same current frontier,
whereas plan_floor chains prior median estimates for later filters.
Those are distinct scenarios and should be labeled as such, not mixed.
The proof-crossing discrepancy was resolved arithmetically above.

The n = 60 density_to_59 of 1.12659e-7 becomes about 1.84687e-9 only
after including forced prime 61. State which density is used. The
[clock_weight](../cyclotomic_model.py#L229) ordering is median distance
times a proxy wheel density, not measured expected wall time. The
[planner](../cyclotomic_gpu.py#L725) also uses inherited width/record cost
coefficients and a model floor, cached by filter rather than by actual
new coverage. Reprice a future plan with measured end-to-end costs and
the current proven boundary, and version its assumptions and cursor
adoption. A changed ranking alone is not a correctness failure.

**Acceptance.** Reconcile each displayed forecast with its saved inputs
without overwriting historical predictions. Check all local counts by
independent polynomial evaluation on test primes; examine multiple
cutoffs and report uncertainty. Measure full-segment closure, host
classification and proof time before assigning clocks or reranking
targets. No reported model limitation by itself proves the engine misses
solutions.

## CYL-010: price shared divisor searches before building them

**Priority P3; Deferred. A known unfinished idea from the round-0 log,
with a new bound on its opportunity.**

The common form set for n = 60 and 90 is the divisor set of gcd(60,90) =
30: 1, 2, 3, 5, 6, 10, 15, 30. Applying only those common conditions
preserves both families' solutions, after which each branch must check
its additional forms. Intersecting the two full families would lose
solutions. The common sieve alone admits many more candidates.

Already at forced-class level,

    U30 = 14,322;
    U60/U30 = 3,965 = 5*13*61;
    U90/U30 = 19.

The ratios are coprime. In a complete period of the combined classes,
their intersection occupies 1/3983 of the union, and duplicated raw
class candidates are only 1/3984 of the summed separate stream counts.
These are exact class-space counts before further wheel/sieve filtering;
they do not bound the duplicate fraction among final survivors or a
possible kernel instruction saving. They do show why eight shared forms
are not evidence that half the search can be removed. Sweeping the
entire U30 line would instead greatly enlarge the generated stream.

First reuse metadata, subgroup counts, and immutable tables where keys
agree. A shared candidate pipeline is worth prototyping only after a
measured cost model accounts for the union of branch classes, differing
heights, each complete-segment boundary, classification, and proof work.
Retain independent branch tags, first-occurrence coverage, pending proofs,
census and evidence; finishing one index does not finish the other.
Prefer the exact 48-to-96 floor/coverage transfer before a combined
60/90 engine. Reject a shared engine that only wins by changing the
absolute workload or excluding one branch's admissible candidates.

## Work estimates and implementation order

There is no cyclotomic scored rate with which to turn the model into
honest elapsed-time forecasts. In particular, the donor candidate rate
in README is not a measured rate for these filters. The provisional
long-filter targets remain A070737 n = 13 and A072942 n = 60, 72, 84,
90, 96, with all openings checked for cliffs. Revisit that prioritization
after collecting the local baseline.

| Mechanism | What is established | What is not established |
|---|---|---|
| Divisor floors | Exact removal of intervals below known inclusive bounds | A useful total runtime gain; current fractions are tiny |
| Subgroup construction | One gcd for counts; one subgroup generator instead of order unions | Significance of setup/model time in the campaign |
| Paired residue representation | Half the roots; exact 4096-bit generic masks through the current 8192 depth | A twofold speedup or elimination of work in already generated tables |
| Known-factor-first proof | Sufficient F for two n = 78 forms, without optional Phi_4/Phi_12 factoring | A proof route for every form or every future candidate |
| Shared 60/90 stream | Common conditions and exact forced-class overlap arithmetic | A positive end-to-end gain |

For a numerical floor L, segment start B <= L, segment span S, and a
model target D > B, the leastness-confirming boundary is

    C = B + S * (floor((D-B)/S) + 1).

Segments are half-open: a candidate exactly at D = B+jS belongs to the
next segment, so the confirming boundary must be strictly greater than D.
Price actual work through C, plus classification, certificates and any
replayed overlap. Never count fractional residue progress as a fraction
of contiguous proven coverage. This is a fixed-depth cost scenario until
the model has been conditioned on the actual coverage and other known
exclusions.

Claude should first address CYL-004 through CYL-008, then establish the
baseline, then test CYL-003 and CYL-002 as separate bounded experiments.
CYL-001 is inexpensive correctness-preserving reuse with modest immediate
performance upside. CYL-009 accompanies any changed floor/planner;
CYL-010 remains deferred. The companion [validation plan](2026-10-23-validation-plan.md)
defines the experiments, acceptance and rejection criteria.

## Alternatives examined and unresolved questions

- **Additional single forced primes:** the existing theorem is complete.
  A070737 forces precisely q <= n+1; A072942 forces precisely q-1 dividing
  n, outside equality exceptions. Residue 0 survives every prime, so there
  is no local obstruction to all solutions. A stronger arbitrary unit
  would lose coverage; general multi-class wheels are already available.
- **Prime equality:** a modular zero is not composite when the value
  equals the sieve prime. Keep the independent prefix/exception zone.
  A valid inherited floor may discharge it through a separate proof.
- **Period windows, subset wheels, generated tails, wide records:**
  already implemented. The [donor round-7 log](../../power-ladders/OPTIMIZATION_LOG.md)
  documents filter-specific wins and losses, not transferrable ratios.
  Current local plain tables do not fit the pairs path; smaller windows
  or larger shared tables trade depth and occupancy and need local data.
- **Device form ordering:** testing a fixed set in a different order
  preserves that set's conjunction. Adding later forms can suppress
  shorter census runs. On A070737 and A072942 n = 60 the first six
  degrees are 1,1,2,2,4,2,
  so a cost-aware order can be tested, but the host must retain the
  original run order and the tested predicate must be fingerprinted.
  The device-depth/host-load sweep is already owed in round 0.
- **Global sign/reflection:** even-index modular symmetry is not a
  bijection between positive least terms at different indices. Do not
  prune positive x by half from it.
- **Factoring x^n-1 as a search:** the algebraic factorization explains
  the subgroup sieve, but factoring a degree-n integer for each x has
  no established advantage over testing its individual required forms.
- **All hard certificates solved:** not established. Phi_11/Phi_44
  routes and other high-degree values require measured bounded proof
  strategies; failure is an unresolved candidate, not permission to
  call it a proved first occurrence.
- **No local rejected optimizations:** the new project's log has no
  completed optimization rounds to reverse. Shared 60/90 work, proof
  routing, window layout and device-depth exploration were already
  identified there; the proofs and constraints above are the new input.

## Sources and execution record

Read the repository review/convention/optimization guidance; all five
public Python roles and the mathematical model; local README, RESULTS,
BENCHMARKS, OPTIMIZATION_LOG and model_results; relevant shared primality,
certificate, evidence, checkpoint and ceiling code; and applicable donor
optimization records and prior Codex reports. The review used three
complementary static reviewers for mathematics, engine algorithms, and
proof/coverage logic, reconciled into this report.

Primary web definitions consulted on 2026-10-23 were
[A070737](https://oeis.org/A070737),
[A072942](https://oeis.org/A072942), and
[A233512](https://oeis.org/A233512). The linked A072942 a-file was
unavailable through the retrieval tool; the embedded transcription is
identified as stored evidence rather than freshly verified content.
All new mathematical deductions are stated with their reasoning above.

Executed only read-only file/Git inspection, text searches, source hashing,
small arithmetic on recorded integers, and documentation writes/checks.
No project or shared-helper code was imported or executed. No tests,
benchmarks, primality trials, searches, models, GPU access, machine
settings, campaign state or evidence were changed. Documentation checks
do not constitute mathematical or runtime validation.

### Source and data hashes

SHA256 values pin the initial reviewed contents. README navigation and
the repository review index were subsequently updated as documentation;
their listed hashes describe the pre-review snapshot. Code and data
hashes were checked again after writing the reports.

| File | SHA256 |
|---|---|
| cyclotomic_reference.py | f844de2805262db9568d73120c4410c16f6a8d893473fdca1e7077df2675779c |
| cyclotomic_search.py | 3b9b2f1b42464ff89aa656cc8589f5021953bec8341c0547a6e201ce0348f3d2 |
| cyclotomic_gpu.py | 1356886c87c1b73d58f3a727bf8cf5f8ccfc009cf2f2ebe55d3f30e8a58812a3 |
| launch.py | cf713dab306c06ddf60345989553975c9875f06c76fae83b3eef80cc71e53041 |
| score.py | ab1440ed4284f671311e8e2c05b08d74c387f3a9d8a07185b322fbf19e41a7f5 |
| cyclotomic_model.py | 71e6d318235cabe9e813cc5fab25c6a0a4aa3e95c62936d4a5f84c3d06b3346d |
| model_results.json | 62b34b2102b3efcacdc6d2c6a2bc095037354a765db9add55c97eb085b05a204 |
| README.md (before navigation edit) | 3589a6e5a7edd9ca343ce987928937864bc9dee7d7892167f295e0dfa5e84861 |
| RESULTS.md | ae348b1741a3ad7cde6777f87d30227263c72f63baae502804ed10273ba97fc6 |
| BENCHMARKS.md | b1138106f055ecd5ba2e5b380ac00d2261355a38b0abcab20165db67ef0a4307 |
| OPTIMIZATION_LOG.md | 6186981e2904bd8a980f0a0c59f20645ab39cf49f3b141384aa0d635007effcd |
| ../huntlib/certificate.py | 4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813 |
| ../huntlib/primes.py | d8cb255728a99c23540bb1af545c0d8d6d88cc400556e470c32fce7e28ea8d3f |
| ../huntlib/checkpoint.py | 5b81f9c1f2322a8790c8c24c769bd6c39e6d4614e8db5f94ba7ac0667f74f02c |
| ../huntlib/evidence.py | a5b2a6d2b573b87772f059ec3660ac298a224e21d944bc364baf3ed681880e3f |
| ../huntlib/ceiling.py | f7db7c72a8f72ad8f71cfe5cc8ecc64e2c9233d351d592d9cc06407b3b243d92 |
| ../power-ladders/OPTIMIZATION_LOG.md | 652586eb6d582daf622beb8599fee78abf6699f3c010e3f798871b34a15754fe |
| ../CODEX_REVIEWS.md (before index edit) | 0a74c207edc20639ff341dd621d303e35a6f5f2ccf071bbebd65b8a6c7c7dc41 |
