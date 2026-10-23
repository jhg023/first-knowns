# LCM ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A078502, A074200, A093554 and A093553.
**Status:** mathematical analysis and implementation handoff.
Workflow: [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

Three reviewers examined only this project, with complementary mathematical,
implementation and evidence checks. Sources, documents, checkpoints and
evidence were read; source hashes and lightweight arithmetic were computed.
No project engines, models, oracles, primality experiments, tests,
benchmarks, campaigns or GPU operations were executed.

## Assessment

**No substantial speedup sufficient to make the current median searches
one-day jobs has been established.** The most concrete new mathematical
lead is **LCM-001**: every prime's forbidden residues become one short
interval after a modular scaling. It can replace a generic exact root-list
lookup, especially behind the existing cheap mask, without changing the
candidate stream. Whether that saves runtime is unmeasured.

**LCM-002** gives a monotone description of the total forced divisor,
despite the nonmonotone quotient unit. It clarifies the already documented
opportunity to carry coverage across promotions. That opportunity requires
additional classification: the present launcher caps ordinary runs at the
old filter, so merely copying a boundary would be unsound.

**LCM-003** is a modest donor transfer for later sieve rounds. **LCM-004**
rigorously bounds a small singular-series truncation error. None provides
evidence for the roughly 11-fold improvement needed for A074200's current
conditional median, or the roughly 364-fold improvement needed for
A078502's. The primary engine already has the major CRT, period-window,
sparse-mask, wide-record and subset-wheel improvements.

**LCM-005** supplies a concrete decomposition for the already-open wheel-67
idea under relaxed table limits, without claiming a faster complete plan.
**LCM-006** identifies a custom-unit validation gap; current default plans
use squarefree units and are not shown to be affected.

Labels used below distinguish **proved** mathematical claims,
**observed source/data**, **previously measured here**, **measured in a
related project**, **unmeasured hypotheses**, and **model-derived estimates**.

## Definitions, evidence and current coverage

Write L(n)=lcm(1,...,n). A078502 asks for the least positive N with N/k-1
prime for every k=1..n. A074200 asks for the least positive m with m/k+1
prime over the same indices. Integrality forces L(n) to divide the term.
For a fixed filter the engine's quotient is x=term/L(n), and its forms are
`(L(n)/k)*x+s`, with s=-1 or +1.

The definition is **at least n**, not exactly n. Riders and plateaus count.
The direct oracle's `run_length_N` also checks divisibility, so extending a
run requires more than continuing a fixed multiplier list. Substitution
in the two derived definitions gives A093554(n)=A078502(n)-1 and
A093553(n)=A074200(n)+1. These identities are already implemented.

| Entry | Last recorded term | Open term | Current exclusion |
|---|---:|---|---|
| A078502 | a(18)=a(19)=52270101840951834355676160000 | a(20) | Monotonicity and the known term's rung-20 stopper; no completed n20 segment |
| A093554 | a(18)=a(19)=52270101840951834355676159999 | a(20) | A078502 shifted by -1 |
| A074200 | a(18)=246823048779050778944771141280 | a(19) | No eligible m below 511330427374470630698663892000 |
| A093553 | a(18)=246823048779050778944771141281 | a(19) | A074200's exclusion shifted by +1 |

The [A078502 evidence](../evidence/A078502_a18_52270101840951834355676160000.json),
lines 4–17, records a run of 19 found at filter 18; lines 68–71 record
the rung-20 composite with factor 233. The
[A074200 evidence](../evidence/A074200_a18_246823048779050778944771141280.json),
lines 4–15 and 64–67, records an exact run of 18 and a rung-19 composite
with factor 109. Both have complete stored certificates and no unproved
values. Their least-claim fields begin at lines 1428 and 644 respectively.

[RESULTS.md](../RESULTS.md), its opening verification paragraphs and
least-claim section, records historical independent checks of these
certificates and the coverage chain. Reading these records is not a fresh
independent verification. Primality certificates establish eligibility;
minimality additionally depends on the recorded exhaustive coverage.

| Saved checkpoint | n | L(n) | unit | q2 | W in quotient x | j, u | Segment |
|---|---:|---:|---:|---:|---:|---|---|
| [A074200](../campaign_checkpoint_a074200.json) | 19 | 232792560 | 6 | 32768 | 2539314151841498430 | 865, 87333 / 120960 launches | 224 periods, v2 |
| [A078502](../campaign_checkpoint_a078502.json) | 20 | 232792560 | 30 | 16384 | 2539314151841498430 | 88, 3801 / 14391 launches | 107 periods, v1 |

A074200's saved contiguous quotient boundary is
`C=2196506741342896141950`; multiplying by L gives the term bound above.
The 72.20% partial segment does not extend C. A078502's saved boundary
`223459645362051861840` is below its monotonicity floor
`224535104734239936000`: its partial work establishes no new n20 interval.
The current v2 launcher explicitly adopts its v1 checkpoint, discards
the old partial enumeration and pending records, and replays from j=88;
its n20 plan uses 216 live periods, not the saved v1 width of 107.
See checkpoint headers and `launch._adopt`, lines 724–769.

For prime q, put h=q^e, where e=v_q(L), and w=floor(n/h). For q>n this
means h=1 and w=n. Exactly those k divisible by h contribute a root,
giving w roots. The current forced unit contains precisely the primes
with w=q-1; the special small-value exceptions are retained in the oracle.
The sieve's safe floor is
`x > floor((q2-s)/(L/n))`, as in `lcml_search.k_floor`, lines 136–149.

Both current filters have proof crossing approximately x=1.42e16, obtained
from `(MR_VALID_BELOW-1-s)//L(n)+1`. Their current heights are above it.
Discoveries use certificates from the factorization of the quotient and
the smooth L(n), on the N+1 side for the minus family and N-1 side for the
plus family. The enforced quotient ceiling is x<1e40, not a bound of
1e40 on the published term (`lcml_search`, lines 99–133).

## Snapshot

Git HEAD: `f8fdb200c56a54aa5e207c146882f7d2d7b87224`. The worktree contained
existing documentation changes and an untracked project. The hashes below
pin the reviewed source/data independently of those changes. The project
README received a navigation update during this review and is not hashed.

| File | SHA-256 |
|---|---|
| [lcml_reference.py](../lcml_reference.py) | `BF5DDE426AA386FE664CE9964A05A2F5816F113115DFB381C5724FB5ED62426E` |
| [lcml_search.py](../lcml_search.py) | `3E30313802400AD41777EC5086C9CB911C09A2A64E9A5B09E5BB0B956F83F56D` |
| [lcml_gpu.py](../lcml_gpu.py) | `B35E12B120C966C9701A3E7DB75C5E5968E90473038B1C5088B119524A908ABA` |
| [launch.py](../launch.py) | `F75896247D9A19463E41596DDFEABE6478C95223E09EA3466DAD9CB9813B95B0` |
| [score.py](../score.py) | `725BC25D726CC068F6DD26BC2EBF83DEC87034C92BD1B2C95E412BFCC97119EB` |
| [lcml_model.py](../lcml_model.py) | `B4A402DB4A69DF8CC0D6C5B4BD224F74148FF0406DA1046EE5AF5F3E36305B49` |
| [model_results.json](../model_results.json) | `C0B1B1B7F341DFDAC13DBBB11AC84A33F5F5AE5FFC9D52AA02DC03D2E09E6C56` |
| [campaign_checkpoint_a078502.json](../campaign_checkpoint_a078502.json) | `700064A57EE65635432E6C9660A3EB248AFF02C214053E7DA0CCF1656356EF0A` |
| [campaign_checkpoint_a074200.json](../campaign_checkpoint_a074200.json) | `99C4B2BE639C3A986679BD881F5497DCDC4E79DD54529A216E6C84C0D3C99EBF` |
| [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) | `E9E9F4A69D8EFA5B88B7765D80862324EB718A0C7AAE71327B301C0C5C62EA20` |

<a id="lcm-001"></a>

## LCM-001: the forbidden set is a scaled interval

**Priority:** most concrete new mathematical optimization.
**Evidence:** exact equivalence proved below; runtime unmeasured.

For a fixed prime q let h=q^e with e=v_q(L), and d=L/h, so q does not
divide d. The only indices producing a nonzero multiplier modulo q are
`k=h*t`, for `1<=t<=w=floor(n/h)<q`. For these indices,
`L/k=d/t mod q`. Thus

`q | ((L/k)*x+s) for some k<=n`

is equivalent to

`(-s*d*x mod q) in [1,w]`.

In the device's unit coordinate z=x/u, replace x by u*z. For primes
outside u the normalizing multiplier `a=-s*d*u mod q` is nonzero, and
`1 <= (a*z mod q) <= w` is the complete killed-set test. For a prime
dividing u, all the actual forms are s modulo q, so skip it. For q>n,
the same statement in the published term T=L*x is simply
`(-s*T mod q) in [1,n]`.

This is not an extra restriction and does not thin the mathematically
eligible set. It replaces a general collection of roots by one
coefficient and an interval. The plus and minus signs must be handled
explicitly; residue zero is allowed, and the endpoint w is forbidden.

The current CPU construction at `lcml_search.killed_residues`,
lines 152–178, takes one modular inverse per surviving multiplier.
The GPU's `TEST`, lines 1320–1339, first probes a 4096-bit mask, then for
q>4096 confirms a set bit by scanning the exact list. At n19/n20 the
allocated list has 32 slots, or 128 bytes per prime; table construction
is at lines 1845–1867. A set mask bit alone is insufficient when q>4096
because distinct residues alias modulo 4096.

The conservative first implementation is therefore to keep the mask-clear
fast path and the already-exact q<=4096 path, replacing only the q>4096
list confirmation with a multiply/reduce/range test. It can replace the
128-byte list by a 4-byte coefficient; w=n for these primes at the current
filters. The existing metadata fields are occupied, so coefficient storage
must be explicit. This is a representation reduction, not a runtime factor.
Normalizing every prime unconditionally could regress by replacing a cheap
mask rejection with arithmetic.

At current q2=32768/16384, two reduced residues multiply below 2^30/2^28.
The full configured sieve ladder reaches 2^24, so its product can approach
2^48: cast before multiplication and retain exact modular reduction.
On either survivor format the existing PERIOD_TERM must be added before
normalization, because r must denote the complete z modulo q.

For later Claude validation: independently derive the interval in the
optimized CPU/GPU paths, leaving the direct divisibility oracle untouched.
Compare every residue for small primes across signs, q dividing u or L,
prime-power transitions and both interval endpoints. Retain exact
survivor fingerprints on populated high windows and both record formats.
Check narrow/wide overflow paths and compare the hybrid against the
original lists. Reject the runtime proposal if it does not improve the
whole current-filter pipeline. The old phase measurements placed only
10–16% in tail rounds at n15–17; they do not establish today's n19 split,
and eliminating a list scan cannot justify an 11-fold overall gain.

<a id="lcm-002"></a>

## LCM-002: total forcing is monotone; promotion reuse needs fuller runs

**Priority:** mathematical clarification and conditional future reuse.
**Evidence:** proved identity; reuse already documented and unbuilt.

Although the quotient unit u(n) is not monotone, the total forced divisor
`F(n)=L(n)*u(n)` is monotone. More precisely,

`v_q(F(n)) = max{a>=1 : phi(q^a)=(q-1)*q^(a-1) <= n}`,

with exponent zero if the set is empty. To see this, let e=v_q(L(n)).
When q<=n, the extra unit factor q appears exactly when
`floor(n/q^e)=q-1`, equivalently `(q-1)*q^e<=n`.
Exponent e+2 cannot qualify because `n<q^(e+1)`.
For q>n the sole possibility is q=n+1 prime, giving the same criterion.
Thus increasing n can only increase these exponents.

For example, `F(18)=F(19)=1396755360`, while `F(20)=6983776800`.
The device already uses `z=x/u=T/F(n)`: this theorem does **not** reveal
an omitted factor by which the current candidate stream can be thinned.
It explains why a changing quotient denominator does not destroy nesting
in the published term T.

Coverage reuse is explicitly listed in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md),
lines 930–933, with a historical price of at most about 2.6 hours at
n18->n19, approximately 1% of that hunt. The current
`launch.follow_frontier`, lines 1170–1193, restarts at the new term floor.
A valid future implementation can instead carry a fully resolved interval
in T, converting its exclusive end B to `ceil(B/L(new_n))` in the new
quotient. Floor onto the new wheel and replay/clip any overlap; never
copy an old x or j as though its units were unchanged.

**The prerequisite is missing from the current classifier.**
`sprp_run`, lines 562–589, explicitly caps the returned run at n.
Only `record_discovery`, near line 1080, extends the run on the actual
published term. After a first find moves the frontier, a later stored
run-n candidate can become NEAR or CENSUS without that extension.
Therefore a closed old segment is not automatically fully classified for
the next open index. A cap value is not a proven stopping composite.
Existing exact-stopper checks can fail closed on an unextended rider;
this analysis does not assert silent corruption of the saved results.

For safe reuse, retain and resolve **every old-filter full hit** above a
find in increasing T order, checking integrality and the new forms, and
continue through any successive riders. Every genuine longer run survives
the old sieve above its exception floor, so this retained set suffices for
discovery coverage. Failed old runs cannot become true longer runs.
If changing q2, preserve the distinction between discovery coverage and
raw/censored census: the new sieve need not have the same survivor stream.

Persist the published-term boundary and its source-filter provenance only
after all potentially relevant capped hits have been resolved. Keep an
independent direct oracle and certificates; test promotions where L changes,
where only u changes, and where both are unchanged, including several
finds in one segment. The already-discarded tails of historical segments
cannot be reconstructed from a boundary alone. This proposal offers no
retroactive extra coverage at the present saved checkpoints.

<a id="lcm-003"></a>

## LCM-003: reuse period coordinates in later sieve rounds

**Priority:** bounded donor transfer, principally for the current wide
n19 configuration. **Evidence:** exact equivalence; donor measurements
only, destination unmeasured.

`lcml_gpu.lit_prefix` and the generated later rounds, near lines 2100–2110
and 2134–2149, reduce reconstructed offsets and add per-period terms.
The newer `ROUND_WINDOW` route in
[clique-ladders](../../clique-ladders/OPTIMIZATION_LOG.md), lines 528–552,
keeps those tests in the coordinates of a periodic pattern.

In z=x/u coordinates write `z=Wp*(j0+j)+r`. For a group modulus Q coprime
to Wp, let d=Wp^(-1) modulo Q. Define K_Q in these same z coordinates:
it is the set of residues where `(L/k)*u*z+s` is divisible by at least one
constituent prime of Q for some k<=n. Then testing z against K_Q is
equivalent to testing `j0+j+d*r` against d*K_Q modulo Q.
`window_patterns`, lines 1192 onward, already builds this kind of pattern.
With the factored CRT expression `r=r1+W1*(A-D)+b*Wp`, where b corrects a
borrowed period, precompute
`x0=(r1+W1*A)*d` and `ne=j0-W1*D*d` modulo Q.
The bit address is `x0+ne+b+j`. The borrow bit must survive compaction
and every overflow/fallback path.

The donor recorded approximately 1.08–1.10x on selected wide shapes;
its scalar row version fell to 0.87x, and narrow shapes could regress
to approximately 0.90–0.91x. These are neither LCM measurements nor
independent factors to multiply by LCM-001. A078502's current n20 record
is narrow, so the donor gives no basis to promise a gain there.

A future port must recheck the donor's compact-index bounds
`spb*tpb<=2^15` and group modulus `<2^15`, preserve group-union semantics,
and price the extra rows: approximately
`R1*16*ceil(padded_round_slots/8)` bytes plus block rows and patterns.
Keep frozen score windows; additionally validate and measure the actual
n19/q2=32768 wide plan, which has no dedicated current-filter score row.
Reject on end-to-end regression or excessive initialization/memory cost.

<a id="lcm-004"></a>

## LCM-004: the singular-series tail has a small rigorous bound

**Priority:** model assurance. **Evidence:** proved error bound, no search
speedup and no new model execution.

`lcml_model.log_singular` truncates at Q=200000. For every prime q>n,
the root count is **exactly n**, so its factor is
`G_q=(1-n/q)/(1-1/q)^n`. Expanding logarithms gives

`log G_q = -sum_{r>=2}(n^r-n)/(r*q^r) <= 0`.

Using `1/r<=1/2`, a geometric series and
`sum_{j>Q}1/j^2<=1/Q` yields, for integer Q>n,

`-n^2/(2*(Q-n)) <= sum_{q>Q} log G_q <= 0`.

At the composite source cutoff this is approximately [-0.000903,0]
for n19 and [-0.001001,0] for n20. Thus the finite product overstates
the full singular series by at most about 0.0903% and 0.1001%.
There are no exceptional large collision primes to account for here.
Floating-point error and integral discretization are separate issues.
This bound cannot explain an eleven-day or year-long forecast.

There is also an exact independent relation to the mathematical comparator
with forms `x+s, 2*x+s, ..., n*x+s`, at the same n and sign. Its root law
is `w_linear(q,n)=min(n,q-1)`:

`S_lcm(n)/S_linear(n) = product_{q<=n}(q-floor(n/q^e))`,

where q^e is the largest power of q at most n. The denominators cancel;
for q<=n the linear numerator is 1/q, and for q>n the local factors
coincide. This finite integer ratio is an independent mathematical check,
not a new thinning condition. A future model can report the remainder
interval and compare this identity without treating either check as a
validation of the prime-tuple/Poisson heuristic.

<a id="lcm-005"></a>

## LCM-005: a constructive refinement of the wheel-67 proposal

**Priority:** optional representation investigation. **Evidence:** static
integer arithmetic; the density opportunity was already documented.

The log's open item 1 says adding 67 at n20 requires relaxing R1_MAX or
using a fourth level. One concrete three-level split at unit 30 is:

| Level | Primes | Modulus | Allowed residue count |
|---|---|---:|---:|
| 1 | 23,29,31,37,41,43 | 1348781387 | 2438667 |
| 2 | 7,47,61 | 20069 | 5535 |
| 3 | 53,59,67 | 209509 | 60489 |

Here the combined second/third modulus is 4204636121<2^32 and the unit
coordinate period is 5671134939112679827<2^63. R2/R3 fit their 65535
limits. R1 exceeds 2^21 by 16.285%, but is **4.6 times the current n20
first-level row count of 530145**; the latter is the relevant memory
comparison. The wide record is necessary.

This is not a plan admitted by the current implementation:
`_split_rest`, lines 341–365, tries contiguous cuts of its sorted remainder,
whereas levels 2 and 3 above are interleaved. Raising R1_MAX alone need
not discover it. Allowing this split requires bounded non-contiguous
partitioning and rechecking every table/index/resource limit, not merely
changing a constant.

The constructor also needs a correction before these lists may be used.
At lines 1672 and 1683 it enables later levels through `p2>p1` and
`p3>wheel_top`. On explicit sequences these are lexicographic comparisons:
the proposed second level starts at 7, below the first level's 23, so the
constructor would omit it and subsequently omit level 3. Separate integer
upper-bound mode from explicit-set mode; in the latter, activate nonempty,
disjoint levels without an ordering test. Check the actual constructed
prime union, modulus and residue counts against the requested plan.
Directly supplying these lists to the current constructor is unsafe.

Adding q=67, whose w=20, changes the exact wheel density by 47/67:
**1.4255 times fewer generated candidates**. That is the already-priced
count opportunity, not measured speed. Larger first-level tables, the wide
record and much longer coverage segments can erase it. Claude should
reject the proposal unless a complete admissible plan improves time to a
confirmed term. Even the ideal count factor cannot turn the year-scale
n20 median into a one-day task.

<a id="lcm-006"></a>

## LCM-006: an explicit unit must not repeat a forced prime

**Priority:** correctness prerequisite for future custom plans.
**Evidence:** observed source and an existing recorded counterexample;
no execution and no effect on current defaults established.

`lcml_search.assert_unit`, lines 198–228, checks that every prime divisor
of the supplied unit is forced, then strips all its powers. It therefore
does not reject a repeated prime factor. `GpuEngine.__init__`, line 1621,
relies on this guard when handed an explicit unit.

For example, at n17 only unit 2 is forced, but the guard also admits unit 4.
The [recorded A074200 a(17)](../evidence/A074200_a17_3806845688410765173753259680.json),
divided by L(17), is
`x=310706098510212432482`, which is 2 modulo 4. A sweep restricted to
multiples of 4 would miss this recorded term. This counterexample uses
the existing evidence; its primality proof was not rerun.

Require the proposed unit to divide the complete squarefree `forced_unit`,
or explicitly check both squarefreeness and forced prime factors.
`forced_unit` itself, lines 181–195, already returns a squarefree product,
so the normal launcher and saved plans do not exhibit this mistake.
Future validation should reject unit 4 at n17 while accepting 1 and 2,
and retain the independent oracle and exceptional-prefix coverage.

## Conditional one-day thresholds

The JSON model record remains the historical n14-frontier forecast.
`lcml_model.write_model_results` uses `KNOWN`; its original n15–18 table
does not describe the present searches. Current conditional forecasts are
the later recorded values in [RESULTS.md](../RESULTS.md), “What is open now.”
The project's eight searched draws have mean E=1.21, versus 1.12 in the
disjoint published validation set. A blanket inherited 2.5x correction
is not established by this sample, and a model median is not a hard floor.

| Search | Stored current forecast | Rate used here | Continuous distance / rate |
|---|---|---|---|
| A074200 a(19), also A093553 | Conditional median x approximately 9.4e22 from C=2.1965e21 | 9.87e16 quotient/s, recorded campaign n19 rate | Approximately 10.77 days |
| A078502 a(20), also A093554 | Median x approximately 1.48e25 from its monotone floor | 4.71e17 quotient/s, v2 n20 benchmark | Approximately 363.7 days |

These are rounded fixed-distance calculations from stored forecasts/rates,
not fresh model predictions. A one-day median would require roughly
10.8x and 364x effective gains respectively. The n20 device rate has not
been established by a complete resumed campaign at the current height.
No reviewed proposal supports either factor.

For A074200, a current segment is
`224W=568806370012495648320` quotient units, about 1.601 hours at its
recorded campaign rate. Its saved partial segment needs approximately
0.445 hours more. Assuming unchanged rate, negligible startup, no find
and no promotion, 24 hours closes 15 segments, giving
`x<10728602291530330866750`, or
`m<2497538792667212040117751380000`.
The fifteenth closure is approximately 22.86 hours after resumption.

For A078502 after v2 adoption, a segment is
`216W=548491856797763660880`, approximately 0.3235 hours at the recorded
v2 device rate. With the same assumptions, 24 hours closes 74 segments,
giving `x<40811857048396562766960`, or
`N<9500696680650279741721301817600`.
The old v1 partial fraction was not credited in this calculation.

The published positive-family probability of 10% in a day is a model
statement at continuous depth. A probability of a **confirmed least term**
must account for segment completion and the extra work of proof. No such
probability was recomputed here. Implementing and validating a proposal
also takes time separate from its eventual hunt budget.

## Prior attempts and implementation boundaries

The subset wheel, killing-power order, corrected 2^64 bound, sparse tail
masks, wide record and runtime pool sizing are already present. Round 10
measured the wide n18/n19 wheel at about 1.15x/1.23x and n20's corrected
narrow width at 1.27x; these are incorporated in the current rates.
Do not count them again as prospective gains.

The wheel to 67 at n20 was rejected under the existing split/table bounds;
LCM-005 makes a relaxed construction concrete, not a free 1.43x.
The density-ordered wheel selection need not be a globally optimal subset,
and LCM-005 establishes arithmetic feasibility under relaxed bounds;
no faster complete replacement plan has been established here. The log's
64-bit pattern and thread-work proposals remain unmeasured, and ordinary
runtime profiling is outside this review's permanent scope. Sign reflection
equates local counts, not the positive-domain least terms; it cannot merge
the two searches. The two exact rider identities already avoid duplicate
campaigns.

Any change to level splits, segment width or launch enumeration must use a
new full enumeration fingerprint or explicit adoption. `config_key`
comments near lines 337–345 promise more load checks than `load` and
constructor assertions actually perform: stored n and W are checked, but
the same W does not determine the meaning of u. The existing v1-to-v2
`_adopt` is the relevant pattern: preserve the numeric coverage boundary,
floor onto the new wheel, reset u, replay pending work, avoid duplicate
census in overlap and alarm on a contradictory discovery there.
This requirement is not a finding that the existing checkpoints are corrupt.

LCM-001 and LCM-003 should preserve survivor fingerprints exactly. LCM-002
changes coverage/classification provenance and requires explicit census and
rider tests. The independent oracle must continue evaluating the original
entry definitions. Future implementation tests and measurements belong to
Claude's separately authorized work; this report performs none of them.
