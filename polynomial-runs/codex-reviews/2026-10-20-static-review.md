# Polynomial runs: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A165234, A230663, A092120, A347537,
and the A164926 relation.
Workflow: [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

The review team examined this project only, reading the five public roles,
model, documentation, optimization history, checkpoint data and evidence.
Source hashes and lightweight arithmetic were computed. No project engines,
models, oracles, primality experiments, tests, benchmarks, campaigns or GPU
operations ran. This report is an implementation handoff, not a measurement.

## Assessment

**No new substantial speedup or one-day median has been established.**
The two nearer targets remain A230663 a(21) and A092120 a(20). Their stored
conditional forecasts imply about **2.4 and 2.8 days to close the segment
through the median**, using the saved work and historical rates. The two
a(22) targets remain about 92 and 52 days.

The strongest supported throughput option is already documented: moving
5 and 7 out of the device period, sweeping six classes modulo 210 and
putting 59 into the wheel. It measured **1.306× on A347537 n=21**, but was
not shipped. The current filter is n=22, with a different sieve depth and
rate. Its much larger confirmation segment remains a material price.
This is **POL-002**, an existing deferred design, not a missed new result.

The most important new handoff is **POL-001**: beyond the deterministic
primality bound, exact-run coverage needs proved classifications, and a
failed certificate must not silently become a settled term. The current
saved coverage and all nineteen recorded finds are below that bound, so
this is a future requirement, not an allegation of a historical miss.

**POL-003** supplies a rigorous model-tail calculation, taking account of
the subtraction that defines an exact run. **POL-004** proves globally
that no additional forced prime exists for the quartic. Neither gives a
new candidate-density reduction.

Evidence labels used below are **proved**, **observed in source/data**,
**previously measured here**, **unmeasured**, and **model-derived**.

## Definitions, indices and recorded discoveries

Write c(k) for the indicated polynomial, and let r be the number of
consecutive prime values p+c(1), p+c(2), ... after the prime p itself.

| Family | c(k) | Prime conditions for a(n) | Composite stopper | Current lowest open index |
|---|---|---|---|---:|
| A165234 | 2k² | k=0..n−1 | p+2n² | 22 |
| A230663 | k²+3k | k=0..n−1 | p+n²+3n | 21 |
| A092120 | 4k² | k=0..n | p+4(n+1)² | 20 |
| A347537 | k⁴+k³+k²+k | k=0..n−1 | p+n⁴+n³+n²+n | 22 |

For the three offset-1 entries, r=n−1 and the number of prime forms is n.
For offset-0 A092120, r=n and there are n+1 prime forms. Every term is
the least **prime p** with exactly that run. A longer run settles a
different index; it does not settle the shorter one. Every index starts
at p=2, not at a previous term. These distinctions are implemented in
[poly_reference.py](../poly_reference.py), module definition, `run_of`,
`index_of`, `constants` at 391–395, `floor_x` at 421–427 and `is_term`
at 453–458.

The nineteen files contain A165234 a(16)..a(21), A230663 a(16)..a(20),
A092120 a(16)..a(18), and A347537 a(17)..a(21). The sparse known terms
A165234 a(29)=29, A230663 a(39)=43 and A092120 a(19)=163 remain settled
and are skipped. In particular, A092120's next index is 20.

| Family | Recorded final contiguous frontier | Evidence example |
|---|---|---|
| A165234 | a(21)=1718639236717627483289; a(20)=10595142219289312569299 | [a(21)](../evidence/A165234_a21_1718639236717627483289.json) |
| A230663 | a(20)=234505015943235329419; a(19)=1568805168304652737369 | [a(20)](../evidence/A230663_a20_234505015943235329419.json) |
| A092120 | a(19)=163 from the entry's comment; latest new a(18)=262534077967707789937 | [a(18)](../evidence/A092120_a18_262534077967707789937.json) |
| A347537 | a(21)=545605440824324681493499 | [a(21)](../evidence/A347537_a21_545605440824324681493499.json) |

All nineteen files have `certificates_verified=true`, no `unproved`
entries and a nontrivial stopper factor. [RESULTS.md](../RESULTS.md),
lines 18–39, records an independent disk verification on 2026-10-15:
350 deterministic Miller–Rabin certificates, every value below the
deterministic bound. This review read the records; it did not reverify
primality, certificates or the exhaustive least claims.

`FOUND` is still empty (reference line 279). The resumed launcher's own
`found` data handles the real frontier correctly; fresh source-only
openings and the frozen score shapes still use 16,16,16,17.
RESULTS 352–365 and OPTIMIZATION_LOG 1105–1112 already identify frontier
normalization and current-filter shapes as unfinished work. Preserve the
old fingerprints when adding current shapes; a source table update alone
does not independently re-establish the finds.

OEIS status in the existing documents is the 2026-10-15 export's status.
This report makes no claim about current online publication or submission.

### The Euler relation is already implemented

The identity

    x²+3x+p = (x+1)²+(x+1)+(p−2)

gives A230663(n) ≤ A164926(n+1)+2. Conversely, if A230663(n)=p and p−2
is prime, the same exact stopper proves A164926(n+1)=p−2. If p−2 is
composite, A164926(n+1)>p−2. The missing y=0 condition is essential.
The reference's `UPPER` at 247–257 and G1d at 673–699 already express
this, and `launch.also_settles`/`derived_bound` at 377–413 record it.
A230663 a(20) attained the known bound A164926(21)+2. No current open
A230663 index has a newly available upper bound in this source table.
POL-001 adds the proof requirement for a future large Euler rider.

## Actual coverage, partial work and one-day budget

The four runtime checkpoint files are present in this workspace even
though they are ignored runtime files. They agree with RESULTS 303–338.
All use engine v2 / plan p1, unit 6, q2=16384, a full wheel to 53 and
wide 256-period segments. A165234 uses p=5+6t; the others p=1+6t.
The physical period is W=32589158477190044730 and the full segment length
is S=256W=8342824570160651450880, both in p units.

| Family / checkpoint | n | j | u / launches | Proven coverage boundary B | Pending / maximum r |
|---|---:|---:|---:|---:|---:|
| [A165234](../campaign_checkpoint_a165234.json) | 22 | 1296 | 160438 / 341775 | 42235549386438297970080 | 7659 / 15 |
| [A230663](../campaign_checkpoint_a230663.json) | 21 | 48 | 2663 / 512512 | 1590719867556427277670 | 494 / 11 |
| [A092120](../campaign_checkpoint_a092120.json) | 20 | 8 | 209319 / 384384 | 266247275860816780530 | 13882 / 17 |
| [A347537](../campaign_checkpoint_a347537.json) | 22 | 16899 | 0 / 144256 | 550724189106034565892270 | 0 / — |

Checkpoint anchors are lines 2–40; `found` and census data follow pending.
B is the exclusive covered endpoint, so every still-open term is at least
B. These endpoints are even, and p is prime above 2, so the documents'
strict “greater than B” formulation is also valid here.

The covered region applies to **every open index at or above the filter**.
A sorted closed segment has had every relevant survivor's exact run read,
including later indices. `launch.swept_k` at 812–817 takes the maximum
of the completed wheel boundary and carried `x_start`, so a promotion's
inherited coverage is preserved even before the new wheel catches up.
The sorted pending loop at 1289–1292 processes the entire closed segment;
`follow_frontier` at 1014–1048 then carries its end. This useful coverage
reuse is already implemented. Partial u values are work across the whole
segment, not a contiguous numerical fraction. None of the pending runs
reaches its current target.

The first three families' wheel split is
{5,7,11,13,17,19,23,37} × {29,31,41} × {43,47,53};
A347537 uses {5,7,11,13,17,23,37,41} × {19,29,31} × {43,47,53}.
[BENCHMARKS.md](../BENCHMARKS.md), lines 73–98, records these plans.

| Family | Stored rate p/s | Remaining first closure | Whole closures in 24h | Completed endpoint after 24h |
|---|---:|---:|---:|---:|
| A165234 | 1.51e18 | 0.81 h | 16 | 175720742509008721184160 |
| A230663 | 9.20e17 | 2.51 h | 9 | 76649700738350985204960 |
| A092120 | 1.24e18 | 0.85 h | 13 | 108717432679905989219280 |
| A347537 | 3.42e18 | 0.68 h | 35 | 842723049061657366673070 |

These are arithmetic scenarios: constant recorded rate, unchanged filter,
no discovery/promotion, negligible startup and verification overhead,
and equal work per launch as the campaign analysis assumes. If f=u/L,
the calculation is C=floor(f+86400R/S), followed by endpoint (j+256C)W.
It is not a new timing or probability calculation.

The n22 rates were short, alternated readings at the actual paused
positions on 2026-10-15, not frozen score workloads. A230663 n21 and
A092120 n20 use the recorded per-filter price table. The latter also
achieved 1.27e18 during its partial campaign segment. Whole sustained
campaign filters matched their prices within about 0.99–1.03×.
See BENCHMARKS 100–181 and OPTIMIZATION_LOG 1055–1096. The older n21
A347537 rate of about 2.03e18 is not its current n22 rate.

### Conditional forecasts, not schedules

RESULTS 308–325 records a model calculation conditional on each B, made
on 2026-10-15. It was not written into the older `model_results.json`.

| Open target | Stored conditional median p | Raw remaining median clock | Clock to close through rounded median | Stored raw day probability |
|---|---:|---:|---:|---:|
| A165234 a(22) | 1.20e25 | 91.66 d | 91.67 d | 3% |
| A230663 a(21) | 1.86e23 | 2.32 d | 2.41 d | 33% |
| A092120 a(20) | 2.98e23 | 2.78 d | 2.76 d | 31% |
| A347537 a(22) | 1.59e25 | 51.95 d | 51.95 d | 3% |

The closure column adds segment rounding but credits saved u; therefore
it can be slightly below the raw distance/rate column, which gives no
credit for work in flight. Rounded median inputs limit precision.
The last column is the stored model's continuous-depth probability,
not an exact probability of a certified term before a day. The appropriate
future calculation is `p_by(family,index,B,completed_endpoint)`, with
startup, certification and changed rates included. No model was rerun.
A later-index discovery can also occur, but the table concerns the named
next index, not the probability of any new exact-run term.

At the current segment sizes a one-day confirmed find is already possible;
there is no plus-two-style first-closure barrier. To put the same rounded
median inside one day would require roughly 2.4×/2.8× for the nearer two,
and much larger gains for the others. No supported proposal supplies that.
The nineteen finds' recorded E mean is 0.98, with ordinary scatter
(RESULTS “The finds against the model”); this small sample is not a
guarantee, nor support for applying an automatic 1.5–2× penalty.

<a id="pol-001"></a>
## POL-001 — Prove exact classification before committing coverage

**Priority:** correctness prerequisite for searches beyond the proof
crossing. **Classification:** observed control flow; new review finding,
not a speedup or a demonstrated historical error.

[huntlib/primes.py](../../huntlib/primes.py), line 35, sets the exclusive
deterministic bound to 3317044064679887385961981.
[`poly_search.k_proof`](../poly_search.py) at 141–148 subtracts the
largest required shift. The term ceiling is
10^40; the residue-list limit is 32 prime forms (index 32 on three
families, 31 on A092120). Actual shifts and a classified run's own index,
not just the current filter, determine which values are below the bound.
The two stored a22 medians lie beyond it. All current coverage, recorded
finds and baseline one-day endpoints above lie below it.

[`launch.certify_value`](../launch.py) at 348–359 retries and re-verifies certificates.
However, `record_discovery` calls `certify_run` at 925, writes
`certificates_verified: not unproved` at 951–952, then assigns `self.found`
at 980 and emits DISCOVERY even when `unproved` is nonempty (1006–1012).
Those candidates remain probable-prime claims, not proved settlements.
`also_settles` at 387–402 checks the additional Euler value p−2 with
sympy, but does not attach a certificate for it above the deterministic
bound. Existing complete historical certificates are unaffected.

There is a second, exact-run-specific obligation. A failed strong test
proves compositeness, so a probable-prime chain cannot understate a run.
But **overstating a run can hide an exact-run first occurrence**: an actual
open index may be classified as a larger already-settled index.
`event_kind` at 240–261 and `handle` at 870–889 can send such an apparent
index to CENSUS without verification. Sparse and early settled indices
make a monotone “longer is always safe” argument invalid. This describes
a logical exposure after the bound, not a found pseudoprime or observed
misclassification.

Future implementation must prove the classification of every candidate
whose true run could reach an open index, or prove facts excluding it
from every open index it could occupy. Cheap failed tests below the
current target remain safe exclusions. A claimed new term needs its whole
prime prefix proved and an actual composite stopper. To exclude a
candidate from an earlier open exact index, it can instead suffice to
prove that index's own stopper prime: the run cannot end there. Resolve
every open index it could occupy; this selective route may be cheaper
than proving the whole apparent run. A certificate failure is unresolved,
not composite and not settled.
Keep unresolved candidates and their coverage barrier durable. Do not
advance the certified boundary past an unresolved candidate or use an
unproved discovery to promote away its filter. A separately labelled
probable-result queue may retain progress without making a least claim.

For an Euler rider, certificates of the A230663 values prove y=1..n;
certify the additional y=0 value p−2 and preserve the shared stopper.
Persist resolved evidence, frontier and coverage atomically. A capped
run must be extended or held, never interpreted as an exact stopper.

Claude's future tests should inject certificate failure and a classifier
overstatement into an apparent index m with both m and m+1 settled, while
the true exact index below m remains open. This exercises the unverified
CENSUS branch rather than the independently checked NEAR branch.
Require a held coverage boundary and no settled/proved announcement;
then resolve the candidate and verify resume, census and evidence once
only. Preserve the independent oracle and the existing MR-bound tests.
These are future validation requirements; none ran during this review.

<a id="pol-002"></a>
## POL-002 — Existing six-class wheel: useful research, not a day breakthrough

**Priority:** medium for long hunts, lower for a one-day objective.
**Classification:** previously measured here but unshipped; explicitly
known and deferred in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md),
round 3, lines 493–706.

For A347537 n≥6, allowed p residues modulo 5 are {2,3,4} and modulo 7
are {1,2}. Together with p≡1 mod6 this gives precisely

    p ≡ 37,43,79,127,163,169 (mod 210).

Sweeping all six classes p=r+210t is an exact partition of the old
survivors. It moves 5 and 7 outside the device period without asserting
that either is forced. The period of the {11..59} wheel is
9156001667401012567<2^63, with split
{11,13,17,19,23,43,47} × {29,31,37} × {41,53,59}.
The old n21 residue counts are 4209408 × 4845 × 34320; at q=59 the
old n21 quartic filter kills 19 residues, so candidate count per p unit
falls by exactly 40/59. Moving 5 and 7 alone causes no thinning.

At the **actual current filters**, direct finite arithmetic on the shift
formulas gives the following q=59 counts. These are mathematical work
ratios, not measured speedups or a search over candidates.

| Family / current n | w(59) | Candidate-generation reduction from adding 59 |
|---|---:|---:|
| A165234 / 22 | 22 | 59/37 ≈ 1.595× |
| A230663 / 21 | 21 | 59/38 ≈ 1.553× |
| A092120 / 20 | 21 | 59/38 ≈ 1.553× |
| A347537 / 22 | 19 | 59/40 = 1.475× |

In particular, the history's A092120 n21 count of 22 killed residues is
not its present n20 count.

Round 3 measured the complete six-class work at 1.306× the old plan at
A347537 n21 and p≈2.95e23. It also measured 1.102× at 128 periods and
0.811× at 64 periods. Counts and runtime are different: the 59/40 count
benefit was partly spent on slower work per candidate. The source already
proposes analogous six-class partitions for the other three families,
but has no destination measurements at their current filters.

The 256-period physical segment becomes 59S≈4.922e23. All six classes
must close before a least claim can use that endpoint. It took about
49 hours at the measured old n21 rate. Even the illustrative assumption
that the same 1.306 factor holds at the current n22 rates would give
about 69 hours per segment on A165234 and 31 hours on A347537. Those are
fixed-rate scenarios, not measurements, and neither closes once in a day.
Shorter windows change the rate, as the recorded 128/64 arms demonstrate.

The history correctly deferred this at the old n21 cursor: expected
confirmation cost improved only 1.029× because of oversweep. Its 1.297×
long-hunt example was priced with an older illustrative a22 rate and
floor; it is not the present 52-day forecast divided by a measured n22
speedup. Reprice at the actual saved B, filter, depth and day objective.
The 19-to-20-style generic post-find suffix reuse suggestion is unnecessary:
this launcher already reads and carries the whole closed segment.

**Future implementation obligations.** Keep the forced-single-class API
strict; add an explicit complete-class contract rather than weakening
`assert_unit`. The present constructor derives one r0 from the unit
([`poly_gpu.GpuEngine`](../poly_gpu.py), 2628 and 2722). A class-aware implementation must
carry the class set and index through tables, stream keys and checkpoints.
Preserve W1<2^32, W2<2^32, Wp<2^63, Wp+q2<2^64, the R2/R3 limits and the
wide record's period byte (GPU 2668–2743, 3047–3051). The documented
split meets the explicit-level activation checks; arbitrary partitions
must not rely on Python list ordering to establish level validity.

Adopt the absolute completed floor B, floor-divide by the new W and clip
at B. Never reinterpret an old u or a completed single class as numerical
coverage. Include period, class, launch and a complete enumeration
fingerprint. The current loader checks n,W and segment/launch counts
(launch 584–606), but a mismatch resets u while retaining loaded pending
(799); that is not a complete migration policy. Reconcile or deduplicate
partial pending and survivor/census accounting, preserve committed
evidence, and credit coverage only when every class closes. Raw census
remains sieve-filter dependent; changing depth needs explicit provenance.

Future parity must compare the union of all class streams against the
independent dense CPU sieve on the same absolute p interval, including
exception boundaries, known finds, wide reconstruction and class-boundary
resume. Add frozen current-filter shapes alongside the existing seven
at [score.py](../score.py) 82–96. Reject a design that saves device time but worsens
completed coverage at the chosen deadline.

<a id="pol-003"></a>
## POL-003 — A collision-free tail, propagated through exact-run subtraction

**Priority:** model assurance. **Classification:** new proved bound;
no search or runtime speedup claimed.

[poly_model.py](../poly_model.py), `log_singular` at 83–98, truncates at
Q=200000. At a filter with m forms, its local factor is

    A_q = (1−w_q/q)/(1−1/q)^m.

All forms are p+c(k), so a collision modulo q requires q to divide a
nonzero difference c(j)−c(i). For the three quadratics these differences
factor as 2(j−i)(j+i), (j−i)(j+i+3), or 4(j−i)(j+i).
For the quartic,

    c(j)−c(i) = (j−i)G(i,j),
    G = j³+j²i+ji²+i³+j²+ji+i²+j+i+1.

For 0≤i<j≤r, G≤4r³+3r²+2r+1. Even r=32 gives 134209<Q.
This covers every supported filter and the next-index series used by its
exact-run model: at most 33 constants, indexed 0..32. Thus every q>Q
has w_q=m exactly. The omitted factor T_m is universal for that m:

    T_m = ∏_(q>Q) (1−m/q)/(1−1/q)^m,
    −m²/[2(Q−m)] ≤ log T_m ≤ 0.

To see the bound, expand the logarithms. The linear term cancels;
the remaining negative magnitude is at most
m²/[2q(q−m)]. Bound it by m²/[2(q−m)²] and sum over all integers q>Q.
Q is composite, so the model's q<Q convention leaves exactly this tail.
At the present m=21/22 filters, these exponential lower bounds are
approximately 0.998898 and 0.998791. Their next-index factors have the
same controlled form.

The model uses an **exact-run difference**, however (`_density_curve`,
110–115), not a single at-least intensity. Let A and B be its truncated
at-least intensities at the current and next index, with A>B. Then

    R_m = T_(m+1)/T_m
        = ∏_(q>Q) [1−m/((q−m)(q−1))] < 1,
    D_true = T_m[(A−B)+(1−R_m)B].

In particular,

    exp(−m²/[2(Q−m)]) ≤ D_true/(A−B)
       ≤ 1 + [m/(Q−m)]·B/(A−B).

The upper bound uses 1−∏(1−t_q)≤Σt_q≤m/(Q−m).
It explicitly exposes cancellation: an at-least-series percentage cannot
be applied blindly to A−B, especially near the model's clipped zero region.
Future code should propagate the two correlated tail factors or the
displayed interval, and then integrate. Do not enlarge a forecast error
bound from these formulas into a claimed error bound for the underlying
prime-tuples/Poisson heuristic. No model or singular product was evaluated
in this review; the displayed decimals are arithmetic from the bound.

Keep the independent killed-set definition, model floor and exact index
conversion. A future static-bound helper can be checked symbolically and
against small independently formed constant sets; a later implementation
may compare increased-cutoff products without changing the search stream.
This is an assurance addition, not evidence of an error large enough to
turn the recorded multi-day searches into one-day searches.

<a id="pol-004"></a>
## POL-004 — Complete the quartic no-extra-forcing proof

**Priority:** mathematical assurance. **Classification:** new complete
proof of an existing claim; no additional thinning.

The reference proves admissibility using the collision f(0)=f(−1)=0 for
f(k)=k(k+1)(k²+1), but its no-extra-forcing claim is backed by finite
checks through n=30 and primes below 400 (G2c, 775–807).
Here is an all-prime argument.

For prime q≥7, suppose the full image of f over F_q has q−1 elements.
There is then exactly one repeated image value, with two preimages.
Since f(0)=f(−1)=0, that repeated value must be 0. Let b be the missing
value; b≠0. Summing all q values with multiplicity gives −b modulo q:
the sum of all field elements is zero, one b is missing and the repeated
zero adds nothing. But

    Σ_k f(k) = Σ_k(k⁴+k³+k²+k) = 0 (mod q),

because each exponent is between 1 and q−2. This contradicts b≠0.
Therefore the image has at most q−2 elements. At q=5 the image is
{0,4}; at q=3 it is {0,1}; at q=2 all shifts vanish.
Every finite prefix image is a subset of the full image, so **no prime
above 3 is forced at any index**. Together with the existing quadratic
bound (q+1)/2<q−1 for q≥5, this proves the forced unit is exactly 6 from
the first two-form filter for all four families.

This proof does not select one surviving class as the only class to hunt.
The current sieve already keeps every allowed class; the theorem explains
why the maximal-forced-unit shortcut from other projects cannot add 5 or 7
here. Multiple allowed classes must all be represented, as in POL-002.
Keep prime-equals-value exceptions separately: a sieve is valid only
above q2, and the host must still classify [2,q2], including the sparse
comment terms. See `poly_search.k_floor`, `zone` and `prefix_hits`.

Admissibility concerns the prime conditions. To obtain exact runs under
the prime-tuples conjecture, choose a prime ℓ larger than the stopper
shift and put p≡−c_stop modℓ. Every required earlier form is nonzero
modℓ, all other local admissibility is retained, and sufficiently large
p makes the stopper a multiple of ℓ strictly greater than ℓ. Thus this
does not uncover an impossible exact index. It is a conditional
infinitude argument, not an unconditional existence proof.

Claude can add the proof to the reference explanation and retain the
independent finite residue checks as implementation checks. There is no
reason to change a wheel, checkpoint, oracle or fingerprint for this
assurance result alone.

## Alternatives examined and disposition

- **More strongly filtering the next rung:** making it prime discards the
  still-open exact target; forcing it composite discards later-index
  discoveries unless another exhaustive stream retains them. The existing
  extended classification and closed-line carry avoid this duplication;
  its finite cap still needs POL-001's extend-or-hold rule.
- **A165234/A092120 equal singular series:** at equal form count the
  constants differ by multiplication by 2, a bijection modulo every odd
  prime; both have the same parity factor. This is equality of local
  counts, not a prime-preserving bijection of candidates. Scaling p to 2p
  does not transfer a least-prime claim or combine their coverage.
- **Quadratic image formulas or Legendre tests:** the current killed sets
  already deduplicate equal residues. Replacing compact exact membership
  by square-root/image tests establishes no new exclusion or supported
  speedup at these short finite prefixes.
- **Doubly-focused enumeration:** already built and measured at 0.069 of
  the engine's best rate, OPTIMIZATION_LOG 708–862. It loses the periodic
  window amortization; the documented arithmetic floor still loses.
- **Ranked-subwheel windows:** already built and declined, 864–1053.
  Window-only rates were 0.72–0.78 of the reference stage, and adding 59
  moved the tables into a bandwidth-limited regime around 0.31. Their
  candidate reduction cannot be counted again as an untested free gain.
- **Larger windows, quads, and repeated donor ports:** already priced in
  rounds 1–2. The current engine already has periodic window sieving,
  wide records, lazy/folded rounds and generated tails. No new mathematical
  justification was found for reopening those tuning experiments.

Unresolved items are the actual current-filter six-class rates, their
completed-coverage costs, a robust proof barrier after the deterministic
bound, and current frozen benchmark shapes. Engineering time is additional
to any quoted hunt clock. No implementation or campaign is authorized by
this review.

## Source snapshot and execution record

Git HEAD: `f8fdb200c56a54aa5e207c146882f7d2d7b87224`.
The shared worktree was dirty during review; these source/data hashes
identify the reviewed content. Root documentation and project README
navigation were being edited separately and are not hashed here.

| File | SHA-256 |
|---|---|
| poly_reference.py | cac1c856ab0cc3b8a7108403c9f4c0cbd50d6c2368c1ec245f4fae726cee62d2 |
| poly_search.py | b3c4e8b1eebb830b3767ab9e25e8a1cd540d8923d4a3be03e13f8b6246d75021 |
| poly_gpu.py | 4f5971bd643ca26622ab16c2cc9aa3b66669aae3c52a85d1e818b7779265d11c |
| launch.py | c1b2b7682328989fb2f1b185fafb6417204150be24d7a301192e7d0c6359624b |
| score.py | b974a3c16b37fcd63265a0fb6284a911e5a8737a307bcf0f008b9e5abbb9cb36 |
| poly_model.py | 6369ad3694c1cea73395e726c82204233aa3d32464b7fb9bf386d2d1b337aa00 |
| model_results.json | 621d9a57610beb600045308d034a0ee299b962c16301d778fe2e3cecf3459fe6 |
| OPTIMIZATION_LOG.md | 40022808a7ba69d68a6e620ebbe685439df8e156c1fb930ffa24806d830d4f60 |
| RESULTS.md | f1363f0cf031e50d7ae1e84bb05629aa7f58056e608968f2491a1dc32e9939e9 |
| BENCHMARKS.md | 8233d584f0ce5fe23a6dc2b06cdc28ae165ebfd5adcc835d3762fa0ff852e2aa |
| campaign_checkpoint_a165234.json | 4bcf962b3a2d0d2bd1965c0c70c25aec323af0141b6b62e8f5c10d4dc52918d1 |
| campaign_checkpoint_a230663.json | bebffa63d859603cc88b55efd55865fad8f2d9aaa268debd21e20a0cfb66023d |
| campaign_checkpoint_a092120.json | 299ec5d79c82f343eea979b82826b164cd982c74fb2a06a5e3aa75d895e1dead |
| campaign_checkpoint_a347537.json | a62e3402df4b320453423cf726757f171ba08ac709620009b7a10f7c5669339b |
| ../../huntlib/primes.py | d8cb255728a99c23540bb1af545c0d8d6d88cc400556e470c32fce7e28ea8d3f |
| ../../huntlib/certificate.py | 4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813 |
| ../../huntlib/ceiling.py | f7db7c72a8f72ad8f71cfe5cc8ecc64e2c9233d351d592d9cc06407b3b243d92 |

Executed only file reads/searches, JSON parsing, hashes, simple arithmetic,
documentation writes and documentation checks. No hunt code was imported
or executed, no new performance measurement or model forecast was made,
and the GPU was never queried or used.
