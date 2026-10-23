# Decimal ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A305740 and A153431; mathematical
reductions, their proof obligations, and a handoff for possible implementation
by Claude. **Status:** analysis only; no optimization implemented.

This review follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex's role is
always static: no GPU use, hunt-module imports, oracle execution, tests,
benchmarks, campaigns, or engine changes. Reading source and saved JSON,
hashing files, and arithmetic on recorded values are the only operations used
for this review. Existing verification and performance results are attributed
to the repository; they were not rerun.

The main opportunity is **DEL-001**, a conditional exclusion of one complete
candidate class for A153431 a(17). It is a known but unbuilt proposal whose
original dependency on a moving sibling cursor has been replaced by a settled
term. Its exact work reduction is 25% under the existing wheel's complete CRT
enumeration. **DEL-002** identifies a separate forecasting issue: the same
knowledge that removes the class also removes its contribution to the
conditional odds. A 25% work saving must not automatically be advertised as a
25% reduction in the published median forecast.

## Evidence classes and source snapshot

| Label | Meaning in this review |
|---|---|
| **Proved** | An algebraic or coverage statement derived below. Where it uses a recorded least term, that dependency is explicit. |
| **Repository observation** | A value, source behavior, stored claim or historical measurement read from this checkout. It has not been independently executed or reverified by Codex. |
| **Model consequence** | A calculation inside the repository's Bateman–Horn/Poisson assumptions. It is not a proof about where the next prime run occurs. |
| **Unmeasured** | An implementation or elapsed-time hypothesis. No new runtime result is claimed. |
| **Donor rate** | A rate measured in another project. No donor rate is used to forecast this proposal. |

The inspected checkout had Git HEAD
`f8fdb200c56a54aa5e207c146882f7d2d7b87224`. HEAD alone does not identify the
working tree: root documentation had local changes and other project work was
present. The hashes below identify the actual reviewed engine and evidence
files. Source links are relative; line numbers are snapshot locators, and the
named symbol is the durable locator if code moves.

| Source | Snapshot SHA-256 |
|---|---|
| [decl_reference.py](../decl_reference.py) | `b1ce9c6666644b39e7e812e97140a41579da1155c5bce9fdba667f21e6b4c963` |
| [decl_search.py](../decl_search.py) | `bc4adfca6fc865071fbf83555702932f2f03a43104c25a882d172df67b573edc` |
| [decl_gpu.py](../decl_gpu.py) | `f5302045e72fadc978e09908ac1b9db4814bab9508a0c7ea17cdac8c61fa7b0b` |
| [decl_model.py](../decl_model.py) | `e8beb00ce682c70b404e94838bd74148da79181defcfb26266f0dbad7407a347` |
| [launch.py](../launch.py) | `6cbbd2842edebfdf17797702580e8a8976169d2c57a58fdd9730bb794b80e1f7` |
| [score.py](../score.py) | `abe35458adc616f228e901b33491f40a7771355891b68135b68326055e844f80` |
| [model_results.json](../model_results.json) | `bef74b2dd530415a8a3843b097637e5effe7d044b0c3c09bfbdb7852798cff49` |
| [A305740 a(18) evidence](../evidence/A305740_a18_1705184924533540483774741.json) | `b679f7d9369958bba847be63f6db93e45e4f61c7935b4ca2259ebe175d9d11c1` |

## Current search state and the meaning of the indices

A305740 asks for the smallest **k** for which `10^m*k + 1` is prime for
every exponent **m = 1..n**. A153431 asks for the smallest **m** for which
`m*10^k + 1` is prime for every exponent **k = 0..n**. Thus their indices
count different numbers of forms: n versus n + 1.

The unoptimized definition is in [decl_reference.py](../decl_reference.py),
`exponents`, `nforms`, `index_of`, `run_length`, and `first_x` (snapshot lines
181, 186, 193, 219 and 291). In particular, `run_length` returns the largest
**index** achieved; it does not demand that the run stop at the requested
index. A153431 can return -1 when the exponent-zero form is composite.
`first_x` asks for a run **at least** the requested index. Plateaus are valid.

The saved checkpoints read on 2026-10-20 contain:

| Family | Next open term | Reported contiguous boundary, exclusive | Work position | Carried previous-filter coverage |
|---|---|---:|---|---:|
| A305740 | a(19) | k = 1,763,320,915,600,480,167,930,999 | filter 19, period 2541, launch 0, unit 2261 | `cover_x = 1763330689510694071075308` |
| A153431 | a(17) | m = 77,995,803,506,947,091,585,820 | filter 17, period 798, launch 0, unit 4522 | `cover_x = 78084657236164392897720` |

Sources: [A305740 checkpoint](../campaign_checkpoint_a305740.json) and
[A153431 checkpoint](../campaign_checkpoint_a153431.json), fields `n`, `j`,
`u`, `k` and `cover_x` (snapshot lines 6 and 29–36). Their saved timestamps are
2026-09-29 03:13:11 and 2026-09-24 17:17:04, respectively. They are historical
saved state, not a claim that a process was observed running.

The checkpoint hashes at review time were
`8c48cab24b6a16850e0448cb4e9f317462498358239f059c5ac7ef83e9e221ef`
for A305740 and
`75e69dc6d7e078ef12e5e2d28ccbde53f6d986b0ea76d7654be678bb8f1467e1`
for A153431. Runtime checkpoints may be absent from a published clone.

Do not collapse `k`, `j * W`, and `cover_x` into one interchangeable
quantity. [launch.py](../launch.py), `state` and `swept_k` (lines 669 and 750),
stores a conservative segment boundary; `follow_frontier` (line 928) carries
the previous filter's classified line and floors the new work cursor onto its
period. Both observed launch cursors are zero, but the coverage justification
still has to survive a future plan change.

<a id="del-001"></a>

## DEL-001: remove the sibling-excluded class for A153431 a(17)

**Status:** proposed, not implemented. **Evidence:** proved conditional
pruning; repository-recorded prerequisite; unmeasured elapsed-time benefit.

### What is already known, and what changed

The repository records

**A305740 a(18) = 1,705,184,924,533,540,483,774,741.**

Call ten times this recorded term **B**:

**B = 17,051,849,245,335,404,837,747,410.**

B is a bound used in the proof, not a new name for either sequence's published
variable. The target remains A153431's **m**.

This is not a newly invented optimization. See
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), “Priced and declined,” item 5
(snapshot lines 765–794). Its 2026-09-28 proposal depended on an evolving
A305740 searched-empty cursor. The 2026-09-29 update explicitly says that the
objection has lapsed because a(18) is now a settled term. The same log still
marks the proposal unbuilt.

Current [launch.py](../launch.py), `sibling_floor` (line 222), implements the
other direction: it raises A305740's floor using a settled A153431 term. It
does not implement this A153431 exclusion or its endpoint. The current
[decl_search.py](../decl_search.py), `killed_residues` and `_xkills` (lines 125
and 158), describes divisibility by the forms alone. The current A153431
filter-17 plan includes prime 5 in its first CRT level
([decl_gpu.py](../decl_gpu.py), `MEASURED_PLANS`, line 583).

### Proof, including the endpoint

For any positive A153431 candidate **m** divisible by 10, its quotient
**m/10** satisfies A305740's condition at index 18 exactly when **m** satisfies
A153431's condition at index 17. Indeed, A153431's eighteen values are

`m + 1, m*10 + 1, ..., m*10^17 + 1`,

and A305740's eighteen values at the candidate **m/10** are

`10*(m/10) + 1, 10^2*(m/10) + 1, ..., 10^18*(m/10) + 1`.

These are the same integers in the same order. The relevant index is **18**,
not 17, on the A305740 side.

If `0 < m < B` and `10 | m`, then `m/10 < A305740(18)`. By the recorded
least-term claim, that quotient cannot satisfy all eighteen conditions.
Therefore **no positive multiple of 10 below B can be A153431 a(17)**.

At **m = B**, the quotient is the recorded A305740 a(18), so all eighteen
conditions do hold. Consequently

`A153431(17) <= B`,

and the empty interval for the divisible-by-10 class is **strictly below B**.
Rejecting the class at `m <= B` would delete a known valid endpoint.

An implementation can exhaust the reduced domain below B and then process B
explicitly through the normal independent verification and evidence path.
For a half-open interval API, either sweep `[floor, B)` and separately process
B, or use an exclusive upper bound of `B + 1` while special-casing B so that
the conditional exclusion does not reject it. Merely passing B as an
exclusive search limit does not inspect B.

This proof concerns the monotone predicate “run at least 17.” It does not
assume that the run stops there. The particular recorded A305740 endpoint
also has a factor-61 stopper at exponent 19, so its shifted A153431 run is
exactly 17 **if that stored evidence is accepted**. That extra fact is not
needed to justify the exclusion. Any earlier A153431 discovery still needs
its full run checked for riders.

### What the proof depends on

The [a(18) evidence record](../evidence/A305740_a18_1705184924533540483774741.json)
contains:

- `oeis_terms["18"]` and `run = 18` at lines 5–9;
- four verification flags and the stopper at lines 54–64;
- eighteen BLS75 certificates and `certificates_verified = true` at line 680;
- a `least_claim` at line 686, with monotone floor
  21,858,781,309,925,220,643,647, previous-filter coverage, the swept interval,
  wheel, sieve depth and unit.

The certificates support primality of the endpoint's values. **Primality
certificates alone do not prove leastness.** Excluding every smaller quotient
also depends on the recorded exhaustive coverage and the earlier term used
as its monotone floor, with their existing verification history. Codex has
read this chain of claims; it has not independently rerun or re-proved that
exhaustive search.

The future A153431 evidence should identify the exact sibling sequence,
index, value, evidence path and content hash, explain the shifted-form
identity, and distinguish “swept by this campaign” from “excluded by the
sibling's least-term claim.” The current `settled_term` loader at
[launch.py](../launch.py), line 198, reads a matching JSON value; that lookup
by itself is not certificate or coverage verification.

### Why the work reduction is exactly one quarter

Above the existing small-value exception zone, A153431 requires even **m**,
and the exponent-zero form rejects `m == 4 (mod 5)`. Its four remaining
classes modulo 10 are therefore

**0, 2, 6, 8 modulo 10.**

DEL-001 removes class 0 below B, leaving **2, 6, 8**. For complete CRT
enumeration with the same other wheel primes, each choice of those other
residues pairs with four residues before pruning and three afterward. This
is **25% fewer generated candidates**, or a **4/3 ideal work-rate ratio**,
at unchanged per-candidate cost. A partial interval or launch need not have
exactly that finite count ratio.

At the current forced unit 4522, the code's reduced coordinate has
`m = 4522 * x`. Since 4522 is 2 modulo 5, the existing forbidden residue is
`x == 2 (mod 5)` and the new conditional forbidden residue is
`x == 0 (mod 5)`. This coordinate statement is implementation notation;
the published candidate remains **m**. Do **not** multiply the forced unit
by 5: three classes survive, and restricting to multiples of 5 would select
the class this proposal excludes.

This reduction belongs in generation/the wheel or an equivalently early
domain restriction. Dropping the candidates only after full sieving does
not remove the corresponding sieve work.

### The one-day question

[RESULTS.md](../RESULTS.md), “In progress,” lines 315–325, gives a conditional
median near `m = 1.5e24` from the saved contiguous bound, approximately
**1.4 days / 34 hours** at a historical rate near `1.16e19 m/s`.
Those are repository model and measurement values, not new measurements.

For the **same fixed target depth**, ideal 25% less work changes 34 hours to
**25.5 hours**. Recomputing the frozen model from its saved constants gives
34.57 hours to its original median, or **25.93 hours** after the ideal 4/3
work-rate improvement; the arithmetic is specified under DEL-002. The
rounded 34-hour illustration would need another 6% in rate to fit 24 hours;
the more precise frozen-model illustration would need another **8%**. Both
are before implementation overhead or changing conditions, and neither is
a measured speedup.

That calculation is not a new conditional-median forecast: **DEL-002 below
changes the relevant probability calculation.** Furthermore, the project's
three A153431 finds at indices 14–16 landed 4.3–5.9 times their predicted
medians ([RESULTS.md](../RESULTS.md), lines 263–268). The sample is small, but
it is evidence against promising a one-day term from an uncorrected median.
The deterministic endpoint B remains useful regardless of the odds model.

### Claude implementation and validation handoff

These are future obligations for Claude; Codex has performed none of them.

1. **Represent a proof-backed search restriction explicitly.** Give the
   context a family, target index, strict upper endpoint B, excluded
   congruence class, sibling evidence identity and policy version. Missing,
   inconsistent or unverified prerequisites must fall back to the full
   search domain or produce a clear refusal; they must not silently prune.
   Keep ordinary mathematical divisibility separate from a restriction that
   depends on an earlier exhaustive search.
2. **Keep the oracle's original definition intact.** Do not “optimize”
   `decl_reference.run_length`, `first_x` or the oracle's divisibility sets
   by teaching them the exclusion. A separate proof/domain gate can use the
   theorem. The optimization log's older phrase “in all three engines” is
   not a reason to make the oracle stop independently defining the problem.
3. **Give the CPU and GPU distinct checks of the restriction.** The existing
   GPU module imports the CPU's `killed_residues`
   (`decl_gpu.py`, lines 124–126). Simply changing that shared function and
   obtaining CPU/GPU agreement would not independently validate the new
   conditional rule. Preserve a baseline full-definition sieve. Compare the
   optimized stream with that baseline intersected with the explicitly
   allowed domain, and separately compare true hits with the untouched
   oracle on tractable cases. Exercise the GPU wheel/coordinate
   construction independently of the CPU's direct candidate predicate.
4. **Cover the boundaries and indices.** Future tests need A153431 n = 17
   below B, exactly B and above B; other families and n values without the
   context; term-space and unit-space residues; unaligned split intervals;
   populated windows; and the small-prime equality exception. Use known
   small sibling terms to exhaustively check the general theorem without
   pretending to exhaust the production interval. A wrong sibling index
   and a forged bound must fail the restriction's validation.
5. **Preserve cursor meaning.** Removing one fourth of the first-level
   residues changes launch decomposition even if the period W is unchanged.
   Version the cursor policy with the restriction and its dependency. Do not
   reinterpret an old `u` under a new residue list. Adopt from a justified
   contiguous/previous-filter coverage boundary, floor to the new period,
   clip any overlap, and preserve the old coverage claims. The observed
   cursors have `u = 0`; that convenience does not replace a general
   migration rule. No existing checkpoint should be overwritten as part of
   this review.
6. **Keep promotion and census claims honest.** The removed candidates may
   have shorter runs, including near misses; their exclusion proves only
   failure of the target's predicate. Record the restricted census
   population instead of implying those runs were classified. On promotion,
   retire the filter-specific policy or explicitly prove its scope at the
   next filter. Do not carry a boundary beyond B on the strength of a rule
   that was proved only below B. Preserve exact rider classification for
   every retained discovery and the endpoint.
7. **Make changed fingerprints explicit.** The optimized raw survivor set
   is deliberately smaller; its fingerprint is not the old one.
   [score.py](../score.py), `SHAPES` line 65, currently freezes SCORE153 at
   count 8163 and xor 119430980700175536911810. Preserve a baseline shape for
   the original stream and add or deliberately refreeze a restriction-aware
   shape only after independent domain/parity checks justify the change.
   Include the endpoint/context in what the new shape identifies. A changed
   count must never be dismissed as an expected speed improvement without
   that proof.
8. **Only after correctness, measure the actual benefit.** Future
   measurements belong to Claude's implementation work, on the actual
   A153431 n = 17 restricted domain with exact work accounting. Record them
   in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), then update the
   [review index](README.md). Do not promote the 4/3 work ratio to a measured
   time ratio.

<a id="del-002"></a>

## DEL-002: condition the forecast on the removed class

**Status:** proposed model follow-up; not implemented. **Evidence:** exact
algebra within the existing density formula, followed by an explicitly
conjectural probability model. This does not claim an additional speedup.

[decl_model.py](../decl_model.py), `log_singular`, `_log_dens`, `expected`
and `quantile` (snapshot lines 82–140), models all A153431 candidates. Its
conditioning is a lower endpoint of an interval. It has no input expressing
“the divisible-by-10 class is empty up to B, with a guaranteed hit at B.”
The original scalar forecast must therefore not be reused unchanged as if
it already incorporated the new information.

For a fixed index n, compare A153431 at n with A305740 at n + 1. They each
have n + 1 forms. At every prime other than 2 and 5, shifting all exponents
by one multiplies the killed residues by an invertible constant, so the
killed counts agree. At 2 the singular-series factor for A153431 is half
the A305740 factor; at 5 it is four fifths. Consequently

`S(A153431, n) = (2/5) * S(A305740, n + 1)`.

The saved [model_results.json](../model_results.json), `singular_series`
entries at lines 21 and 153, give approximately 4,554,636,064.67 and
1,821,854,425.87 for the relevant pair, consistent with this ratio.

For A153431's candidate **m**, the modeled intensity of just the
divisible-by-10 class is the A305740 intensity evaluated at **m/10**, divided
by 10 to convert the interval length. The log denominators are identical
under the shifted-form identity. The singular-series ratio above therefore
makes this class's intensity **one quarter** of the total A153431 intensity
in the current model, not zero.

Under the additional usual assumption that events in the residue classes
can be modeled as independent Poisson processes, learning that this class
has no hits below B leaves the other three classes' intensity at **three
quarters** of the original total. For the saved contiguous lower bound and
`m < B`, the class-conditioned survival probability is thus

`exp(-(3/4) * E_A153431(saved_bound, m))`.

At B there is a guaranteed admissible candidate. The remaining survival
mass lands at that endpoint rather than continuing as the old unbounded
Poisson tail. This is a conditional forecast incorporating the sibling
claim; it is not a proof that the Poisson assumptions are correct.

A future model should solve `(3/4) * E = log(2)` for a median below B, if one
exists, and otherwise return B, with the endpoint mass made explicit. Keep
the published unconditional model available for validation and historical
comparison. Check that its class densities sum to the original intensity
and that conditioning is not accidentally applied twice.

### Static arithmetic for the recorded cursor

The following calculation freezes the recorded A153431 cursor
`C = 77995803506947091585820`, the saved singular series
`S = 1821854425.8687186`, and the historical rate `1.16e19 m/s`. It integrates

`E(C, M) = integral_C^M S / product(j = 0..17, log(10^j*t + 1)) dt`.

Codex independently evaluated this scalar formula using a 3,000-point
log-spaced trapezoid, matching the numerical scheme described in
`decl_model.expected`, followed by bisection on the median equation. This
was plain arithmetic on recorded constants: no project model, hunt module,
oracle or engine was imported or executed. Floating-point results are
approximate model outputs, not new search measurements.

| Frozen scenario | Median candidate m | Remaining distance from C | Hours at historical rate | Hours at ideal 4/3 rate |
|---|---:|---:|---:|---:|
| Original interval-only model, `E = log(2)` | `1.52166e24` | `1.44367e24` | 34.57 | 25.93 |
| Class-conditioned model, `(3/4)*E = log(2)` | `2.15156e24` | `2.07356e24` | 49.65 | **37.24** |

The first row's final column is a fixed-depth comparison, not the forecast
after learning the excluded class is empty. The second row makes that
conditioning explicit. Within these assumptions, even an ideal 4/3 runtime
improvement gives a median near **37 hours**, so it does not establish a
one-day median. A model using the complete historical data could differ
from both rows.

At B the same integration gives `E(C, B) ~= 4.72825`, leaving
`exp(-(3/4)*E(C, B)) ~= 0.0288` of the modeled probability at the guaranteed
endpoint. This approximately 2.9% point mass describes a truncated
conditional model. It is not an exact probability assigned to a fixed
mathematical sequence.

This explains why the 34-hour to 25–26-hour arithmetic in DEL-001 is only a
fixed-distance illustration. The reduced domain takes less work per unit
of line, but the original forecast assigned some of its success probability
to a class now known to contain no successes. The revised median depth can
move outward. Claims about the chance of a result within one day need this
conditioning as well as an eventual measured rate. The rigorous domain
exclusion remains beneficial compared with actually searching that same
known-empty class.

## Coverage of the other mathematical opportunities

| Opportunity examined | Finding and disposition |
|---|---|
| Decimal residue orbits and saturation | Already central to the engine. For primes other than 2 and 5, the killed count is the smaller of the number of forms and `ord_q(10)`. `decl_reference.py`, `w_count`, `g2b_killed_set_three_ways` (line 412), and `decl_search.py`, `_xkills` (line 158), explicitly implement/check this. Replacing an exponent-by-exponent account by the order formula is not a new pruning result. |
| More forced divisors at the current filters | Existing forcing is exact for this argument: A305740 n = 19 has unit 2261; A153431 n = 17 has unit 4522. A prime is forced only when all its nonzero classes are killed. Small order alone is insufficient. `forced_unit` and `assert_unit` are at `decl_search.py` lines 167 and 198. Forcing q does not force q squared, and the factorization of one successful term does not prove that its factors divide every future term. No additional forced divisor was established here. |
| Sibling floors for A305740 | Already implemented by `launch.py`, `sibling_floor` and `x_floor` (lines 222 and 173). The floor for A305740 n = 19 would use A153431 a(18), which is not settled in this snapshot. A153431 a(17) belongs to the A305740 n = 18 relation, not n = 19. The index shift cannot be ignored to claim a new floor. |
| Equality and plateau reuse | Already supported. `g2d_nesting_and_shift` (`decl_reference.py`, line 499) checks nesting and shifts; `record_discovery` and `follow_frontier` (`launch.py`, lines 833 and 928) classify riders and carry the classified line. A305740 a(16) equals A153431 a(15) divided by 10 in the recorded results. Treating each n as an exact-length search or requiring strict growth would be a correctness regression. |
| Joint sweep of the two families | Mathematically sound through the same shift, but already priced and declined in `OPTIMIZATION_LOG.md`, item 1 at line 742. It adds shared coverage bookkeeping and its benefit depends on overlap of both searches. DEL-001 obtains the presently useful exclusion from a completed claim without requiring a simultaneous campaign. No new large benefit for A305740 a(19) is established. |
| Larger wheels, wider windows, instruction or occupancy tuning | The log contains extensive work on these. Runtime profiling and hardware tuning are outside this static mathematical review. Their historical rates are not new mathematical eliminations and are not added to DEL-001's work ratio. |

For A305740 a(19), the repository's current model gives approximately
**51 days** to its median at a historical `1.07e19 k/s`
([RESULTS.md](../RESULTS.md), line 317). This review establishes no new
mathematical reduction large enough to turn that search into a one-day
median. That is a bounded audit result, not a claim that all possible
algorithms have been exhausted.

## Handoff state

DEL-001 is the concrete implementation candidate. DEL-002 should accompany
any new probability or one-day claim made for it. Both remain proposed.
The independent oracle, engines, checkpoint files, evidence, scores and
optimization log were left unchanged by this review. Claude should record
future implementation and validation under these stable IDs and update
[README.md](README.md) with links to the actual outcomes.
