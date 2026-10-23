# Prime-ladders static mathematical review — 2026-10-20

**Author: Codex (OpenAI).** The review team examined this project only,
following [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). This was entirely
static: source, saved evidence, checkpoints, models and prior measurements,
with finite arithmetic and mathematical proofs. No GPU, project imports,
models, searches, primality experiments, tests, benchmarks or campaign
changes were run. Only documentation was edited.

There is a substantial algorithmic donor to investigate: this project
still tests candidates individually, while newer sibling engines amortize
the small-prime sieve across many wheel periods. A related linear-ladders
transfer recorded 8.8× at its live filters. That is donor evidence, not
a measured prime-ladders gain.

A new proof-ceiling observation complements that transfer. Every current
candidate is divisible by 2310, so writing k=2310t keeps every prime factor
of k below the deterministic Miller–Rabin bound whenever t is below it.
The existing one-level certificate argument therefore permits a current
ceiling **2310 times larger** than the plus family's present bound.
The shared library now also has the N+1 certificate route that the minus
family lacked when it stopped.

Together these are a credible route to a materially stronger hunt.
The saved median depths still require approximately **10.9×** the recorded
plus rate or **9.1×** the recorded minus rate to fit one day, before proof
and startup costs. No speedup or additional term was established by this
review, and donor performance does not guarantee those thresholds.

## Evidence and snapshot

**Proved here** means a mathematical implication or finite arithmetic.
**Observed** means a source/data statement. **Recorded measurements**
belong to their cited historical configuration. **Unmeasured** covers the
proposed port and extrapolated clocks. Certificate files were read, not
independently reverified by executing their checks.

HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`; the worktree has later
changes. SHA256 values at the end pin the reviewed files. Source citations
give relative links, symbols and snapshot line anchors.

Both saved checkpoints are from **2026-09-03**, with zero partial cursor
and empty pending lists. The documentation says these hunts were paused;
this review does not infer current process activity from that history.
The OEIS-export status mentioned in the README is dated September 29,
not a statement about current submissions.

## Both families, all recorded terms and actual coverage

For sign s=±1, the condition at index n is that all
`p_i k+s`, i=1..n, are prime, where p_i is the ith prime and k≥1.
These are **at-least n** conditions. Terms are nondecreasing and can
repeat. See [pladder_reference.py](../pladder_reference.py), definitions,
`KNOWN`, `FOUND`, `forbidden_k_residues` and `w` at 189–215.

| Family | Recorded new terms in this project | Actual next filter |
|---|---|---|
| A084700, s=+1 | a14=24581646307811670; a15=1183192161007235610; a16=161515890673488267840; a17=2446970377116913184460; a18=416266897501398851227320 | n19 |
| A084701, s=−1 | a12=43708752888360; a13=2276961234558570; a14=a15=165784683394437030; a16=16739777598441148020; a17=9050934616476845605590; a18=23562434281685500120920 | n19 |

There are **eleven discovery files settling twelve terms**. The old-schema
plus a14–a17 files contain deterministic-MR certificate objects and four
verification legs, but omit the newer aggregate certificate flags.
Plus a18 and all six minus files explicitly record
`certificates_verified=true`, `unproved=[]`. Across all eleven files there
are **171 certificate objects: 157 deterministic-MR and 14 BLS75 Theorem 1**.
The BLS proofs belong to plus a18's values from i=5 onward.

The complete history, exact values, stopper factors and independent
disk-verification claim are in [RESULTS.md](../RESULTS.md), lines 7–197.
The latest evidence is [plus a18](../evidence/A084700_a18_416266897501398851227320.json)
and [minus a18](../evidence/A084701_a18_23562434281685500120920.json).
The [minus a14 file](../evidence/A084701_a14_165784683394437030.json)
records its run of 15 and both settled indices. These are existing
discoveries, not new terms produced by this audit.

Let B be the **exclusive committed boundary**: all relevant candidates
below B, starting from the campaign's justified floor, have been classified.
The next candidate may equal B. A partial launch cursor is not such a bound.

| Saved state | A084700 | A084701 |
|---|---|---|
| Checkpoint | [plus](../campaign_checkpoint_plus.json), 09:34:34 | [minus](../campaign_checkpoint_minus.json), 13:16:20 |
| Filter inferred from `found` | 19 | 19 |
| Device unit | 2310 | 210 |
| Wheel levels / depth | primes through 31; 37,41; 43,47,53 / 65536 | same physical prime set / 65536 |
| Physical W | 32589158477190044730 | 32589158477190044730 |
| j; u; pending | 12774; 0; empty | 1519; 0; empty |
| B | 416293910387625631381020 | 49502931726851677944870 |
| Adopted census floor | 54377163033430649351940 | 0 |

`swept_k`, [launch.py](../launch.py) 663–673, preserves the numeric
adopted floor as well as closed-period coverage. The plus last term is
slightly below B; do not replace the exhausted interval by the term.
The campaign loop at 1045–1095 closes **one physical period at a time**.
The checkpoint key's suffix `seg128` is not evidence of a 128-period
committed coverage unit in this implementation.

At n19, `p_19=67`. With
`M=3317044064679887385961981` from
[huntlib/primes.py](../../huntlib/primes.py) line 35, the current enforced
ceilings are M for plus and `floor(M/67)+1` for minus:

`C_minus = 49508120368356528148687`.

The minus campaign stopped after its last complete period, leaving
**5188641504850203817** units below C_minus unswept. RESULTS 239–258
already acknowledges this sliver. It is not legitimate to claim all line
to the exact ceiling has been covered, nor to prove the next term exceeds
that ceiling. Resuming the current whole-period loop finds no legal
complete period and stops.

## Recorded rates, model limits and the one-day target

[BENCHMARKS.md](../BENCHMARKS.md), the n19 discussion, and
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), v3.1, record:

- **Plus n19:** approximately **1.23×10^19 k/s**, a paired/interleaved
  actual-filter measurement. The frozen SCORE18 rate about 6.2×10^18
  belongs to n18 and is not the present n19 rate.
- **Minus n19:** approximately **1.27×10^19 k/s**, from the campaign's
  final 2.59×10^22 stretch in 34 minutes, at unit 210. The old proposed
  unit-210-to-2310 rate gain was not measurable in this pointwise engine.

At these rates one current period takes approximately 2.65 seconds
(plus) or 2.57 seconds (minus). The problem is search depth and proof
range, not present confirmation latency.

[model_results.json](../model_results.json) is the original pre-campaign
artifact: its frontiers are plus n13 and minus n11, and it contains no
n19 prediction. The later n19 quantiles are recorded in RESULTS
245–290 and BENCHMARKS, calculated from the respective a18 terms:

| Family / n19 | Saved Q1 | Saved median | Saved P90 | Continuous travel from B at recorded rate |
|---|---|---|---|---|
| A084700 | ≈4.0×10^24 | ≈1.2×10^25 | ≈6.2×10^25 | Q1 ≈3.37 days; median ≈10.90 days |
| A084701 | ≈2.9×10^24 | ≈1.0×10^25 | ≈5.9×10^25 | Q1 ≈2.60 days; median ≈9.07 days |

Those clocks are **arithmetic to rounded saved locations**, not newly
conditioned medians. The current B values exceed a18, particularly for
minus; a new probability forecast must condition on the exhausted
interval. No model was executed here.

One day's raw line budget is approximately 1.063×10^24 for plus or
1.097×10^24 for minus. Reaching the saved median locations in one day
therefore needs approximately 10.9× or 9.1× end-to-end gains, respectively,
plus any startup, classification or certificate costs. The current
ceilings exclude both median locations.

The old model places 22% of plus a19 below M and 27% of minus a19 below
M if its proof ceiling is extended. These are model estimates from the
old floor, not certified probabilities or current conditional results.
At the current rates, travel to M is about 2.73 and 2.98 days. A fast
sieve alone would simply reach the old ceiling sooner.

The eleven recorded finds have mean E≈1.27; their ratios to saved median
locations range from 0.11 to 6.4, mean 2.5 and median 2.2. That history
does not justify treating a model median as a deterministic lower bound
or guaranteeing an automatic “2–3×” correction. PRL-004 bounds one small
numerical uncertainty, not the conjectural first-occurrence error.

## PRL-001: Amortize the sieve across wheel periods

**Status: exact representation transfer; substantial donor evidence,
no prime-ladders implementation or measured gain.**

[pladder_gpu.py](../pladder_gpu.py), module explanation and candidate
loop around 730–813, still reconstructs and tests candidates individually.
It already has compact tail queues, masks and exact root lists. The
missing representation is the later **period-window sieve**.

Use device coordinate z=k/U, physical period W, and device period
`Wp=W/U`. Let r be one allowed wheel residue and q a sieve prime not
dividing Wp. Let Kq be the exact killed residues **in z coordinates**:

`Kq = {−s (U p_i)^−1 mod q : q does not divide U p_i}`.

For a candidate `z=Wp(j0+b)+r`, put `d=Wp^−1 mod q`. Then

```
z mod q ∈ Kq
  ⇔ (j0+b+r d) mod q ∈ Cq,
Cq = {a d mod q : a∈Kq}.
```

For fixed r, the next P candidates are thus a P-bit slice of one periodic
pattern. One small-prime pattern read rejects many periods together.
The argument depends on the wheel progression, not on consecutive or
polynomial multipliers: arbitrary prime multipliers are compatible.
Deduplicate coincident roots and omit forms whose coefficient is zero
modulo q, since their constant ±1 cannot be divisible by q.
At n19 the first post-wheel q values 59,61,67 kill 17,18,18 residues;
the generic count 19 applies only for q>67.

For the existing CRT decomposition,
`r=(r1+W1 A)−W1 D+Wp·borrow`, the phase splits into a first-level
table, a second-level phase and the borrow. This is already implemented
in [factorial-ladders/fladder_gpu.py](../../factorial-ladders/fladder_gpu.py),
the derivation at 995–1028 and `window_patterns` at 1152–1190.
The pattern can group coprime sieve primes; use the inverse modulo the
group modulus and preserve the source's bounds on phase sums, tables
and queue indices.

The donor measurement is
[linear-ladders/OPTIMIZATION_LOG.md](../../linear-ladders/OPTIMIZATION_LOG.md),
v4 from line 864: **10.5–13× on frozen shapes, 8.8× at live filters**.
Its first build was only 4.6–6.2× against the properly pipelined baseline;
the final improvement included deeper in-block filtering. Transfer the
complete mathematical design, not an isolated bitmask instruction and
the final headline multiplier. Different survivor density and tail cost
can materially change the result here.

At current n19 the wheel counts are
`R1=61152, R2=456, R3=25375`, total `707589792000`,
with density about `2.17124×10^−8` per physical k.
Both signs have the same counts. That makes first-level phase tables
plausible, but their sizes and traffic still require later validation.
No new pruning occurs: this computes the same sieve more economically.

### Width, maximal unit and coverage constraints

For U=2310, `Wp=14107860812636383`.
A conservative PB256 bound is

`257 Wp + 65536 = 3625720228847615967 < 2^63`.

Thus the current physical wheel supports a broad narrow-record window
without a larger wheel or wider survivor record. At minus's frozen
U=210, `Wp=155186468939000213`; PB32 fits the existing signed
reduction bound, PB64/96 need a correctly proved full-uint64 reducer,
and PB128 exceeds even that range. Moving the now-forced 11 into the
unit makes **U=2310** and enables the broader representation.

This does not newly thin the search and is not the old unmeasured 1.1×
unit-change claim. The physical period remains W when a forced wheel
prime moves into U, but CRT ordering and partial launch indices change.
Use U=2310 only at filters where it is actually forced; the historical
minus n12 opening has U=210, and its canary/opening cases must retain
valid filter-specific units.

At the old plus rate, 32/128/256 periods close in approximately
85/339/678 seconds. Even a new multi-period coverage unit has modest
confirmation cost at n19 on this wheel. Preserve the absolute ceiling
and the final short interval rather than rounding a claim upward.
A current shape comparison must sweep the same absolute k interval;
equal j or equal launch counts do not define equal work after migration.

An 8.8× gain here would give about **29.7 hours** to the old plus median
location and **24.7 hours** to the old minus median location. Those
are hypothetical scalar calculations, not a transferred forecast.
They explain why this is a worthwhile one-day research candidate while
falling short of a demonstrated one-day result.

### Secondary wheel59 option and deferred affine alternative

After establishing the same-wheel port, a concrete larger wheel is
arithmetically feasible at U2310 with cutoff levels `(37,43,59]`:

| Quantity | Value |
|---|---|
| W1; combined W2 | 3212440751; 259106347 |
| Device Wp; physical W | 832363787945546597; 1922760350154212639070 |
| R1; R2; R3 at n19 | 1161888; 600; 42630 |

The level moduli and row counts fit the relevant bounds. Since q59
kills 17 classes, adding it reduces generated candidates by exactly
`59/42≈1.40476`. This is a candidate-count ratio, not a runtime multiplier
to apply to the donor's 8.8×.

Even PB32 requires `33Wp+65536=27468005002203103237>2^64`, so this
option needs a modern wide record carrying a per-period offset and
separate period index through every queue, tail and host reconstruction
path. At the old plus rate, PB32 closes in about 1.39 hours and PB256
in about 11.12 hours. The physical period is 59 times larger; lower
generation density does not erase this confirmation cost. A smaller
live-period count, tables and complete host work need joint pricing.
This is a feasible alternative under the stated representation, not
an established superior plan.

A more complicated exact alternative splits the two surviving classes
modulo 13: at n19, positive-sign k residues are 0,1 and negative-sign
residues 0,−1. Combined with forced 2310 this gives
`k=30030t+b`, with b=0 or 6930 for plus and b=0 or 23100 for minus.
Both classes must be swept. It removes 13 from the device modulus and
can accommodate a wheel to 61 with a noncontiguous prime partition, but
needs affine offsets, explicit prime sets, complete complementary
sieve coverage and multi-class checkpointing. It does not prune any
class the existing wheel retains. One finite construction has levels
`[17,19,23,41,53,61]`, `[29,31,37]`, `[43,47,59]` and
device Wp=3905707004975257109, so even a one-period representation
needs separate width analysis before it can become a broad window.
Its physical period 117288381359406970983270 takes about 2.65 hours at
the old plus rate, or about 85 hours for 32 periods. This makes it
deferred here; 30030 is not a forced divisor, so PRL-002 still uses
the proved U=2310.

**Future Claude validation:** retain the independent dense CPU sieve and
bare-definition oracle. Independently check transformed roots, each
pattern bit, CRT borrow/phase, both signs, unit 210/2310, final partial
words, all output paths and queue overflow fallbacks. Compare full
sorted survivor streams over identical absolute intervals, including
populated windows above 2^64 and near the proposed new ceiling.
Freeze new n19 shapes; [score.py](../score.py) 91–108 currently freezes
n14, n18 and minus n12, not either actual n19 front.

Version PB, levels, unit, class, reduction/record format and launch
enumeration. Adopt the numeric committed B, floor it into the new
enumeration, and replay uncommitted work plus any required floored
overlap. Preserve B as the proved boundary and suppress duplicate census
and claims below it. Existing adoption at launch 482–504 provides the basic
numeric-floor pattern. W equality alone is insufficient for accepting u.
Both saved cursors have u=0, simplifying this particular migration.

## PRL-002: Use the forced divisor to extend the proof ceiling

**Status: new mathematical ceiling theorem; available N+1 transfer
implements a previously known proposal. No certificate experiments run.**

Current `k_ceil`, [pladder_search.py](../pladder_search.py) 92–114,
uses M for plus because every factor of k<M is then a deterministic-MR
prime. For minus it still stops at the value proof crossing because the
old project had no N+1 certificate routine.

The stronger factor bound uses **mathematical forced divisibility**,
independently of which device unit happens to be configured. Suppose
eligible k=Ut, where all prime factors of U are below M. If

`k < U M`,

then t<M and every prime factor of k is either a factor of U or a factor
of t. Every such prime is strictly below M. Repeated factors and overlap
between U and t do not affect the argument.

For current n19, U=2310 is proved by the existing forcing lemma, so the
exclusive bound can be

`C_new = 2310 M = 7662371789410539861572176110`

(approximately 7.662×10^27). Equality is excluded: the generic argument
there only gives t≤M. This comfortably contains both recorded n19
median locations and the saved n20 median near 5.1×10^26.
It is a **range extension**, not faster search or a probability claim.

The factorization workload retains a useful bound too. Trial division
removes the small forced factors of U, so the remaining input is at
most k/U<M. The new 28-digit k does not force a larger-than-25-digit
residual factorization merely because of this extension. This is an
input-size statement, not a guarantee of bounded wall-clock factoring.

Use a proved filter-specific divisor: U2310 from n14, U210 at n12,
and the appropriate smaller unit at older canaries. Apply the forcing
argument only above the independently covered prime-equals-sieve-prime
exception zone. `k_proof(n,s)` remains the value-classification crossing;
it does **not** grow when the certificate ceiling grows.

For plus, `N−1=p_i k` is factored by adjoining p_i to the shared
factorization of k. For minus, `N+1=p_i k` has the same structure.
The shared [huntlib/certificate.py](../../huntlib/certificate.py)
now implements `_prove_plus` 486–503, `prove(...,fac_plus=...)`
519–581 and independent verification from 623. With a complete admitted
N+1 factorization, F=N+1 and `(F−1)^2>N` is automatic for N>1;
the required Lucas witnesses and their verification still have to succeed.

The old minus-ceiling proposal is explicitly recorded in RESULTS
250–258 and the project's log. The new opportunity is that this shared
routine now exists, as used by power-ladders. `launch.certify_run`,
319–363, currently supplies `fac=` only for plus; minus falls back to a
generic proof attempt. Supply the known N+1 factors directly for minus,
reverify every returned certificate and gate settlement as in PRL-003.

Future validation must pin strict ceiling arithmetic for both signs and
each applicable U, actual tested values rather than just filter labels,
certificate-side selection, malformed factor maps, wrong-sign factors,
and failure to find a witness. Preserve deterministic old evidence.
The ceiling, engine version, source documentation and all readers/gates
must agree; changing a constant alone is not the implementation.

## PRL-003: Make the proof and unit guards match their claims

**Status: correctness handoff, not a current measured optimization.**

`record_discovery`, launch 782, asks for `certs, unproved`, but
813–814 adds every claimed index to `found` even if some values remain
unproved. Lines 830–833 explicitly announce that the find stands.
A higher ceiling requires a durable unresolved-candidate barrier or
proved-prefix settlement; a failed bounded certificate attempt cannot
become a proved new term.

The sequence is at-least, so a verified prime prefix can settle the
indices it proves. An unproved later value cannot create a rider.
A composite stopper is necessary for an exact-run claim, not for
membership in a proved at-least prefix. This does not reproduce the
exact-index CENSUS-hiding issue of polynomial-runs: lengthening an
apparent at-least run cannot turn a true next-index hit into a shorter,
irrelevant index. All eleven saved discovery files have complete
certificate objects and no observed unresolved claimed value.

The current `assert_unit`, search 171–200, checks each prime divisor is
forced, then strips every power of that divisor. It can consequently
accept unit 4 at n14, although only one factor 2 is forced. The existing
[A084700 a14 evidence](../evidence/A084700_a14_24581646307811670.json)
has `k=24581646307811670≡2 mod 4`; an engine restricted to multiples of
4 would lose this recorded term. This is a static contract counterexample,
not a run of the faulty configuration.

Require the proposed unit to divide a certified squarefree forced
product, or independently justify every exponent. Current default
units 2310 and 210 are squarefree, so this does not invalidate them.
For the PRL-002 ceiling, the safe U is the mathematical divisor proved
for all eligible k, not any explicit unit accepted by the current guard.

Finally, the helper `forced_unit` at search 158–168 scans only
2,3,5,7,11,13. That suffices at the present n19 fronts, but is not a
general maximal-unit algorithm. At n27, 17 is also forced: the missing
classes 15,4,1 are supplied by p23=83, p24=89, p27=103. Thus a forced
product at n27 includes 510510, not merely 30030. A complete finite
candidate-prime scan needs only q≤n+1, since n coefficients cannot cover
q−1 nonzero classes when q−1>n. This is a future representation/helper
improvement, not additional current n19 thinning.

## PRL-004: Bound the model tail and preserve the domain

**Status: mathematical assurance, no direct runtime gain.**

For q>p_n all p_i are distinct nonzero residues, so wq=n. The model's
finite product at Q=200000 therefore omits a generic tail

`T_n = ∏_{q>Q}(1−n/q)/(1−1/q)^n`.

For Q>max(p_n,n), expand the logarithms:

`log((1−n/q)/(1−1/q)^n) = −Σ_{r≥2}(n^r−n)/(r q^r) ≤ 0`.

Bounding `1/r≤1/2`, summing the geometric series, then replacing the
prime tail by the integer tail gives

`−n²/[2(Q−n)] ≤ log T_n ≤ 0`.

At n19 the magnitude is at most **0.000902586**, or about **0.0903%**
in multiplicative intensity. This is far too small to account for the
multi-day depth requirement. It bounds truncation of this Euler product;
it does not prove Bateman–Horn, the Poisson first-hit model, its
quadrature, or a particular next-term probability.

Both signs share the **same singular series**, since negation maps
their killed sets bijectively. Their full density denominators
`∏log(p_i k+s)` differ slightly; that difference is tiny at these
heights, not an exact identity of densities. More importantly, mapping
k to −k leaves the positive search domain. Equal modular counts do not
transfer least terms or exhaustive positive coverage between families.

Coordinate compression also does not multiply the odds. When a forced
squarefree U is extracted and k=Ut, the series in t coordinates is
`S_t=U S_k`: each q dividing U changes the local surviving fraction from
1/q to 1, and other roots are permuted. The Jacobian `dt=dk/U` cancels
that factor, leaving the same predicted intensity per physical k.

All eligible classes are already represented by the exact killed sets.
No prime-power forcing beyond the established squarefree factors follows
from simple divisibility: a surviving class modulo q lifts to all its
classes modulo q^a as far as q-divisibility is concerned. Admissibility
is already immediate from k=0 modulo each q and gives the usual
conditional infinitude under Dickson's conjecture, not a new exclusion.

## Prior work and implementation order

The log already records tail compaction, masks plus exact lists,
in-block splits, host back-pressure, per-filter constants and unit-space
wheel53. Those are existing optimizations. Its previously rejected
mask/list variant and occupancy experiments are not reasons to rerun
tuning during a static review.

The old minus unit-change proposal promised about 1.1× but was not
measurably useful in the completed pointwise campaign. PRL-001 gives it
a different mathematical purpose: a broader window under exact word
bounds. The sparse tail is already implemented; it is not a new donor.
`follow_frontier`, launch 836–860, already carries fully classified
closed periods after all sorted pending candidates are handled.

For a future Claude task, first repair the unit/proof acceptance
contracts, then implement the N+1 and forced-divisor ceiling paths.
Port the periodic-window representation while retaining old full-stream
checks and adding both current n19 workloads. A speed result is relevant
only with the same absolute coverage, completed host classification and
certificate behavior. Update fingerprints only when the changed work
denomination is documented and equivalent absolute streams have been
compared.

The largest uncertainty is actual end-to-end window-port speed at these
two fronts. The mathematics proves applicability and a much larger
certificate range. It does not establish the approximately 9–11× gain
needed to reach the saved median depths in one day.

## Source and evidence hashes

All values are SHA256. The source snapshots include relevant donor files;
no sibling project was audited concurrently.

| File | SHA256 |
|---|---|
| pladder_reference.py | `8db92db63d09c209ec315c740b717b950b62c8dc914a44cbfae89d0cdd35d71e` |
| pladder_search.py | `b3467ee657f6f5f21f7f2a5779cb311723df238deff3a235751e47e47968f578` |
| pladder_gpu.py | `e02a0e89d47ffb5a6525545d945d4010a2d215f8643f82451bff76469b073417` |
| launch.py | `4ea0882ab9bd25c1c8c94f45ebaba2a81c90e6498b91629094f76978e352490c` |
| score.py | `9c644d879d107d16688ebe7410945616b550da9379ee9c2c746b9063947585a6` |
| pladder_model.py | `7f3aaf6637fdd5a9922b81e66fe30f4ac06b9113b684cfc1f320488d75c8fb50` |
| model_results.json | `07cf5c11a539dfc314a9b45c41c392c78ce0ea18dfd9942f0e35a569d297ef62` |
| OPTIMIZATION_LOG.md | `f110cbda7dab42938bcaf9748ca8b3a4eb24e44a100149df9f31ac64813fadcc` |
| BENCHMARKS.md | `3575ff1152c947803c57ad4b6ba9accab87e1d27cc7d6526c1ab7ed3fa648372` |
| RESULTS.md | `235a780752611b19f7136eeb77284de125e8eaf65e8f7bcc176d51a412b13686` |
| campaign_checkpoint_plus.json | `08b79da74e1c82979cd5ff84e3dad1bc018f4b782c7622d76f8e32b5f94a21cb` |
| campaign_checkpoint_minus.json | `92cb64a1f04bceadb87d7988ee21b729ac03e54e4b63059d66456a9bc40715b7` |
| ../huntlib/certificate.py | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
| ../huntlib/primes.py | `d8cb255728a99c23540bb1af545c0d8d6d88cc400556e470c32fce7e28ea8d3f` |
| ../factorial-ladders/fladder_gpu.py | `1a1a2c5a639488e0bbb75585c7e06d29857f24917dd47641e8e5723bbd0c7668` |
| ../linear-ladders/OPTIMIZATION_LOG.md | `de67c4ec3d805a80b3e43d99a3cd7847d9fdde379d2a469ff514135050f3faea` |
| evidence/A084700_a14_24581646307811670.json | `8dca1d6a15ae60501b23a76e714d3705d78d498f4285091643bf04267230cc64` |
| evidence/A084700_a15_1183192161007235610.json | `4eae3323de2a6319aaa348cda39a2180016e71386edff400c34c6bb28c27373b` |
| evidence/A084700_a16_161515890673488267840.json | `8acb73f695a770ee17411385f6da74fdbc543ae0b2bc48fdc0c37d202f6ec373` |
| evidence/A084700_a17_2446970377116913184460.json | `45972e669fe96a72e540adb5c3a045191891bafb81ddd96e3d1cc0e6a9622e1e` |
| evidence/A084700_a18_416266897501398851227320.json | `78b906a99a77650dfd0bf4814700696a3068385783d85dc4f798a1592309f5db` |
| evidence/A084701_a12_43708752888360.json | `4f43c9567dcb7c27ac9d2d6ffd2d64648ef14e656a67910400d9dc6da30efdef` |
| evidence/A084701_a13_2276961234558570.json | `7c735fb1e198fe13f188d3d7bdfd19ec9b0cd857d8e36eb15f05678ef2f7c91e` |
| evidence/A084701_a14_165784683394437030.json | `306bbdb0b1c7e396b86795a09d6840407458cf8d8c124ebcac6b2cc06674135b` |
| evidence/A084701_a16_16739777598441148020.json | `c49c846906b324515d98f8cb0666925614a19080e4bb1a25a76e6ca85a11c161` |
| evidence/A084701_a17_9050934616476845605590.json | `15382b514fd56d04cbb713ca160b3cb66719d2e2663cbc22b38c15e05b7e06a6` |
| evidence/A084701_a18_23562434281685500120920.json | `ceac831756a2b0a0a8dd97750239c89379f2c02e7023bea84774d8837d9f5a7c` |
