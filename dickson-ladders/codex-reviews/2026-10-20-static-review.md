# Dickson ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A247965 and its current a(14)
frontier. **Status:** proposed analysis; no implementation or new measurement.
This review follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

Three reviewers independently examined the mathematics, implementation and
evidence before this report was consolidated. Only source/document reads,
hashes, lightweight arithmetic and a mathematical reference lookup were used.
No GPU operations, project imports, model execution, primality experiments,
oracles, tests, benchmarks or campaigns were run.

## Assessment

The strongest new lead is **DKL-001**: the full sieve tables currently
duplicated for each fold offset are cyclic translations of one canonical
table. A modular phase can represent that translation exactly. This removes
the table-multiplicity argument that helped rule out a second fold.

There is also a smaller current-filter correction, **DKL-002**: at n = 14,
prime 19 is a stronger single fold than the automatic choice of 17, with
the same number of surviving offsets. **DKL-003** describes the larger
factored-wheel/window route and a concrete root-capacity trap in transferring
a linear-form engine.

None establishes a one-day hunt. At the old n = 13 device rate, reaching
even the stored *unconditional* a(14) median from today's saved boundary
would take about 7.63 days. A current conditional median is farther away.
Small fold changes cannot plausibly supply that entire reduction by
themselves. The larger redesign has to remove work from multiple stages.

Evidence labels used below:

- **Proved:** an implication or count established by the given mathematics.
- **Source/data observation:** read from the identified files, not executed.
- **Historical measurement:** an existing result with its original scope.
- **Unmeasured hypothesis:** an implementation benefit requiring later work.
- **Model-derived scenario:** arithmetic under stated model/rate assumptions.

## Definition, snapshot and current state

A247965 a(n) is the least positive **k** for which `m*k^2+1` is prime for
every `m = 1..n`. The predicate is **at least n**, not an exact run with a
required composite at n+1. A longer run can settle several successive
indices; equal terms are permitted. See
[ladder_reference.py](../ladder_reference.py), `run_length` at line 73
and `first_k` at line 81. Its `hi` argument is inclusive; the engine's
interval APIs require their own explicit endpoint contract.

Above the finite exception zone, every eligible k is a multiple of
`W(n) = product(primes <= n+1)`. If q does not divide k, some
`m = -k^(-2) mod q` lies in `1..q-1`; when q <= n+1, that m is tested.
Divisibility implies compositeness only when the value exceeds q.
The direct oracle handles small values; the production floor is `k = 10^4`.

For q > n+1, let K_q be the forbidden residues of `j = k/W`. The quadratic
roots are distinct across the m values, and

`|K_q| = 2 * #{1 <= m <= n : (-m | q) = +1}`.

The CPU derives roots with `sqrt_mod`; the GPU builds them by a direct
residue walk. Preserve that independence.

The reviewed Git HEAD was
`f8fdb200c56a54aa5e207c146882f7d2d7b87224`; the worktree had existing
documentation changes and an untracked project. Hashes below identify the
actual reviewed bytes. Snapshot line numbers supplement function names.

| File | SHA-256 |
|---|---|
| [ladder_reference.py](../ladder_reference.py) | `E1586612FD0C5FD228DA92ED998A72277C9C9AC4466558DEE2FD1DDC6BE119AF` |
| [ladder_search.py](../ladder_search.py) | `17F7DE3210C2569A02DDCBBDCA5B46D177A689A2D89F1DEE739A40BFA911EDC9` |
| [ladder_gpu.py](../ladder_gpu.py) | `9665766356B53C70727F4EB7A56B2D9953D359F024F39FF47C14428ECB26C2A0` |
| [ladder_model.py](../ladder_model.py) | `68D5C4217CB014425FB2042CC84FCA0DDE6B3616DD6EF7E1301FD22124ED91BC` |
| [launch.py](../launch.py) | `6E30F12D552511E22F23B3C3E08208C47C3E8629FA963020C7C4D68E44AE8B68` |
| [score.py](../score.py) | `52F3CA7901D94BDCB84B76C8BD77B226383FF3BE6C77B6B77FA8A8657B0E60D8` |
| [model_results.json](../model_results.json) | `AC24EC6A4E04DCA0BBE86AC738B61EC752F6ECC330A40138F98372A1AA075213` |
| [campaign_checkpoint.json](../campaign_checkpoint.json) | `CBDC69AAEDB76E62294297623106BD970A3BEAEFFD0FFE95FF68F1997D45268D` |
| [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) | `FB9A855521419E915F4BC5AEDF778BC485B646BAB0749E674FD8B94E6DC20C0F` |

| Saved/configured quantity | Value |
|---|---|
| Current filter / open term | n = 14 / a(14) |
| Last recorded term | a(13) = 12094123415384869458600 |
| Forced wheel W | 30030 |
| Saved `next_j` | 521960159937822721 |
| Absolute next boundary C = W*next_j | **15674463602932816311630** |
| Checkpoint key | `dickson-ladders/v2/q2=262144/jceil=4e18` |
| Sieve depth / automatic fold | 262144 / 17 |
| Device coordinate | u in `j = P*u+r`, with u below `J_CEIL = 4e18` |
| Current folded candidate reach | `30030*17*4e18 = 2042040000000000000000000` |
| Normal campaign segment | `2^42` units of j, or 132073336728453120 units of k |

The saved state is historical, not an observation of a running process.
The checkpoint's old version wording does not describe all current engine
internals; its preserved external coordinate is still j. The saved `found`
mapping carries a(12) and a(13), while earlier recorded terms also belong
to the project's evidence history.

At n = 14, values leave the deterministic Miller–Rabin range already at
`k = 486756323951`, far below this frontier. Rejections by divisibility or
failed strong tests remain rigorous; reported successes require certificates.
[launch.py](../launch.py), `factor_n_minus_1`, `certificate`,
`verify_certificate` and `full_verify` use the structure `N-1 = m*k^2`.
The [a(13) evidence](../evidence/ladder_hit_run13_k12094123415384869458600.json)
records its certificates and a breaker at m = 14 with factor 2711.
Those stored checks were not rerun. Certificates prove the accepted values;
leastness also depends on the exhaustive coverage history.

<a id="dkl-001"></a>

## DKL-001: replace offset-specific tables with one pattern and a phase

**Priority:** first structural experiment. **Disposition:** proposed.
**Evidence:** exact equivalence; new representation of an existing fold;
unmeasured destination performance.

`GpuEngine.__init__` in [ladder_gpu.py](../ladder_gpu.py), lines 476–531,
allocates full `d_bits[r]` and `d_pat[r]` for every surviving fold offset r.
The v4 log prices five copies at about 344 MiB each at the campaign depth.
Its second-fold discussion, lines 686–692, declines 35 classes and about
12 GiB at the then-current n = 13.

For a fold P and a remaining sieve prime q with `gcd(P,q)=1`, define

`H_q = {P^(-1)*c mod q : c in K_q}`,

`delta(q,r) = P^(-1)*r mod q`.

Then, exactly,

`P*u+r mod q in K_q`

if and only if

`u+delta(q,r) mod q in H_q`.

Therefore every per-offset bit table is a cyclic translation of the
same q-bit table H_q. The corresponding 64-candidate pattern is a lookup
at the shifted start; its stride through subsequent blocks remains 64.
There is no need to store a second copy of all q bits for each offset.
Zero is an allowed fold offset, so its existing table is a natural
canonical construction. Build it by the GPU's existing residue walk,
not by importing the CPU root helper.

The representation changes table storage from approximately
`offset_count * sum_q ceil(q/32)` words to one copy plus phase metadata
of order `offset_count * number_of_primes`. Phases may alternatively be
prepared for the current offset only. Pattern storage shares the same
translation property. This is a proved storage relationship, not a
measured allocation or speed result.

For stage 1a, add delta to the initial prime residue in `_S1A_INIT`;
the existing recurrence then carries it without an extra operation on
every 64-bit block. Stage 1b must account for the phase on each candidate
probe, for example an addition followed by one conditional subtraction
when both operands are canonical. That cost and metadata access may
erase some gains. Queue and pattern padding requirements remain unchanged.

For a composite fold, construct offsets by CRT of the allowed classes of
each folded prime. Remove **every prime factor of P** from the remaining
sieve. The current constructor accepts one prime and excludes only
`q != fold` at lines 446–456. Simply permitting P = 323 there is wrong:
testing divisibility modulo 323 is not equivalent to testing 17 and 19
separately, and inverses do not exist for retained primes dividing P.

The current table kernel computes `P*s+r` in an unsigned 64-bit temporary
before reducing modulo q (`_TABLE_SRC`, lines 197–205). A larger CRT fold
can overflow that temporary even if its final residues fit. Reduce P and
r modulo q before multiplication, or prove the full intermediate bound.
The existing small-fold bound cannot be inherited unchanged. This check
is separate from survivor-coordinate capacity and the q² arithmetic bound.

Future validation must compare canonical-plus-phase tables with the direct
walk at every represented residue, then compare complete folded/unfolded
streams on populated, unaligned and high windows. Exercise phase wrap,
word boundaries, partial 64-bit blocks, every offset and queue overflow.
The oracle must continue to evaluate `m*k^2+1` directly.

<a id="dkl-002"></a>

## DKL-002: select the fold for the actual filter

**Priority:** small, separable opportunity. **Disposition:** proposed.
**Evidence:** exact counts; runtime unmeasured.

The automatic choice in `GpuEngine.__init__`, line 444, is the first
sieve prime. It is 17 at both n = 13 and n = 14, but the relative
quadratic kill counts change:

| Filter | Survivors modulo 17 | Survivors modulo 19 |
|---|---:|---:|
| n = 13 | 5 | 7 |
| n = 14 | 5 | 5 |

At 17, adding m = 14 contributes no roots. At 19 it contributes two:
`-14 = 5 (mod 19)` is a square, since `9^2 = 5 (mod 19)`.
Distinct m give disjoint roots. Thus at n = 14, a single 19 fold
generates `5/19` rather than `5/17` of the j line: **17/19 as many
generated inputs**, with a candidate-rate ratio of **19/17 = 1.118**.
Both choices have five offsets. The omitted fold prime remains in the
other choice's ordinary sieve, so the final survivor set is identical.

This does not predict an 11.8% end-to-end gain: the first remaining prime,
prefix length, queues and table costs change. A filter-aware fold choice
needs whole-pipeline measurement later. The existing `--fold` path can
express either single prime; selection logic need not start with the
larger redesign.

Combining 17 and 19 at n = 14 keeps **25/323** CRT classes, not the
35/323 of the historical n = 13 estimate. Relative to the present 17
fold, its further dense-input reduction is 19/5 = 3.8. DKL-001 removes
the linear scaling of full tables with those 25 offsets.

However, the post-fold log puts stage 1a near 35% of the old device bill.
If only that stage improved by 3.8 and everything else stayed fixed,
the ideal gain would be

`1 / (0.65 + 0.35*5/19) = approximately 1.35`.

Even deleting that stage entirely gives only 1/0.65 = 1.54. These are
illustrative bounds from an old n = 13 phase split, not present n = 14
measurements. They explain why a second fold alone is not an eightfold
one-day solution.

<a id="dkl-003"></a>

## DKL-003: a factored wheel can change more than the dense prefix

**Priority:** larger investigation after DKL-001. **Disposition:** proposed.
**Evidence:** mathematical applicability proved; plan and speed unknown.

Modern sibling engines factor a CRT wheel into manageable residue arrays
and sieve a bit window over its period index. Their essential requirement
is a fixed forbidden set in the candidate variable for each prime.
Dickson has exactly that: its forms are quadratic, but their forbidden
residues in k are fixed once n is fixed.

Let M be a wheel containing the forced primes and selected further sieve
primes, and let r be an allowed canonical wheel residue. For
`k_i = M*(J+i)+r` and a remaining prime q, define

`d_q = M^(-1) mod q`, `H_q = d_q*K_q^(k)`, `b_q = J+d_q*r mod q`,

where `K_q^(k)` is the forbidden set in k rather than j. Then

`k_i mod q in K_q^(k) iff b_q+i mod q in H_q`.

This is the period-window identity independently of the polynomial degree.
Use factored CRT enumeration rather than materializing the full Cartesian
product. Share the patterns and carry the period separately if offsets
would overflow. Relevant references are
[clique_gpu.py](../../clique-ladders/clique_gpu.py), `window_patterns`
at line 1327, and the representation discussion in the
[square review](../../square-ladders/codex-reviews/2026-10-20-static-review.md).
These are applicability references, not Dickson speed measurements.

**Do not copy linear-form capacity assumptions.** The clique donor sets
a 16-slot residue list for at most 16 linear forms (`clique_gpu.py`,
near line 1986). At Dickson n = 14, q = 97 already kills **18** residues:
m in `{1,2,3,4,6,8,9,11,12}` each contributes two roots. Size from actual
maximum kill counts, with `2*n = 28` as the safe current bound; a 32-slot
layout suffices here only after all related bounds are checked. Future
filters require their own capacity policy.

The possible larger gain is that wheel generation and window masks replace
work now distributed between the dense prefix and later candidate rounds.
A proposal changing only the old 35% phase inherits the previous ceiling.
No wheel, width, cutoff or speed factor is selected by this report.
Claude must price the complete segment, all later rounds, survivor delivery
and host verification at n = 14 before preferring this to the simpler fold.

Preserve the public five-role structure. Keep the independent CPU
square-root construction and direct oracle. Do not silently inherit a
donor's higher candidate ceiling, a one-root-per-form assumption, or a
linear-form certificate path.

<a id="dkl-004"></a>

## DKL-004: use actual quadratic selectivity in test ordering

**Priority:** secondary. **Disposition:** proposed. **Evidence:** exact
zero-work elimination and a cost-model ordering rule; runtime unmeasured.

The prime array remains numerically sorted after construction, while the
engine already knows each exact `w_q` from table popcounts
(`ladder_gpu.py`, lines 440–456 and 503–507). Character fluctuations mean
`w_q/q` need not decrease with q. Stage 1b's candidate test can stop after
its first rejection.

A prime with `w_q = 0` has an empty kill set and can be omitted exactly.
For two equal-cost independent modular tests, ordering the larger rejection
fraction first minimizes expected tests: their respective costs are
`c + (1-p_A)*c` and `c + (1-p_B)*c`. With unequal scalar costs, the
pairwise criterion is descending `p/c`.

Independence here describes uniform residues over the joint CRT period,
not a promise about every finite window. Actual device costs also depend
on memory access, warps and compaction. Stage 1a has different pattern-row
sizes and does not satisfy this simple cost model. Use the rule as a
candidate ordering, not a throughput theorem.

Any permutation or omission must move the corresponding prime, reduction
constant, table offset, phase, count and round boundary together. Prove
the final survivor set unchanged; retain every frozen fingerprint under
its original interval and sieve contract. No significant gain is priced
here, and the modern wheel investigation may subsume this idea.

<a id="dkl-005"></a>

## DKL-005: the claimed singular-series tail bound omits a term

**Priority:** correctness of forecasts. **Disposition:** proposed.
**Evidence:** analytic derivation; no new numerical model run.

`log_singular_series` in [ladder_model.py](../ladder_model.py), lines 56–63,
returns `n*n/qcut` as a bound because w_q averages n. `z1_tail_small`
then checks that asserted number. For q > n+1, however,

`w_q = n + sum_{m=1}^n chi_m(q)`,

where chi_m is the primitive quadratic character associated with
the field Q(sqrt(-m)). Thus for the local factor
`A_q = (1-w_q/q)/(1-1/q)^n`,

`log A_q = -sum_m chi_m(q)/q + O(n^2/q^2)`.

Average cancellation does not bound the omitted first-order prime sum
by the sum of 1/q². The code has not established its advertised
`9.8e-5` logarithmic tail bound at n = 14.

A constructive repair is to remove the character contribution analytically.
Set `B_q = product_m (1-chi_m(q)/q)`. Then

`C_n = [product_m L(1,chi_m)^(-1)] * product_q (A_q/B_q)`.

The first-order terms cancel in `log(A_q/B_q)`, leaving an absolutely
convergent remainder. Use primitive characters consistently and compute
the finitely many small-prime factors exactly; repeated characters retain
their multiplicity. The Euler-product convention and the conversion
between primitive and induced characters are given in
[NIST DLMF 25.15, equations 2 and 4](https://dlmf.nist.gov/25.15).
The cancellation and bound below are the derivation for this project.

For an integer cutoff Q >= 4n, use
`|log(1-z)+z| <= z^2` for `|z| <= 1/2`, `w_q <= 2n`,
and `sum_{j>Q} 1/j^2 <= 1/Q`. The remaining logarithmic tail of
the accelerated product is at most

`(4*n^2 + 2*n)/Q`.

This deliberately conservative bound does **not** bound the old,
uncorrected product. Error in evaluating the L-values and the finite
product needs separate control. Future validation should compare both
formulations at several cutoffs and verify the explicit remainder,
using an independent numerical method where practical.

This repairs model arithmetic and may reduce model-construction work;
it is not a sieve speedup. It does not prove Bateman–Horn or the Poisson
first-occurrence law. It also does not show that the historical 2.26-fold
optimism came from truncation.

The quadratic prime-tuple heuristic here is Bateman–Horn (or the
qualitative Schinzel hypothesis H); standard Dickson's conjecture concerns
linear forms. Retain the project name, but distinguish these hypotheses
when updating the mathematical explanation. A certified finite term does
not prove infinitude.

<a id="dkl-006"></a>

## DKL-006: represent sparse kill sets with a mask and exact list

**Priority:** complementary to DKL-001. **Disposition:** proposed.
**Evidence:** exact membership representation; memory arithmetic only.

The canonical q-bit rows still occupy substantial memory after their
offset copies are removed. At n = 14 each row contains at most 28 killed
residues, regardless of q. The newer clique engine already uses a small
hashed mask followed by an exact root list; see
[clique_gpu.py](../../clique-ladders/clique_gpu.py), constants near lines
691–695 and construction near lines 1984–2018.

For a canonical forbidden set H_q, set a 4096-bit mask at every
`h mod 4096`, and retain the exact h values. For a candidate residue t:

1. A clear bit at `t mod 4096` proves that t is not forbidden.
2. A set bit requires exact membership testing in H_q. A hash collision
   must never reject a candidate.

Use exact dense rows for small q if cheaper. For approximately 23,000
primes, 512 mask bytes plus at most 28 four-byte roots per prime amount
to roughly 14 MiB, compared with the historical 344 MiB full bit-table
figure. Counts, alignment and small-prime special cases add overhead.
This is a storage estimate, not a new allocation measurement.

Apply DKL-001's phase before this membership test. Derive the GPU lists
independently of the CPU square-root oracle, and enforce the actual root
capacity. A fixed 32-slot layout is safe from the `2n` bound only through
n = 16. Unlike adding a fold solely to stage 1a, this representation also
targets the later sieve's working set; its possible benefit is therefore
not restricted to the old 35% phase. It adds mask/list lookups and can
lose on some rows. No runtime gain, much less a one-day result, follows
from the byte ratio.

## One-day assessment and implementation obligations

[BENCHMARKS.md](../BENCHMARKS.md), lines 172–199, records the v4
`2.31e17 k/s` rate at **n = 13, q2 = 262144**, measured on a
campaign-shaped `2^41` j interval. It is a device measurement.
[score.py](../score.py), lines 56–58, freezes n = 10, 12 and 13 shapes,
with sieve depth 65536. None measures the actual n = 14 campaign.

At that historical device rate, a day covers `1.99584e22` of k-line,
ending near `3.56329e22` from C. The stored a(14) median is
`1.6797130530463832e23`; its `searched_empty_to` is **zero**.
Reaching that fixed depth from C takes **7.63 days**, or requires at
least a 7.63-fold rate improvement to fit 24 hours. This is not a new
conditional median. Under the same Poisson model, the actual conditional
median solves `E(M)-E(C)=log(2)` and lies farther out.

The documented 8.5-day remaining median estimate and the 98.6% model
probability below the current ceiling are historical forecast claims.
The four finds landed at model expected counts 2.47, 2.57, 1.54 and 2.48;
[RESULTS.md](../RESULTS.md), lines 125–147, reports a pooled optimism
factor of 2.26 with a wide interval. Neither the old unconditional
median nor a transplanted rate is a one-day guarantee.

The current segment spans only about 0.572 seconds at that old rate.
A larger factored wheel can change that substantially: price time to
close the segment and confirm leastness, not merely time to return a hit.
Do not multiply DKL-001, DKL-002 and DKL-003 as independent speedups.

Claude's later implementation should proceed in bounded stages:

1. Establish the actual n = 14 baseline and preserve the old fingerprints.
   Compare the supported single-fold alternatives as separate plans.
2. Implement and verify canonical-plus-phase tables before adding more
   fold primes. Recompute exact survivor counts and queue limits.
3. Consider the larger CRT/window representation only with its root,
   offset, index and complete-segment bounds written down.
4. Keep external coverage in **k or j=k/W**, not in the new folded u.
   The current API fully processes `[j0,j1)` across all offsets before
   returning sorted candidates. Preserve that contract, or version and
   migrate to an explicit partial-work/committed-boundary state.
   Floor any changed-wheel adoption to overlap, clip repeated counts,
   and never skip a remainder. `redenominate` is at launch lines 506–512.
5. Preserve promotion across completed classified intervals: the
   conditions are fixed and nested here, unlike a greedy clique.
   Longer verified runs settle every eligible open index. Near/census
   populations still depend on the production sieve.
6. Retain the current absolute ceiling initially. Multiplying the fold
   automatically increases `P*J_CEIL`; that is not permission to extend
   the certificate policy. Larger k may introduce prime factors needing
   recursive proofs and harder factorizations.
7. Test populated CPU/GPU parity, fold/unfold equivalence, offset seams,
   resumed versus uninterrupted streams, changes of wheel at promotion,
   strong-test pseudoprimes, known discoveries and certificate forgeries.
   Include primes above 65536: the old 32-bit q² bug shows why.
8. Record measured results or rejection against the stable DKL IDs in
   the existing optimization log and update the local index.

These are future obligations, not actions performed by Codex. They do
not authorize anyone other than the owner to start a campaign.

## Other mathematical paths examined

| Idea | Disposition |
|---|---|
| Force additional primes above n+1 into W | Impossible by this residue argument: k = 0 and k = ±1 modulo q all survive when q > n+1, since m+1 lies between 2 and n+1. The existing compulsory wheel is maximal in this sense. |
| Exploit k versus -k | The forms are symmetric, but the search already uses positive k only. This does not halve its existing domain. |
| Substitute t = k² and use a linear ladder | Exact as a predicate with the extra perfect-square constraint, but expanding the search to all t creates a much larger domain. No efficient leastness-preserving shortcut was established. |
| Sophie Germain exclusions | For n at least 9, forms exclude k = s² (s > 1), k = 2s² (s > 1), and k = 6s² (s >= 1), using m = 4, 1 and 9 respectively and `4t^4+1=(2t²-2t+1)(2t²+2t+1)`. These O(sqrt(K)) sets have negligible density at the present height; an extra test on every candidate is not justified as a major improvement. |
| Fold 17 into generation | Already implemented and measured in v4; not a new proposal. The earlier mistaken 1.06-fold estimate must not be repeated. |
| Fold a second prime with duplicated tables | Already priced and declined. DKL-001 changes its memory premise, and n = 14 changes the residue count. |
| Base-2 host screening and overlap | Already implemented; old host bottlenecks are not an additional multiplier on the current rate. |
| CRT-paired rows / generated later rounds | Existing unbuilt engineering proposals; their costs must be repriced after any new representation. |
| Repeated factorization of k during certification | Visible secondary implementation work, but discovery verification is too rare to establish a search-scale gain here. |

The report and its index are documentation only. Source, models, evidence,
checkpoints and measured ledgers remain unchanged by this review.
