# Linear ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** all seven primary families and their
three derived entries. **Status:** mathematical analysis and implementation
handoff. Workflow: [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).

The review team examined this project only, with complementary mathematical,
implementation and evidence checks. Sources, documentation, stored results,
checkpoints and evidence were read. Source hashes and lightweight arithmetic
were computed. No project engines, models, oracles, primality experiments,
tests, benchmarks, campaigns, CUDA compilation or GPU operations ran.

## Assessment

**There is a concrete new representation opportunity, but no established
speedup that makes the current median searches one-day jobs.** The existing
v4 period-window sieve already delivered its documented 6–13× improvement.
The seven current filters all impose 19 prime conditions; their recorded
conditional medians cost approximately **4.8–5.6 days** at the corresponding
stored rates.

**LIN-001** moves all currently forced primes into the quotient unit and
gives an explicit 61-wheel fitting the current narrow arithmetic. This
reduces generated candidates per unit of published-term line by **61/42,
about 1.45×**, while substantially increasing first-level tables. Wider
windows become numerically possible; their performance is unmeasured.
A 67-wheel gives a further constructive option and substantial costs.

**LIN-002** proves modest aggregate savings from combining same-sign
families through an exact union of survivor sets. It does not accelerate
one family's mathematical search by the aggregate factor, and a naive
shared-core sieve can be worse than separate hunts. **LIN-003** is a
conditional donor idea, **LIN-004** bounds a small model truncation error,
and **LIN-005** is an incidental custom-unit correctness prerequisite.

The labels below distinguish **proved mathematics**, **observed source or
data**, **previously measured here**, **related-project measurements**,
**unmeasured proposals**, and **model-derived estimates**.

## Definitions, evidence and saved state

The primary definitions are all **at least** the stated number of rungs:

| Entry | Entry's term and conditions | Last recorded term | Open index |
|---|---|---|---:|
| A088250 | least k, r*k+1 prime for r=1..n | [a(18)=11260441017037317719293680](../evidence/A088250_a18_11260441017037317719293680.json) | 19 |
| A088651 | least k, r*k-1 prime for r=1..n | [a(18)=152058443198637095680139580](../evidence/A088651_a18_152058443198637095680139580.json) | 19 |
| A173750 | least m, k*m+1 prime for k=2..n | [a(18)=a(19)=147316106448079863444150](../evidence/A173750_a18_147316106448079863444150.json) | 20 |
| A125838 | least m, k*m-1 prime for k=2..n | [a(19)=112258928035903409184283860](../evidence/A125838_a19_112258928035903409184283860.json) | 20 |
| A125839 | least m, k*m-1 prime for k=3..n | [a(20)=19653405164609436282292230](../evidence/A125839_a20_19653405164609436282292230.json) | 21 |
| A164325 | least m, (2*k-1)*m+1 prime for k=1..n | [a(18)=511721589397871969516400](../evidence/A164325_a18_511721589397871969516400.json) | 19 |
| A164326 | least m, (2*k-1)*m-1 prime for k=1..n | [a(18)=9606289803039023735440800](../evidence/A164326_a18_9606289803039023735440800.json) | 19 |

[lladder_reference.py](../lladder_reference.py), `FAMILIES` at line 112,
`KNOWN_ALSO` at line 194 and `FOUND` at line 223, separates original
literature from this project's claims. The three derived entries require
these exact distinctions:

- **A202778** agrees with A088250 at an index only when that monotone least
  term has a composite next rung. Recorded a(15)..a(18) all have exact runs,
  so those four derived terms are already settled. The next open index is
  19; a future run longer than 19 would not settle its exact-run a(19).
- **A202779** is analogous for A088651. Recorded a(16)..a(18) are exact,
  and the next open index is 19.
- **A071576(n)=A088250(n)/2 for n>=3**. The new terms a(15)..a(18) are
  already recorded at half the corresponding values; its current last
  term is 5630220508518658859646840 and next index 19. The restriction
  n>=3 matters: A088250(2)=1, whereas A071576(2)=1.

These are existing implemented identities, not new terms from this review.
For example, the primary plateau A088250(7)=A088250(8)=512820 does not imply
A202778(7)=512820; its recorded exact-run term is 8224860. A173750's rider
at index 19 is one discovery, not a separately searched draw.

All 27 stored discovery JSON files have `certificates_verified=true` and
empty `unproved` lists. They cover 28 primary terms. The historical summary
in [RESULTS.md](../RESULTS.md), lines 904–921, records 443 certificates:
263 deterministic Miller–Rabin, 59 BLS75 Theorem 1 and 121 Theorem 15.
The plus families use N-1=m*term; the minus families use N+1=m*term.
Reading certificate flags and the historical verification account is not
a new certificate verification. Minimality additionally depends on the
recorded exhaustive sweep and the known smaller-term exclusions.

Every saved checkpoint below is v4, dated 2026-09-05, with physical wheel
period **W=1922760350154212639070**, q2=65536, 128-period segments and
`k_start=1000000`. Except A088651's unit 510510, the stored unit is 30030.
The checkpoint's `k` is an exclusive contiguous coverage boundary C;
`u` is an interleaved work cursor and adds no contiguous interval.

| Checkpoint | Current filter | C: no qualifying term below | j | u / launches per segment |
|---|---:|---:|---:|---:|
| [A088250](../campaign_checkpoint_a088250.json) | 19 | 11438501323067410989827430 | 5949 | 0 / 680 |
| [A088651](../campaign_checkpoint_a088651.json) | 19 | 213107220648992003638684380 | 110834 | 347 / 680 |
| [A173750](../campaign_checkpoint_a173750.json) | 20 | 4547328228114712891400550 | 2365 | 108 / 680 |
| [A125838](../campaign_checkpoint_a125838.json) | 20 | 112400724549314962454754060 | 58458 | 0 / 680 |
| [A125839](../campaign_checkpoint_a125839.json) | 21 | 59486359713071030627547660 | 30938 | 37 / 680 |
| [A164325](../campaign_checkpoint_a164325.json) | 19 | 4301214903294973673599590 | 2237 | 697 / 1360 |
| [A164326](../campaign_checkpoint_a164326.json) | 19 | 16541507292376691333919210 | 8603 | 1026 / 1360 |

Snapshot field anchors are lines 2–13 in each checkpoint. Its `found` map
and the literature determine the filter; the JSON does not contain a
separate current-n field. `Campaign.frontier`, `state`, `swept_k` and the
closed-segment loop in [launch.py](../launch.py), lines 617, 696, 769 and
1209–1219, establish the interpretation. `RESULTS.md` line 652 says each
leg stopped at a segment boundary; five actual saved `u` values contradict
that wording. The published C values themselves agree with the files.

All current C values exceed their deterministic proof crossings. Failed
strong tests still prove compositeness, so a true prime cannot be discarded
by those tests; a false positive can only add verification work or lengthen
a preliminary run. A discovery must pass the independent checks and
certificate route. See `sprp_run` and `verify`, launch lines 473–495 and
343–375. The census above the crossing is a probable-prime census, not
443 certificates repeated for every classified candidate.

## What one day would mean at the saved rates

The following uses **existing measurements**, not new measurements:
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), v4 Measurement 6,
lines 1076–1128. Each rate is about one second of device work at the actual
post-leg checkpoint. The same log records ambient changes of +7–9% and
-16.7%; whole campaign phases support the general scale, not three-digit
predictive accuracy. [RESULTS.md](../RESULTS.md), lines 848–871, supplies
the rounded conditional medians from these C values.

| Family | Stored rate, term-units/s | Additional line in 24h | Rounded conditional median | Days to that median |
|---|---:|---:|---:|---:|
| A088250 | 2.875e22 | 2.48e27 | 1.2e28 | 4.8 |
| A088651 | 2.906e22 | 2.51e27 | 1.3e28 | 5.1 |
| A173750 | 2.902e22 | 2.51e27 | 1.3e28 | 5.2 |
| A125838 | 2.901e22 | 2.51e27 | 1.3e28 | 5.1 |
| A125839 | 2.893e22 | 2.50e27 | 1.4e28 | 5.6 |
| A164325 | 1.838e22 | 1.59e27 | 8.0e27 | 5.0 |
| A164326 | 1.832e22 | 1.58e27 | 8.1e27 | 5.1 |

Arithmetic is `86400*rate` and `(median-C)/(86400*rate)`. It assumes no
find, promotion, startup, verification pause or rate change. It is not a
new model integration. Approximately 4.8–5.6× throughput would put those
same conditional median locations within a day; a median remains a model
quantile, not a promised discovery. The stored model gives 9–11% within
nine hours, not a current computed 24-hour probability.

Current segment duration is about 8.5 seconds for consecutive-multiplier
families and 13.4 seconds for odd-multiplier families. The existing partial
segment affects at most that much confirmation latency. With L launches,
the ideal number of complete segments in one day is
`floor(u/L + 86400*rate/(128*W))`; the claim ends at C plus that count
times 128W. Larger-wheel proposals must reprice this confirmation interval.
The exclusive engine ceiling is 10^40, far beyond the present model
medians; raising it is not the current opportunity (`k_ceil`,
[lladder_search.py](../lladder_search.py), lines 99–120).

<a id="lin-001"></a>
## LIN-001 — extract the full forced divisor and construct a 61-wheel

**Status: proved representation/count opportunity; runtime unmeasured.**

For prime q, the forbidden residues of the term are
`{-s*m^(-1) mod q : m is a multiplier, q does not divide m}`. Inversion is
a bijection on the nonzero residues. If the multipliers cover every
nonzero residue, the term must be 0 modulo q, outside the prime-equals-value
exception zone. The reference already proves this and tabulates the
forcing thresholds: for odd q, 1..n forces q at n=q-1; 2..n at n=q+1;
3..n at n=q+2; odd multipliers at n=q. For q=2 the corresponding
thresholds are 1, 3, 3 and 1. See `FORCING`, reference lines 586–595,
and `forced_unit`, search lines 167–176.

At every current filter, **U=2*3*5*7*11*13*17*19=9699690** is therefore
forced. No prime above 19 is forced. The existing fixed units intentionally
leave newly forced 17 and/or 19 in the wheel. They already have just one
surviving residue, so extracting them produces **no new candidate thinning**.
It reduces the device quotient period by 323 for six families and by 19
for A088651, releasing arithmetic room.

For a fixed wheel-prime set Q, the published-term period is
`U*product(q in Q, q does not divide U)=product(q in Q)`. Thus extracting
17/19 alone preserves physical W, although it changes the device residue
coordinates and the meaning of a partial `u`. With all forced primes
extracted, Wp59=W59/U=198229051666003.

An explicit next wheel uses contiguous cutoffs **p1=41, p2=53, p3=61**:

| Level | Primes outside U | Modulus | Consecutive 19-form residues | Odd 19-form residues |
|---|---|---:|---:|---:|
| 1 | 23,29,31,37,41 | 31367009 | 190080 | 298870 |
| 2 | 43,47,53 | 107113 | 22848 | 22848 |
| 3 | 59,61 | 3599 | 1680 | 1680 |

The combined second/third modulus is 385499687<2^32, both grid dimensions
are below 65536, and Wp61=12091972151626183. In particular,
`129*Wp61+65536=1559864407559843143<2^63`. Even
`257*Wp61+65536=3107636842967994567<2^63`. The 128-period construction
therefore satisfies the existing narrow numeric limits; a wide record is
not required for it. See `GpuEngine.__init__`,
[lladder_gpu.py](../lladder_gpu.py), lines 1015–1079.

Since 61 exceeds every current multiplier, it excludes exactly 19 of
61 residue classes. CRT independence proves the generation-density
reduction **61/(61-19)=61/42** for all seven families. At unchanged sieve
depth the final complete survivor set in the same absolute interval is
unchanged: 61 moves from a later sieve into candidate generation.

The cost is material: first-level rows increase 22× from 8640/13585 to
190080/298870. The new physical W is 61W59=117288381359406970983270.
Its 128-period segment is 61× longer in term space; even with an ideal
61/42 rate gain, confirmation duration becomes 42× the current duration,
roughly 6–9.4 minutes. These are count-based illustrations, not rates.

The old rejection in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), line
501, and the PB256 rejection at line 955 assumed the old fixed quotient
unit. That premise no longer blocks this current-filter construction.
PB256 is an additional **unmeasured** possibility after re-denomination,
not another proved throughput factor. Keep 128 as the initial comparison.
U=9699690 is invalid at several historical openings and canaries; retain
their valid smaller units and make any new selection filter-dependent.

### A 67-wheel is arithmetically possible but considerably more costly

Contiguous cutoffs **43,59,67** give W1=1348781387,
W2=600662303, Wp67=810162134158954261. The three residue counts are
4561920 / 38080 / 2016 for consecutive families and
7172880 / 38080 / 2016 for odd families. These fit the existing level
count caps, but the current reduction bound permits only **10 live
periods**, since 11Wp67<2^63<12Wp67.

The exact candidate reduction against the present 59-wheel is
`(61/42)*(67/48)=4087/2016≈2.0273`. First-level rows grow **528×**.
The first-level window coordinates alone cost about 8.70 MiB per group
for consecutive families and 13.68 MiB per group for odd families.
A full 128-period proposal needs a wide period record throughout the
kernel, tail, queues and final reconstruction; the present output
reconstruction at GPU lines 1640–1655 only forms `unit*(base+off)`.
A 2^64 narrow Barrett repair alone would still permit only 21 periods.

At a hypothetical ideal count-proportional speed, a full 128-period
67-wheel segment would take 2016× the present segment time, about
4.8–7.5 hours. That is a significant confirmation cost. This option is
not evidence for a one-day median, and the memory/arithmetic costs can
erase its count advantage. Wheel 71 exceeds the current 2^63 CRT product
bound even after the maximal valid unit is extracted.

### Required coverage migration and acceptance

The present config key encodes a fixed unit and wheel; load restores
j/u, and the constructor checks physical W but does not validate the
stored unit or complete enumeration fingerprint. See launch lines
291–325, 595–605 and 751–766. Merely accepting the old key is unsafe,
including when unit-only extraction preserves W.

For a changed physical W, preserve the numeric committed boundary B,
start at `floor(B/Wnew)` with u=0, clip candidates below B even in a
nonzero period, and retain B as the certified bound until the new segment
closes beyond it. Never round B up. Current `k_min` at launch lines
632–635 clips only period zero, so this needs an explicit adoption path.
Discard old partial pending records coherently with their uncommitted
survivor accounting; preserve committed finds, evidence and census and
avoid counting replay overlap twice. Existing v2/v3 acceptance resets u
but retains pending; it is not a complete template for this new change.

Future validation should compare complete survivor sets in identical
absolute term intervals against the independent dense CPU sieve, both
signs and all multiplier shapes, before any timing. Retain historical
score fingerprints; add actual c19 consecutive and odd workloads.
[score.py](../score.py), lines 91–108, currently freezes older c14–17
shapes. A new wheel changes period-denominated workloads, so any replaced
fingerprint needs its absolute interval and justification recorded.

<a id="lin-002"></a>
## LIN-002 — an exact union can share work between same-sign families

**Status: proved aggregate candidate-count opportunity; unimplemented.**

At a common term value, the current consecutive positive families require
multiplier intervals A=[1,19] and B=[2,20]. The negative families require
A=[1,19], B=[2,20] and C=[3,21]. Their wheel-survivor sets overlap.
Let S(I) be the complete 59-wheel survivor set for all multipliers in I.
Then `S(I) intersect S(J)=S(I union J)`.

For the primes q=23,29,31,37,41,43,47,53,59, put
`R_c=product(q-c)`. The smaller primes are forced for all these intervals.
Exact arithmetic gives R19=173717913600, R20=84741239583 and
R21=35612262400. Thus:

| Pool | Exact union size per common wheel period | Separate work / union work |
|---|---:|---:|
| Positive pair | 2R19-R20=262694587617 | 1.3226 |
| Negative triple | 3R19-2R20=351671261634 | 1.4819 |
| Both pools, separate signs | 5R19-3R20=614365849251 | 1.4138 |

For the triple, S(A) intersect S(C) is contained in S(B): passing [1,21] already
passes [2,20]. Its inclusion-exclusion R21 terms therefore cancel.
These factors apply to **combined generation work**, not a single
family's line speed or its probability of finding a term.

An implementation must enumerate the **union of complete survivor
sets**. Taking a union of allowed residues separately at each prime and
then a CRT product is not equivalent: different primes can satisfy
different families, leaving no one family satisfied globally. Carry a
consistent family bitmask through the full wheel construction and later
tests, or use an independently proved disjoint decomposition. A zero
family mask is rejected; the live masks determine each family's tests.
One constructive route is to deduplicate each level's residues, tag and
bucket them by family mask, then enumerate only Cartesian products of
buckets whose masks have nonzero AND. Generating every complete family
wheel separately and deduplicating afterward would still pay the
enumeration work whose reduction is being claimed.

The tempting common-core shortcut is weak. Positive core [2,19] has
R18=325070370625, giving only 2R19/R18≈1.069 before endpoint checks.
Negative core [3,19] has R17=570621542400, more candidates than three
separate R19 wheels. A shared stream can be slower if this distinction is
ignored. Tables, masks, endpoint work and output classification also cost
time; no pooled throughput has been measured.

Keep each family's own bound and activate it only on line not already
covered for that family. Jumping all streams to the largest C would skip
the lower-depth families' unresolved intervals. Independently classify
and verify each family's run, stop witness, riders and census. Promotions
change interval lengths and hence these precise counts. Family events
are correlated; neither multiply independent no-hit probabilities nor
count a shared discovery as independent statistical evidence.

This is an aggregate efficiency proposal, with moderate count savings.
No previous pooled-union attempt was found in the optimization history.
It does not establish the roughly fivefold throughput needed for the
current one-family conditional medians.

<a id="lin-003"></a>
## LIN-003 — later-round period coordinates are a conditional donor

**Status: deferred unless a useful wide-wheel representation is established.**

The current main window sieve already uses period coordinates. Later
in-block rounds reconstruct `off` and use `lit_prefix` Barrett chains:
GPU lines 1346–1399. The related
[clique implementation](../../clique-ladders/clique_gpu.py), lines
2285–2330, keeps the same coordinates in these later rounds.

Here let z=term/U and K_Q be the union, modulo a round-group modulus Q,
of the roots of `m*U*z+s` for its constituent primes. Since Q is coprime
to Wp, D=Wp^(-1) mod Q exists. If CRT gives
`off=r1+W1*A-W1*B+Wp*b`, then the candidate z=off+Wp*(j0+j) passes
the group exactly when
`D*(r1+W1*A) + (j0-D*W1*B) + b+j` avoids D*K_Q modulo Q.
This is the same fixed-residue progression, not a new primality condition.

The donor needs every Q<2^15 and **SPB*TPB<=2^15**, not PB*TPB.
Its table costs `16*R1*ceil(padded round slots/8)` bytes, with each
round padded to eight slots. LIN-001's already enlarged R1 makes this
cost especially relevant.

[Clique OPTIMIZATION_LOG.md](../../clique-ladders/OPTIMIZATION_LOG.md),
lines 528–552, records about 1.08–1.10× on wide records; narrow variants
were 0.90–0.91 on one shape and about 1.006 on another, and the scalar-u16
variant was 0.87. These are donor measurements, not linear measurements.
They justify deferring an unconditional narrow61 port. If tested later,
preserve independent CPU construction and verify the transformed roots,
CRT borrow, high bases and full survivor fingerprints first.

<a id="lin-004"></a>
## LIN-004 — current-series identities and a rigorous small tail bound

**Status: proved model assurance; no search speedup.**

At the present filters, the five consecutive families all have
`w_q=min(19,q-1)`: primes through 19 are forced, and primes from 23 exceed
every multiplier (at most 21). For odd multipliers 1,3,...,37, residues
are distinct for q>19, but q itself occurs at q=23,29,31,37. Those four
primes therefore have **18**, not 19, nonzero multiplier residues.
All other local counts agree. The exact singular-series ratio is

`S_odd/S_consecutive=(5/4)*(11/10)*(13/12)*(19/18)=2717/1728≈1.57234`.

This also explains the 13585/8640 first-level row ratio. A bigger odd
series does not automatically make its hunt cheaper: its wheel is denser,
the measured line rate is lower, and its logarithmic factors differ.
The current approximately equal day costs are consistent with this.

For every current shape, q>37 gives exactly c=19 roots. The omitted
Euler factor is `A_q=(1-c/q)/(1-1/q)^c`. For q>c,

`log A_q = -sum_(r>=2) (c^r-c)/(r*q^r) <= 0`,

and
`|log A_q| <= c^2/[2*q*(q-c)] <= c^2/[2*(q-c)^2]`.
Bounding the prime sum by all integers above the composite cutoff Q
and applying the decreasing-integrand bound yields

`-c^2/[2*(Q-c)] <= sum_(q>Q) log A_q <= 0`.

At Q=200000 and c=19 this is [-0.000902586,0]. Thus the omitted
factor lies between exp(-0.000902586) and 1: less than about **0.091%**
in the singular-series normalization. The truncated product slightly
overestimates intensity. This cannot explain a five-day versus one-day
gap. See `QMAX` and `log_singular`,
[lladder_model.py](../lladder_model.py), lines 68 and 93–109.

The [stored model_results.json](../model_results.json) intentionally uses
the original `KNOWN` frontiers; for example A088250 n14 appears at lines
9–12. `write_model_results`, model lines 281–326, still derives from
`KNOWN`. Its opening predictions must not be presented as the current
frontier forecasts. The report's current numbers instead come from the
later conditional table in RESULTS.

The model's docstring and stored caveat call medians “floors” and prescribe
a generic 2–3× correction. The later project evidence does not establish
that correction: RESULTS lines 916–921 records 27 searched draws with
mean integrated intensity E=1.08, compared with 0.86 on 46 published
draws, and term/median from 0.008 to 7.9 with geometric mean 0.75.
These observations support broad scatter, not a literal lower bound or
a calibrated universal multiplier. Bateman–Horn intensity plus Poisson
first-event assumptions remain heuristic, and related families are not
independent samples.

For a future forecast use each verified current form set and its saved
contiguous C: integrate from C to a proposed completed boundary. The
launcher's status probability at lines 827–831 instead describes the
past interval from the previous term to C. It is not the remaining-day
probability. No model was rerun or edited in this review.

<a id="lin-005"></a>
## LIN-005 — the explicit-unit guard must reject unjustified powers

**Status: observed correctness gap in optional inputs; defaults unaffected.**

`assert_unit`, [lladder_search.py](../lladder_search.py), lines 179–209,
checks that every prime divisor of unit is forced, then strips all
powers of those primes. It does not establish that their higher powers
are forced. `GpuEngine.__init__`, GPU line 993, relies on this guard.

For example, at A088250 n17, unit=4 passes the source's prime-support
checks. Yet the recorded
[a(17)=1048124771278912649231910](../evidence/A088250_a17_1048124771278912649231910.json)
is 2 modulo 4. That explicit unit would omit a known eligible least term.
This conclusion uses source inspection and integer arithmetic only.

Require unit to divide the complete squarefree forced product, or
equivalently check squarefreeness as well as forced prime support.
Current fixed units and the proposed 9699690 are squarefree, so this
does not show a defect in the present saved hunts. Future unit-selection
validation should reject this example and preserve valid divisors.

## Already implemented, rejected, and future handoff

The principal CRT wheel, period-window sieve, sparse residue masks,
base-2 one-sided screen, later strong tests, certificate routes and
per-family checkpoint policies already exist. Recommending the v4
window sieve again would count its historical gain twice. Completed
segments already carry across promotions after every pending run is
classified in order (launch lines 948–964 and 1209–1235); there is no
missing generic promotion-reuse optimization here. Run classification
extends to current filter+8, and exact-stopper verification fails closed
if that cap is reached without a real stopper.

Existing containments give A088250(n)>=A173750(n) and
A088651(n)>=A125838(n)>=A125839(n), and a full [1,2n-1] condition implies
the odd family at n. They give no stronger current open bound than the
saved exclusions: the needed sibling index is unresolved or its bound
is weaker. Sign reflection gives equal modular densities, not a map
between positive least terms. Prime-power lifting of the existing
divisibility tests gives no extra compulsory powers. Sparse perfect-power
factorizations affect a negligible fraction of the present line.

The history already priced window-chain latency, register/shared layouts,
tail streams and queue batching. Those measurements are background,
not a new static mathematical optimization list. The substantial open
mathematical implementation choice is LIN-001, followed by the more
complex aggregate LIN-002 if hunting several entries together is useful.
Do not multiply their count factors into a claimed measured speedup.

For later Claude work: preserve the original independent oracle and
dense CPU definition; implement the transformed GPU mathematics
independently. Cover prime-equals-value exceptions below the safe floor
`max(K_FLOOR,q2+1)` without wheel exclusions. Validate all seven shapes,
both signs, plateaus, exact derived entries, clipped intervals, changed
units, changed physical periods and interrupted resume before measuring.
Keep 128/256 power-of-two windows initially: the current constructor
accepts arbitrary multiples of 32, but `off_of` at GPU line 793 decodes
with `qi & (PB-1)`. A non-power width such as 224 needs a separate proven
encoding change and queue-capacity audit.

Record every attempt, including regressions, in OPTIMIZATION_LOG and
link the outcome from the local index. Compare actual current-filter
end-to-end rates, memory and confirmation latency on equal absolute
term intervals; changed enumeration is not permission to weaken parity.
This handoff does not authorize a campaign start.

## Source snapshot

Read on 2026-10-20 at Git HEAD
`f8fdb200c56a54aa5e207c146882f7d2d7b87224`. The workspace was already dirty;
HEAD alone does not identify the inspected working files. SHA-256 values
below pin them. Project README navigation was edited separately by the
coordinating reviewer and is not hashed here. Line numbers above refer to
this snapshot, not to a future implementation.

| File | SHA-256 |
|---|---|
| lladder_reference.py | `9997fb5ab8b4cf3355196972924665fb3d3db7b01be98bc92c813cbe15da6ce2` |
| lladder_search.py | `9db4c8c1ea1f42befa51735538936c6583e09b2381dd98ad3d2e9ec5301fa8fb` |
| lladder_gpu.py | `4c828282b8c65da71364c3567614d2a77446c133e9b9e3f5827f20455f37a905` |
| launch.py | `afab7401f542dcbc9172f55130be128e5e8a3a0c271a84fa920731ea826655c8` |
| score.py | `aea34aec845b0787608cffb31bcbb214f76ff69ad400cfd44e366f8c0131e630` |
| lladder_model.py | `1714ee745a0fec434e3b51de3adf9ea177b7e9509d5c8367d0e1f321ed7e8a58` |
| model_results.json | `f04c9f17e3844f8cf829ce6eb8d92f33f9baa832aa6c9e16c25e0c2533f81988` |
| OPTIMIZATION_LOG.md | `de67c4ec3d805a80b3e43d99a3cd7847d9fdde379d2a469ff514135050f3faea` |
| RESULTS.md | `6449efdddc0bb7bdd2d7f39548b8d03177b84bb208ff2f4871c5baad9da667e8` |
| BENCHMARKS.md | `82693e220be5a40f53c3930bfb94eed43df3db01ae060e58cc01dd0b4c82c02d` |
| campaign_checkpoint_a088250.json | `1b1dfb39c0a2712b9c96062f81007cfbebcf550e6e198e692185a842662d616c` |
| campaign_checkpoint_a088651.json | `7b80c39a79dbe33e581308f2303a0e87e7ebe92676a3c0ae5192903f814dae02` |
| campaign_checkpoint_a173750.json | `0d3d0acbf7ac1294bb3d4bb1d2511157688eac18fcabe42d66a2b890e3832700` |
| campaign_checkpoint_a125838.json | `cc786b7a7f54b277edb5f2606ae52b82e48984f60dcf10cb9c78baff59d5093e` |
| campaign_checkpoint_a125839.json | `087a314d5c41e6b5e61a2777e345a3f1aba770b3c1275dbae02d25c78e5f0767` |
| campaign_checkpoint_a164325.json | `5c856f3041624c91e02db4bd9c732d5807bd989ce60f921b17b57a28eddf33d2` |
| campaign_checkpoint_a164326.json | `3a421f68b4fc76b05acc80f8f393fdd8dc046e579ffd0b036b60295db06f3ba0` |
| ../clique-ladders/clique_gpu.py | `c7c45c4fb31f7e3ad7fd8d199fbef94ffe2aec2d8386bbc3e4f82a65e9e1f54a` |
| ../clique-ladders/OPTIMIZATION_LOG.md | `0b4f84c182d3798370201f412fea42fc334c304ddd95a361a6a7c80fe6ef7c89` |

Only this report and its review index were authored by this reviewer.
The implementation, model outputs, checkpoints and evidence were unchanged.
