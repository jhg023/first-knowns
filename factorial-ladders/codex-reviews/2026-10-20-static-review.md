# Factorial ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** both primary families, A177013 and
A177014, and their derived entry A226935. **Status:** analysis and handoff,
not implementation. Workflow: [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

Three reviewers examined only this project, with complementary mathematical,
implementation and evidence checks. Source, documentation, saved evidence
and checkpoints were read; hashes and small arithmetic expressions were
computed. No project modules, models, oracles, primality experiments, tests,
benchmarks, campaigns or GPU operations were executed.

## Assessment

**No substantial missed search-space reduction was established.** This
engine already implements the factored CRT wheel, period-window sieve,
sparse tail representation, wide survivor record and carried classification
that are major opportunities in some older projects. Counting these again
as possible speedup factors would be misleading.

The new mathematical result is **FAC-001**, a rigorous finite-collision
bound on the truncated singular series. At the actual n=19 frontier it
limits the omitted logarithmic correction to approximately
`[-0.000903, +0.001051]`. It improves the justification of model arithmetic;
it cannot turn a nine-day median into a one-day hunt.

**FAC-004** identifies a concrete newer sibling transfer: reuse period
coordinates inside the later in-block rounds. Its donor measured modest
gains on the wide record, with regressions on some other shapes.
Destination performance remains unmeasured.

**FAC-002** identifies an incompleteness in the planner's search for a wheel,
without asserting that a better current wheel exists. **FAC-003** revisits
the already documented five-hour confirmation segments and explains how to
change their representation without losing coverage. It can reduce waiting
for a leastness claim, but not remove the underlying nine or ten days of
modelled search.

Throughout this report, a **proved** work or error bound is distinguished
from an **observed source/data** fact, a **historical measurement**, an
**unmeasured hypothesis**, or a **model-derived estimate**.

## Definition and current search

For sign s, the primary term is the least positive m such that

`k!*m+s` is prime for every `k = 1..n`.

A177013 uses s=-1; A177014 uses s=+1. The predicate is **at least n**:
plateaus and riders are valid, with no required composite at n+1 in the
definition. For A226935, induction in
`p(i)=i*p(i-1)-(i-1)` gives `p(i)=i!*(p(1)-1)+1`, so
**A226935(n)=A177014(n)+1**. This exact rider is already implemented and
independently checked by the recurrence in the reference oracle.

| Family | Last recorded term | Open term | Saved contiguous boundary C |
|---|---:|---|---:|
| A177013 | a(18)=1639203889936938872760 | a(19) | 5409800307213547425180 |
| A177014 | a(18)=30911690086525348609590 | a(19) | 31481127088965583209180 |
| A226935 | a(18)=30911690086525348609591 | a(19) | The A177014 boundary shifted by one |

The boundaries describe exclusion **below C**, subject to the recorded
coverage chain. They are not observations of a live process or a new
independent verification. Relevant evidence includes the two
[negative-family](../evidence/A177013_a18_1639203889936938872760.json) and
[positive-family](../evidence/A177014_a18_30911690086525348609590.json)
a(18) files; [RESULTS.md](../RESULTS.md), lines 251–268, explains the
leastness basis separately from the primality certificates.

Both checkpoints specify n=19, q2=32768, unit 6,
`W=32589158477190044730` in m, and 224 periods per segment. The negative
family has `j=166`, `u=24444` of 181350 launches; the positive family
has `j=966`, `u=0`. The negative family's 13.479% partial work is scattered
through its segment: it does **not** add 13.479% of that segment to C.
Its saved pending classifications must be preserved or safely replayed.
The saved keys are respectively
`a177013-v3-p2-seg32-pbd224-cpl37w38` and
`a177014-v3-p2-seg32-pbd224-cpl37w38`.

For prime q the forbidden set is

`K_q(n,s)={-s*(k!)^(-1) mod q : 1 <= k <= min(n,q-1)}`.

Deduplicate it. For k>=q the form is s modulo q and contributes no root.
The set saturates at n=q-1 and grows monotonically with n. The size is
sign-independent, but the actual signed sets differ.

The compulsory unit is already complete: 2 and 3 are forced outside the
small-value exception zone, and no prime q>=5 is forced. Wilson's theorem
gives `(q-2)! = 1! mod q`, so the q-1 factorials have a duplicate and cannot
cover all nonzero residues. More powers of 2 or 3 are not forced either.
The sieve requires the smallest value m+s to exceed its largest tested
prime; the direct oracle retains the exceptional prefix.

At the present height primality certificates are essential:
`k_proof(n,s)=(MR_VALID_BELOW-1-s)//n!+1` is only about 2.7e7 at n=19.
The ceiling is m<1e40. The existing certificate construction factors m once
and merges the factorial's small factors, using N-1 for the positive sign
and N+1 for the negative sign, with recursive subproof support where needed.
None of the proposals changes that certificate policy.

## Snapshot and inspected sources

Git HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`, with existing
documentation modifications and an untracked project. Hashes pin the
reviewed bytes; function names and snapshot line numbers identify the
relevant code even if documentation later moves.

| File | SHA-256 |
|---|---|
| [fladder_reference.py](../fladder_reference.py) | `44A1907E1EFAC85B4C8C4B0B8285B262C06C6D6F197B7DC34B235E9D83E5D6C9` |
| [fladder_search.py](../fladder_search.py) | `12F357589D477934F9EFC8E2DC4334DEDA421E8E0F16FDB74164FF3F6EC7CADF` |
| [fladder_gpu.py](../fladder_gpu.py) | `1A1A2C5A639488E0BBB75585C7E06D29857F24917DD47641E8E5723BBD0C7668` |
| [fladder_model.py](../fladder_model.py) | `54849F33C80738FEFA0A6AFC4D98A89E1EAA264A5EF11857A01AD5B9A883100B` |
| [launch.py](../launch.py) | `1D11D42DCF6272F57F91FEB51E24DA9166DD4B5B8AF80EAE6844690C27EA8D30` |
| [score.py](../score.py) | `238CA3BC6E0E885085B38C7C54455ABFF35BA276F5DFA71C474DB5EE69D92A96` |
| [campaign_checkpoint_a177013.json](../campaign_checkpoint_a177013.json) | `4A8D9180C56E8904E390CD955AE32C294EA489B9468FDF7118FB7AAF92597340` |
| [campaign_checkpoint_a177014.json](../campaign_checkpoint_a177014.json) | `70CAB792D3AEF2B041725691BD7C64B3E48A8B14D07AFD7AB0268A8211C4C1EC` |
| [model_results.json](../model_results.json) | `0C51254415C6CF0E249A0167205DB1E239A06015109BC102AE530980A0435BA5` |
| [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) | `42E52DFB7FE11EA5E8D265AEBEF705BD7EB121AE4C9AC005ED0BC5CFE339A92D` |

The review followed the five Python roles, model, optimization history,
benchmark shapes, evidence/checkpoints and relevant `huntlib` checkpoint,
primality, evidence and certificate contracts.

<a id="fac-001"></a>

## FAC-001: a finite product controls every exceptional tail prime

**Priority:** mathematical assurance. **Disposition:** new proposal.
**Evidence:** proved bound; no numerical model execution or sweep gain.

`fladder_model.log_singular`, near line 122, sums primes below
`QMAX=200000` without a quantitative remainder. For q>n, all factorial
multipliers are invertible. A collision `i! = j! mod q` occurs precisely
when q divides the integer `j!/i!-1`. Define

`D_n = product_{1 <= i < j <= n}(j!/i!-1)`.

Every factor is positive. For q>n not dividing D_n, exactly n distinct
roots occur. If the factorials have collision-class sizes c_1,c_2,...,
their root deficit is `n-w_q=sum(c_i-1)`. Each class contributes at least
`binomial(c_i,2)` to the q-adic valuation of D_n. Therefore

`0 <= n-w_q <= v_q(D_n)`.

Let

`A_q=(1-w_q/q)/(1-1/q)^n`, `G_q=(1-n/q)/(1-1/q)^n`.

For an integer cutoff Q>n, the omitted logarithmic correction decomposes
into a negative generic tail and a positive finite collision correction:

`log(A_q/G_q)=log(1+(n-w_q)/(q-n))`.

Consequently,

`0 <= sum_{q>Q} log(A_q/G_q) <= log(D_n)/((Q-n)*log Q)`.

This follows by bounding the logarithm by its argument, using
`n-w_q <= v_q(D_n)`, and using
`sum v_q(D_n)*log q <= log D_n`. It needs no factorization of D_n.
For the generic part, expand the logarithms:

`log G_q = -sum_{r>=2}(n^r-n)/(r*q^r)`.

Bounding `1/r <= 1/2`, summing the geometric series, and majorizing the
prime sum by `sum_{j>Q}1/j² <= 1/Q` gives

`-n²/(2*(Q-n)) <= sum_{q>Q} log G_q <= 0`.

An easily computed upper bound avoids even forming D_n:

`log D_n < sum_{t=2}^n (t-1)*(n-t+1)*log t`.

At n=19, the latter sum is about 2564.37. At Q=200000 the omitted
logarithmic contribution therefore lies in

**`[-0.000902586, +0.00105055]`.**

The cutoff is composite, so the source's primes-below-Q convention
introduces no endpoint prime. The multiplicative singular-series error
is bounded by exponentiating these endpoints, roughly -0.0903% to
+0.1051%. Numerical rounding and integral discretization errors require
separate treatment. This bound concerns the singular series, not the
truth of the prime-tuple or Poisson heuristic.

An optional exact acceleration factors the collision integers, applies
their exceptional Euler corrections, and handles the generic tail
separately. At current n this is unlikely to be worth complicating the
code merely for speed: the simple bound already makes truncation much
smaller than forecast uncertainty. Keep the direct finite-prime product
as an independent comparison if introducing an accelerated version.

Claude can add an explicit remainder interval to model output and compare
it at several cutoffs, including cutoffs that are themselves prime.
Do not represent empirical agreement on a handful of first occurrences
as a proof of the probability model.

The model introduction also says saturation guarantees `S(n+1)>S(n)`.
Its stated argument establishes factors greater than one at saturated
primes, but other prime factors can be less than one. A general growth
theorem needs a bound on their full product. G12's finite checks support
the checked indices, not that unrestricted assertion. This does not
invalidate the explicitly computed current singular series.

<a id="fac-002"></a>

## FAC-002: the wheel search is restricted to density-ordered prefixes

**Priority:** optional algorithm investigation. **Disposition:** proposed;
no better n=19 wheel demonstrated. **Evidence:** source observation and
an exact way to compare work counts.

`fladder_gpu.wheel_plan`, lines 411–465, ranks primes by
`-log(keep(q))/log(q)` and tests prefixes of that order. It does not solve
the complete subset problem. `_split_levels` can search non-contiguous
level assignments for a chosen set, which is a different question.

Density ordering is appropriate intuition, but its prefix restriction
does not prove optimality under integer period, residue-count, level-size
and segment bounds. A failed extra prime can make a swap or a non-prefix
subset worthwhile. The current source does not examine all such choices.

For a selected set S of optional primes, the exact wheel period and number
of CRT classes are

`P_S=product_{q in S} q`, `R_S=product_{q in S}(q-w_q)`.

CRT proves `R_S/P_S` is the generated density in unit coordinates. A
bounded subset or branch-and-bound planner can retain a Pareto set of
feasible period/density/level-size/window choices instead of only the
prefix winner. One can prune using remaining log-density improvement and
the monotone product bounds. This is plan construction, not an extra
condition on eligible m.

Do not optimize density alone: a larger period increases confirmation
delay, may force the wider record, and can worsen parallel enumeration.
The current wheel contains all optional primes through 53 and is already
strong; the next contiguous prime cannot simply be appended within the
existing representation. No replacement set or predicted speed factor
has been established here. A future planner should reject this avenue
if its feasible frontier contains no materially better complete plan.

Any accepted change must preserve the exact survivor set at fixed sieve
depth. Retain the dense independent CPU engine, direct oracle, old frozen
score shapes and full-period cross-wheel comparison. Check every prime
is in exactly the intended wheel or sieve stage, with normalization of
empty middle levels, residue counts, u32 CRT factors, u64 intermediates,
wide period fields and queue capacities. Existing parity cannot justify
an unchecked new level shape.

<a id="fac-003"></a>

## FAC-003: shorter segments improve confirmation latency, not density

**Priority:** practical follow-up if resuming. **Disposition:** already
documented, not a new discovery. **Evidence:** exact interval partition;
future throughput unmeasured.

[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), open item 5 at lines
608–615, already proposes comparing n=19 at 224 versus 56 periods.
The reason remains valid: the current segment has length

`S=224*W=7299971498890570019520`,

about **5.336 hours** at the stored 3.8e17 m/s. A candidate found early in
its residue-ordered traversal cannot be declared least until every lower
candidate has been ruled out. Four 56-period windows partition exactly
the same interval; shorter windows need not change any mathematical
eligibility condition.

The constructor currently requires the allocated `pb` to be a multiple
of 32 between 32 and 256 (`fladder_gpu.py`, near line 1617).
The log's proposed 56 is therefore a **live interval width**, not a valid
direct constructor argument. Supporting it needs, for example, a
64-period allocation with explicit clipping, or a deliberate choice of
an already supported width such as 64. Re-derive the checkpoint and
segment contract for whichever option is implemented.

At unchanged throughput the maximum wait falls by about four hours.
There may be a throughput loss, and fixed overhead is repeated. Measure
the complete pipeline and time to confirmed leastness; do not compare
only a few window-kernel calls. The shorter width changes neither the
singular series nor the nominal line that must be searched for a median.

For an existing partial segment, the safe simple migration is to retain
the old format until its segment closes, or restart from its committed
absolute boundary using a versioned new plan. Preserve discoveries and
handle replayed pending/census entries explicitly. The old `u` is a
launch index for the old enumeration: copying it into a new window or
level decomposition skips unclassified candidates.

`launch.config_key` at line 350 describes the plan/launch decomposition.
Its comments promise checks of unit, W, depth and segment width, but
`load` at line 880 retains only n and W for the assertions near lines
698–709. A same-W change of level split, width or launch enumeration
therefore needs a complete enumeration fingerprint or explicit versioned
adoption; the period check alone is insufficient. This is an obligation
for future changes, not evidence that the present checkpoint is corrupt.
`follow_frontier`
at line 1086 already carries completed classification to the next nested
filter and floors its adoption to overlap a changed wheel. Preserve that
behavior. Carried leastness is distinct from raw-sieve census continuity,
which changes with filter/depth. A cap-limited run classification must
not be treated as proof of a composite stopping value.

In particular, n=18 to n=19 lowers q2 from 65536 to 32768. The source's
claim that the new raw survivor set is a subset is then too strong.
The correct discovery argument is that every genuine longer run survives
the old shorter-filter sieve above its exception floor and was classified.
It preserves eligible discoveries even when the new raw stream is larger
at some residues.

Future validation should compare resumed and uninterrupted streams,
all partial-window seams, pending candidates, duplicate narration and
census accounting. A populated cross-wheel comparison must cover an
identical absolute interval on both record formats. The production
oracle still evaluates the original factorial forms.

<a id="fac-004"></a>

## FAC-004: keep later rounds in the window's coordinates

**Priority:** most concrete unbuilt runtime transfer found here.
**Disposition:** proposed donor transfer. **Evidence:** exact equivalence;
modest historical donor gains, destination unmeasured.

`fladder_gpu.py`, lines 2052–2065 and 2089–2104, builds later in-block
tests through `lit_prefix`, reconstructing an offset and performing
modular reductions. The wide record also loads a per-period modular term.
The current project does not implement the newer `ROUND_WINDOW` route
described in [clique-ladders' log](../../clique-ladders/OPTIMIZATION_LOG.md),
lines 528–552.

The equivalence applies to factorial roots without any change to the
predicate. In unit coordinates write `z=m/6=Wp*(j0+j)+r`. Here the
forbidden roots must also be in unit coordinates:
`K'_q={-s*(6*k!)^(-1) mod q : k<q, k<=n}`.
For a squarefree group Q, let K'_Q be the residues z for which
`z mod q in K'_q` for **at least one** prime q dividing Q.
For `gcd(Q,Wp)=1`, put `d=Wp^(-1) mod Q`.
Membership in this forbidden set is equivalent to

`j0+j+d*r mod Q in d*K'_Q mod Q`.

Thus later rounds can query the same kind of periodic pattern as the
first window, instead of reducing the reconstructed candidate each time.
The factorial engine's `window_patterns`, lines 1152–1189, already
constructs that transformed forbidden pattern.

In the factored CRT representation,
`r=r1+W1*(A-D)+b*Wp`, where b corrects a borrowed period. Precompute
`x0=(r1+W1*A)*d mod Q` and `ne=j0-W1*D*d mod Q`; the period-pattern bit is at
`x0+ne+b+j`, with reduction/padding according to the group modulus.
The borrow bit is essential, including after queue compaction, overflow
handling and reconstruction. Dropping it loses the equivalence.

The donor measured approximately 1.08–1.10× on selected wide-record
shapes, not on these factorial campaigns. Its scalar u16 row version
regressed to 0.87×; grouped 16-byte loads were necessary, and some narrow
shapes still regressed to approximately 0.90–0.91×. This is evidence for
a bounded wide-record experiment, not a universal improvement.

The donor stores the borrow in bit 15 of a compact queue index and guards
`spb*tpb <= 2^15` and group moduli below `2^15`; see
[clique_gpu.py](../../clique-ladders/clique_gpu.py), near lines 1440–1445,
1545 and 2289–2291. Re-derive those bounds for factorial plans before
copying the encoding. Per-residue rows require approximately
`R1*16*ceil(padded_round_slots/8)` bytes, in addition to block rows and
patterns. Memory growth and extra loads can erase the arithmetic saving.

Claude should first add this as an explicit alternate wide-record plan,
then compare complete populated streams and the whole n=19 pipeline
for both signs at q2=32768 and 224 periods. Retain the existing n=17/18
fingerprints. G18's compilation of n=19–21 is not a frozen n=19 work
fingerprint or a performance measurement. Reject the transfer if its
complete-segment benefit is absent; do not extrapolate the donor ratio
or multiply it by other proposals that remove the same repeated work.

## One-day assessment

[BENCHMARKS.md](../BENCHMARKS.md), lines 66–94, and the optimization log's
campaign summary distinguish several rates: the historical n=19 paired
device rate is approximately **3.8e17 m/s**; the negative family's
40-minute partial work records about 4.1e17; the positive family had
not yet swept n=19. The partial work rate is not extra contiguous
coverage. The n=18 long-run pipeline was approximately 0.90–0.91 of its
harness figure, with that gap not fully attributed.

At 3.8e17, one day is 3.2832e22 of nominal work. With the saved partial
progress and old 224-period segments, absent a discovery/promotion, both
families close four more segments in a day:

| Family | Approximate time for four closures | New contiguous boundary |
|---|---:|---:|
| A177013 | 20.63 h | 34609686302775827503260 |
| A177014 | 21.34 h | 60681013084527863287260 |

This arithmetic assumes work is proportional to the remaining launches;
it is not a measurement or new forecast. Work after the fourth closure
remains partial.

The existing **conditional** medians in [RESULTS.md](../RESULTS.md),
lines 331–350, are rounded to 3.0e23 and 3.6e23 from the respective
bounds. At the stored rate, fixed-distance arithmetic gives about
215.3 hours and 240.1 hours before rounding up to a closed segment.
Thus roughly **9.0× and 10.0×** are needed to bring those stated depths
within a day; the old segment layout adds further confirmation cost.
These are thresholds based on rounded published estimates, not model
calculations performed in this review.

The same existing report gives one-day discovery probabilities of about
12% and 9%, and week probabilities of 44% and 41%. A low probability is
not impossibility; a median is not a guaranteed upper or lower bound.
Those continuous-depth probabilities are not probabilities of a confirmed
least term by the deadline: that question uses the last closed boundary.
No adjusted probabilities were computed in this review.
The project's own fourteen searched draws have mean model expected count
1.10. Do not mechanically apply another project's blanket 2.5-fold
correction, or treat these medians as literal mathematical floors.
The saved `model_results.json` is the original frontier forecast, not a
replacement for the later conditional figures in RESULTS.

Neither the sub-percent tail bound, a plausible wheel-planner adjustment,
nor several hours less confirmation delay supports the required
nine-to-tenfold throughput improvement.

## Other avenues checked and handoff order

| Avenue | Conclusion |
|---|---|
| Force more primes or prime powers into the unit | The Wilson collision argument excludes additional forced primes. Squarefree forcing cannot justify powers. |
| Use the opposite sign's search as coverage | `K_q(n,+)=-K_q(n,-)` equates densities, not positive solutions. Reflecting m gives negative arguments; it does not halve either positive search or transfer a least term. |
| Derive A226935 separately | Already an exact rider. A positive-family discovery settles it without another hunt. |
| Carry a completed segment across a promotion | Already implemented, with nested conditions and direct run classification. |
| Transfer a modern period-window or sparse-tail engine | Both main representations are already present. FAC-004 isolates a later refinement absent here; no multiplier for the original window engine may be applied again. |
| Use one factorization of m for all certificates | Already implemented for both signs. |
| Perfect-power/factorization subfamilies of m | Some sparse values are algebraically composite, but no dense new exclusion or efficient replacement enumeration was found. |
| Wider record, larger launch batches, 64-bit window words, period-sorted queues | Already priced or listed in the log. Their individual percentages and overlapping phase costs do not establish a large mathematical reduction. |
| Append another wheel prime | Requires satisfying every representation and confirmation bound; not a free density gain. FAC-002 first asks whether a valid alternative subset exists. |
| Reduce inverse-factorial setup work | `killed_residues` can use one inverse at t=min(n,q-1) and the recurrence `(k-1)!^(-1)=k*(k!)^(-1) mod q`, instead of one inverse per multiplier. Exact, but setup-only; keep the oracle's direct divisibility walk independent. |

Claude's sensible order is to document FAC-001's error interval, then
price FAC-004 and the already known shorter-window proposal at the actual
n=19 filter if this project is resumed. Investigate FAC-002 only as a bounded
plan search with exact cost inputs and explicit rejection criteria.
Preserve all existing correctness anchors and report any new measurements
against these finding IDs. These future validation obligations do not
authorize a hunt start; the owner controls campaigns.

Only review Markdown and navigation documentation changed. Engines,
models, evidence, checkpoints and benchmark ledgers were left intact.
