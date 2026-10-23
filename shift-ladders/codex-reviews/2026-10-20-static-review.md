# Shift ladders: static mathematical review

**Author:** Codex (OpenAI). **Date:** 2026-10-20.
**Scope:** A130003 and A110096, named related entries, all five public
Python roles, model, evidence, checkpoints and optimization history.
The review team examined this project only, consulting later factored
engines as specific representation references.

This follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex is always
static in this role: no GPU use, project imports or execution, models,
oracles, tests, benchmarks, searches or primality experiments. Only
documentation was edited. Arithmetic below uses stored data or explicit
finite formulas. Existing certificates and measurements were read,
not independently rerun.

**Conclusion.** No supported new change makes either saved median a
one-day target. From the saved completed boundaries, the recorded median
locations require about **30.1 and 17.7 days** at the preceding campaign
rates. The current filters have not received equivalent sustained-rate
measurements. Base 2 also encounters the current proof ceiling well
before its median.

A factored wheel is a concrete representation worth reconsidering now
that the search is much deeper than when it was rejected. It removes
repeated generation work, but the existing engine already uses periodic
bit planes and compaction; there is no missing generic window-sieve
speedup to claim. Proof-range extension is already documented unfinished
work. The new tail bound shows that singular-series truncation is much
too small to explain a factor of eighteen or thirty.

## Definition, provenance and actual state

HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`, with documentation
edits in the worktree. Source/data hashes below pin the reviewed snapshot.
Links identify symbols and snapshot line numbers.

| Entry | Definition in its own notation | Current open index |
|---|---|---:|
| A130003 | Least positive m with m + 4^k prime for every k=1..n | 22 |
| A110096 | Least positive k with k + 2^i prime for every i=1..n | 20 |

These are **at-least** conditions. Neither requires the next shifted
value to be composite. Conditions nest, so the sequences are nondecreasing;
one value can settle several indices. The stopper in evidence proves the
recorded run's end and explains why no additional rider was claimed.
It does not change either entry into an exact-run problem.

For common formulas below write x for the candidate, b for 2 or 4,
and f_i(x)=x+b^i. This notation is explanatory; evidence and proposed
implementation output must retain each entry's own letters.

The [reference](../shiftladder_reference.py#L16) already proves
K(q,n,b)={−b^i mod q:1≤i≤n}, with size 1 at q=2 and
min(n,ord_q(b)) at every odd prime. Thus every tuple is locally admissible.
Base 4 has ord_q(4)≤(q−1)/2, so no odd prime forces a single residue.
For base 2, the complete criterion for a forced zero residue is
ord_q(2)=q−1≤n. This is already represented by the exact killed sets;
extracting a forced divisor does not give a second density reduction.
Prime-equality exceptions remain outside the production sieve and must
retain independent low-range or monotonicity coverage.

### Discoveries and evidence

| Family | Recorded new terms | Latest term |
|---|---|---:|
| A130003 | a(19), a(20), a(21) | 285,661,075,490,357,310,517 |
| A110096 | a(17), a(18), a(19) | 564,052,872,977,379,795,315,735 |

The [base-4 ledger](../evidence/a130003_discoveries.json) and
[base-2 ledger](../evidence/a110096_discoveries.json) reference all six
records. Latest evidence is
[A130003 a(21)](../evidence/A130003_a21_285661075490357310517.json) and
[A110096 a(19)](../evidence/A110096_a19_564052872977379795315735.json).
Together the six files contain 114 required-value certificates, all
within the deterministic MR range according to the recorded verification.
The latest stoppers have displayed factors 67 and 29 respectively.
RESULTS records independent re-verification from disk; Codex did not
repeat it. OEIS statements in old documents describe their dated export,
not a new check of current submission status.

The source [KNOWN tables](../shiftladder_reference.py#L109) still stop at
n18/n16. Campaign frontiers combine them with checkpoint discoveries;
the standalone model artifact remains the original opening forecast.
Historical source-only shapes therefore must not be mistaken for current
n22/n20 workloads.

### Complete saved coverage, not a fractional residue cursor

| Family | Saved timestamp | j | W | Completed exclusive boundary B |
|---|---|---:|---:|---:|
| A130003 | 2026-09-01 04:04:22 | 44,153,733,121 | 6,469,693,230 | 285,661,108,252,160,470,830 |
| A110096 | 2026-08-27 11:49:14 | 1,853,939,112 | 304,250,263,527,210 | 564,061,463,389,401,695,237,520 |

Sources: [base-4 checkpoint](../campaign_checkpoint_b4.json) and
[base-2 checkpoint](../campaign_checkpoint_b2.json).
The boundaries are slightly beyond the last terms. Unlike a factored
interleaved cursor, this engine returns every residue of each completed
period in a launch. Its [`sweep`](../shiftladder_gpu.py#L1018) and
[`swept_m`](../launch.py#L379) use jW as the committed numerical boundary.
No pending partial-u field exists in these checkpoints.

The old-filter survivor stream is sufficient after promotion because the
new shifted forms contain all the old ones. The launcher continues
classifying all returned survivors, with its classification cap derived
from the live frontier for each candidate. There is no old fixed cap
attached to pending tuples here. With the default fixed p1, W is unchanged
by n; a donor that changes W must not assume this transition remains safe.

The configured sieve depth is 65536. Flat wheels stop at 29 for base 4
and 41 for base 2; later primes are bit planes over the existing period
index, not factors of W. Plane depth and launch size are derived from
the current filter. Published values such as p2=103/137 and launch widths
4096/2048 belong to the measured preceding configurations, not a new
execution of the n22/n20 planner in this review.

## Rates, forecasts and one-day constraints

The relevant [sustained campaign rates](../BENCHMARKS.md) are
1.13e15 m/s at base-4 n21 over 67.9 hours and 1.53e19 k/s at base-2 n19
over 10.2 hours. They include host work. They are **previous-filter
measurements**, used below only as surrogates for n22/n20.

The later paired pass also tested a base-2 n20 engine, but its result was
a ratio within noise, not a sustained current-filter absolute rate.
Frozen [score shapes](../score.py#L100) use n19, plus a smaller n10 shape;
they do not independently establish current n22/n20 prices.

The latest [RESULTS forecast](../RESULTS.md#L421) was conditioned on the
latest terms. The extra completed line B−a(last) is small, but a fresh
conditional forecast at B was not run. These are fixed-distance scenarios
to recorded targets, not newly evaluated probabilities:

| Current target | Recorded Q1 | Recorded median | Q1 distance / old rate | Median distance / old rate |
|---|---:|---:|---:|---:|
| A130003 a(22) | 1.15e21 | 3.22e21 | 8.85 days | 30.06 days |
| A110096 a(20) | 7.39e24 | 2.39e25 | 5.16 days | 17.65 days |

Thus reaching those Q1 locations in one day requires approximately
8.85×/5.16× throughput; reaching the rounded medians requires
30.06×/17.65×. A one-day continuation at the old rates would reach about
3.833e20 and 1.886e24 before rounding to completed launches. Both are
below their recorded Q1 locations, and both remain below the current
MR ceiling. No candidate-count factor below establishes those rate gains.

At the historical launch widths 4096/2048, full launch spans are
26,499,863,470,080 and 623,104,539,703,726,080, costing approximately
0.023/0.041 seconds at those rates. Sixteen-launch checkpoint intervals
would cost about 0.38/0.65 seconds. This arithmetic is not a current
configuration measurement; it shows why ordinary confirmation latency
was negligible before any large-wheel redesign.

For base 2, the current exclusive ceiling is
3,317,044,064,679,887,384,913,405 at n20. The old rate traverses the
remaining permitted line in about 2.08 days. The saved model assigns
only 13.4% probability below that ceiling and places the median far beyond
it. These are separate limits: a faster sieve shortens permitted travel,
whereas certification expands the range that can be claimed.

The model source still recommends a generic historical 2–3× multiplier,
but the project's six new draws give mean E≈0.81 and a broad recorded
interval containing 1. Neither a universal correction nor a guaranteed
conservative median follows. Rider terms are not independent draws.
No new first-occurrence model or empirical correction was fitted here.

<a id="shl-001"></a>
## SHL-001: reconsider a factored wheel at the deeper frontier

**Disposition: Proposed.** This is a reconsideration of documented
unfinished/rejected work under changed search depths, not a claim that
the current engine lacks periodic masks.

The [existing bit planes](../shiftladder_gpu.py#L325) already use

    x = Wj+r,
    q kills x iff (j + r/W) mod q belongs to K(q)/W.

Division here means multiplication by W inverse modulo q. The engine
combines 32 period positions per word and compacts survivors between
tests. A generic transplant of another project's window sieve would
repeat this implemented idea.

The remaining structural possibility is to generate fewer flat-wheel
word positions using a factored CRT wheel. The original
[coverage objection](../OPTIMIZATION_LOG.md#L127) compared a period
around 6.1e17 against the old a(19) median 5.75e16. Today's a(22) median
is around 3.22e21. The later [two-level rejection](../OPTIMIZATION_LOG.md#L855)
also depended on the old flat-row slot bound and poor amortization at
short period windows. A modern three-level construction changes those
constraints, but does not by itself prove a favorable clock.

### A concrete base-4 n22 construction

Write the odd candidate as x=1+2t. For odd q the forbidden t residues are
(−1−4^i)/2 modulo q. This is a bijection of residues; it preserves the
original condition and its prime-equality exception zone.

Use three prime sets:

| Level | Primes | Modulus | Allowed rows at n22 |
|---|---|---:|---:|
| 1 | 3,5,7,11,13,17,19,23 | 111,546,435 | 1,572,480 |
| 2 | 29,31,37 | 33,263 | 7,410 |
| 3 | 41,43,47 | 82,861 | 27,900 |

The combined second/third modulus is 2,756,205,443 <2^32, and the
unit-coordinate wheel is W′=307,444,891,294,245,705 <2^63.
Physical period W=2W′=614,889,782,588,491,410. All secondary row counts
fit uint16 and the first-level count fits the later engines' usual row
budget. These are finite CRT counts and representation bounds only.

Relative to the present flat wheel through 29, the extra flat factors
31,37,41,43,47 reduce generated word positions per unit of line by

    (31/26)(37/19)(41/31)(43/36)(47/25) = 6.8957647...

The existing bit planes already enforce these primes. Therefore this
factor removes repeated **generation work**, not additional final sieve
survivors, and is not an end-to-end speedup. CRT reconstruction, phase
tables, queues and later tests may consume the saving.

A 32-period segment spans about 1.968e19 of the candidate line and costs
4.84 hours at the old base-4 rate; 128 periods cost 19.35 hours before
any speed gain. Under unit-coordinate records, 33W′+65536 fits uint64
but exceeds 2^63, so even PB32 needs the later full-uint64 reduction proof
or wide records. PB64 exceeds uint64 in a narrow combined offset.
Transplanting only the CRT tables into the current physical-offset
reducer is insufficient. A wide (within-period offset, period index)
record must survive every queue, tail and output reconstruction stage.

The present proof-height and one-day constraints require comparing
complete confirmed intervals, not only generated line rate. A segment
near one day is an unattractive default even if its kernel is faster.
Keep shorter live windows and a small-wheel fallback in the comparison.
No transfer rate or favorable current plan has been measured.

### A concrete base-2 n20 construction

Above the exception floor, the current base-2 conditions force odd
multiples of 3·5·11·13·19=40755. These are precisely the odd primes
q≤21 for which 2 has order q−1. Write the candidate in its own entry's
letter as k=40755+81510t. The forced class is already encoded in the
current flat wheel; normalization only reduces the device-coordinate
modulus. For q not dividing 81510, transform killed residues by
(K−40755)/81510 modulo q.

A full-59 construction in this coordinate is:

| Level | Primes outside the forced class | Modulus | Allowed rows at n20 |
|---|---|---:|---:|
| 1 | 7,17,23,29,31,37 | 91,040,831 | 1,718,496 |
| 2 | 41,43 | 1,763 | 609 |
| 3 | 47,53,59 | 146,969 | 34,749 |

The combined second/third modulus is 259,106,347; W′ is
23,589,257,148,254,357. The physical period remains
81510W′=1,922,760,350,154,212,639,070. The first count is below 2^21,
the later counts fit uint16 and both component moduli fit uint32.
PB96 has conservative bound 97W′+65536=2,288,157,943,380,738,165,
which is below 2^63 as well as 2^64. Its complete physical segment
is 184,584,993,614,804,413,350,720, about **3.35 hours** at the old
base-2 rate. That time is arithmetic, not a donor measurement.

Relative to the existing flat wheel through 41, the generated-position
factor is (43/29)(47/27)(53/33)(59/39)=6.27125. Again, the existing
bit planes already reject these primes. This is not another 6.27-fold
thinning of the complete sieve or a measured speedup. In particular,
normalization does not multiply the model's physical intensity: the
local singular constant in t is 81510 times the one in k, canceled by
dk=81510dt.

The [later affine-class engine](../../plus-two-cliques/plus2_gpu.py#L102)
already expresses the needed root transformation and factored geometry.
Its [constructor bounds](../../plus-two-cliques/plus2_gpu.py#L2403)
and [record dispatch](../../plus-two-cliques/plus2_gpu.py#L2452) are
relevant references, not an unchanged engine that can simply be imported.
Both listed partitions are contiguous after removing their class primes,
so they do not need arbitrary unordered-prime partitions. Preserve the
direct definition oracle, independent optimized CPU construction, and
all small prime-equality exceptions when introducing class guards.
The donor contract requires PB to be a multiple of 32 no larger than
256, W1 and combined W2 below 2^32, W′ below 2^63, and R2/R3 no larger
than 65535. Its 32-slot killed-root bound covers these n22/n20 filters;
higher filters need their own degree/count guard. Preserve the launch
grid cap and overflow fallback rather than relying only on the row-count
arithmetic above.

### Coverage and validation requirements

There is a concrete fresh-start trap. The current
[initializer](../launch.py#L263) rounds upward past the first whole
wheel period. That skipped interval is below the old published
monotonicity floor with the current wheels. With full47 it contains the
recorded a(19)=13,268,589,982,417,023. Simply changing the default wheel
would create a fresh-start hole.

Start at the containing period with an explicit numerical lower clip,
or normalize the settled frontier with verified provenance and cover the
remaining gap. The [current low-floor refusal](../shiftladder_gpu.py#L1037)
also needs a deliberate way to handle the containing first period.
Preserve the independent oracle and small exception coverage; never
solve the mismatch by making the oracle apply the optimized wheel.

For saved state, retain B as the completed absolute boundary. Floor B
into the new physical period, replay the containing overlap as needed,
suppress duplicate census below B, and never round B upward. A factored
enumerator needs separate work and complete-coverage cursors: partial
CRT classes do not certify a numerical prefix. Store its full geometry,
active endpoint and filter identity. Commit only after all classes and
required proofs through the endpoint are resolved.

Promotion has an additional denominator trap. The current
[discovery handler](../launch.py#L482) replaces self.eng while the
[old generator](../launch.py#L543) is still active, then writes its jn
into the campaign cursor. W is constant today, so the units agree.
A donor that replans W on a find must first drain the old generator with
its old W and translate the completed **numerical** boundary, or cancel
and safely replay. Writing an old period index against a new modulus
would manufacture coverage. Reuse under form nesting does not excuse
that coordinate conversion.

Future acceptance should retain original fingerprints and add current
n22/n20 absolute-window workloads. Compare the complete survivor stream
at the same q2, including arbitrary endpoints, multiple launches, forced
overflow fallbacks, affine output reconstruction and checkpoint replay.
Changing W changes period counts, not the mathematical interval that the
parity comparison must cover. Reject the donor if confirmed-clock gains
do not justify its construction and longer coverage units.

<a id="shl-002"></a>
## SHL-002: expand the proof range without weakening acceptance

**Disposition: Proposed.** Range extension is already named in
[RESULTS](../RESULTS.md#L448); the static contribution is to make its
mathematical and source obligations concrete. It is not a new sieving
reduction and has no measured certificate cost at the next median.

The current [k_ceil](../shiftladder_search.py#L63) is the exclusive bound
M−b^n, where M=3,317,044,064,679,887,385,961,981 is the deterministic
MR bound. It guarantees required values x+b^i<M for i≤n.
It does not guarantee that every higher value examined by an extended
run classifier is below M. The launcher classifies through a live
filter+6 cap, the CPU run helper defaults to cap64, and CPU hunt defaults
to n+8. A current cap hit makes verification demand a stopping composite
where none has been established, so it can alarm on a valid longer run;
this is fail-closed behavior, not a silent accepted exact length.

The [verification path](../launch.py#L184) checks MR, independent BPSW,
an independent CPU resieve and the stopping composite. In fact
[record_discovery](../launch.py#L440) already calls certificate.prove
for every claimed prime. The missing work is more than an import:
returned certificates are not checked for absence or independently
verified before the found table is mutated at lines466–467.
All recorded historical values are below M; this identifies a future
acceptance requirement, not an erroneous recorded term.

Before raising the ceiling:

1. Bound the **actual values** being claimed, including any rider beyond
   the sieve filter. Treat a cap hit as a lower bound, not a composite
   stopper. Extend it or retain an unresolved classification.
2. Below M retain the deterministic route. Above M use probable-prime
   tests only as one-sided screens, then require a certificate for every
   required prime and independently verify each certificate.
3. On unresolved proof, retain the candidate and block promotion and
   coverage past it. A checked composite can be rejected; failed bounded
   factorization alone is not compositeness.
4. A valid at-least prefix may be certified without claiming an exact
   longer run. Keep unresolved riders and exact census metadata separate.
   The first qualifying candidate cannot be silently skipped.

The shared [certificate machinery](../../huntlib/certificate.py#L519)
supports bounded partial factorization on N−1 and N+1. These shifted
values do not share the fully factored multiplicative structure that
makes several other projects cheap to prove. For x+b^i, both adjacent
integers depend on x; forcing x divisible by small primes does not make
either neighbor fully factored. A known forced-divisor ceiling theorem
for multiplicative ladders does not transfer.

Thus a high term ceiling requires a measured, independently checked
certificate path for these additive values, with explicit unresolved
behavior. A generic 1e40 default from another project is not evidence
that its hard cofactor cases are affordable here. Preserve the existing
ceiling until that path is validated in a later authorized task.

Because these are at-least families, the exact-run CENSUS-hiding issue
from polynomial-runs does not apply: a one-sided probable-prime pass can
lengthen an apparent run, but cannot make a genuine required prefix fail.
It still cannot justify a proved longer prefix without certificates.
Near-ceiling tests must exercise extension beyond n, a cap hit, missing
certificates, altered certificates, proof failures and resumed barriers.

<a id="shl-003"></a>
## SHL-003: bound the geometric-orbit model tail

**Disposition: Proposed** as model assurance and documentation, not a
search acceleration. The [model](../shiftladder_model.py#L94) computes
the correct finite killed counts through Q=200000 but gives no tail bound.

For odd q, collisions among shifts b^i occur only when q divides a
difference. Since

    b^j−b^i = b^i(b^(j−i)−1),

the smooth power of b is irrelevant to the odd-prime tail. Put

    Δ = product over d=1..n−1 of (b^d−1)^(n−d).

Every missing distinct root can be charged to a colliding pair, so
n−w(q,n,b)≤v_q(Δ). For q>Q>n, compare its local factor with the generic
factor G_q=(1−n/q)/(1−1/q)^n. The generic logarithmic tail is nonpositive
and at least −n²/[2(Q−n)]. Collision corrections are nonnegative and
at most logΔ/[(Q−n)logQ], using the product's total prime valuation.
Consequently the omitted log product T satisfies

    −n²/[2(Q−n)] ≤ log T ≤ logΔ/[(Q−n)logQ].

Without factoring Δ,

    logΔ ≤ log(b) sum d(n−d) = n(n²−1)log(b)/6.

At the current filters, outward-rounded bounds are:

| Filter | Bound on logΔ | Omitted log product interval |
|---|---:|---|
| Base4 n22 | 2455.128 | [−0.001211, +0.001006] |
| Base2 n20 | 921.886 | [−0.001001, +0.000378] |

This is roughly a tenth of a percent of singular-series normalization,
not a bound on the BH conjecture or Poisson first-occurrence model.
It cannot explain the one-day multipliers above. There is no subtraction
of at-least intensities here, so the exact-run cancellation caveat does
not arise. Higher n needs its own bound, and small primes must always
retain the actual order-based local factor.

A future model update can report this interval beside the finite product,
retain historical forecast files, and distinguish latest-term conditioning
from conditioning at the completed cursor. No model was rerun here.

## Relations, rejected alternatives and prior work

The even-exponent subset proves A130003(n)≤A110096(2n).
At the current base-2 n20 target this only invokes base-4 n10, already
settled far below the base-2 boundary. It supplies no stronger current
floor. The odd-exponent half consists of x+2·4^j, not x+4^j;
dividing by two does not preserve prime values or the odd candidate
domain. No affine identification of the two current searches follows.

The reference already names the two related entries below. Official
OEIS definitions were checked through search output; internal-page
retrieval was unavailable, so this review makes no claim about current
b-file completeness or which values still need submission.

- [A165235](https://oeis.org/A165235) satisfies
  A165235(n)=A110096(n+1)+2 for n≥1. Put p=k+2: its shifted prime
  conditions are the same tuple with indices translated. The case p=2
  would give k=0, which fails once the base-2 tuple has two conditions,
  so it does not disturb this positive-domain bijection.
- [A193109](https://oeis.org/A193109) asks for an exact run and allows
  k=0. Its a(1)=0 is an exception to the positive-domain identification.
  For n≥2, k=0 fails at the second exponent. Thus the least at-least
  term is also the least exact-n term **when its run stops at n**.

All three stored base-2 discoveries have exact runs, with stopper factors
19,157,29. They therefore imply the following six derived values without
another sweep:

| Evidence source | A193109 exact-run consequence | A165235 translated consequence |
|---|---|---|
| A110096 a(17) | a(17)=305948728878647722725 | a(16)=305948728878647722727 |
| A110096 a(18) | a(18)=760056834873121351995 | a(17)=760056834873121351997 |
| A110096 a(19) | a(19)=564052872977379795315735 | a(18)=564052872977379795315737 |

These are consequences of existing evidence and an already named
relation, not six newly searched terms or an assertion that they are
unsubmitted. A future evidence export can cite the original certificate
and leastness records while stating the index/domain proof. A plateau
minimum with run r settles the exact family at r only, not every smaller
index whose at-least term shares that minimum. An independent hunt for
still-open exact indices would need exact-index proof-safe classification;
the present at-least launcher is not such a hunt.

Already implemented work includes the period-index bit planes, compacted
round chain, tail compaction, vectorized base fold, adaptive launch sizing,
the live-frontier model cache and the effective-root-count wheel cache.
The 3.47×/2.42× host-cache fix is shipped. Recommending it again would
misrepresent the current source. Likewise the later 1.537×/2.380× pass
already corrected the wheel cost model and enlarged the useful flat
wheel/plane combination.

The final [optimization record](../OPTIMIZATION_LOG.md#L960) rejected
64-bit plane loads, the warp shuffle, locality ordering, deeper queues
and several schedule variants. Replacing a load with a dependent operation
was repeatedly measured worse. Generic hardware tuning is outside this
review, and the named small unsearched phases do not support an eighteen-
or thirty-fold end-to-end claim.

No extra fixed-prime exclusion beyond the existing order criterion was
proved. Prime-power lifting does not add a necessary restriction to
primality once a value is known nonzero modulo the underlying prime.
Sparse algebraic input exclusions do not remove a positive-density share
of these enormous intervals. A complete-segment reuse transplant is also
unnecessary: the current launcher already continues through the sorted
old-filter stream and carries completed coverage under nesting.

The practical handoff is bounded: consider the factored representation
with explicit completion costs, establish a fail-closed additive proof
path before extending the range, and improve forecast qualification.
There is no supported one-day next-term promise. Nothing in this report
authorizes project execution or a campaign start.

## Snapshot hashes

SHA256 values pin source/data read on 2026-10-20. Project README navigation
was edited separately and is excluded from this snapshot.

| File | SHA256 |
|---|---|
| `shiftladder_reference.py` | `bfab07f74513321537a30395ad6739fd994382dbc21aa2e51231cad6d5b09e2c` |
| `shiftladder_search.py` | `494f1ebaa9bce91ab8266f2b7259ebd55a8341635d77f6b048bd3141a61476bd` |
| `shiftladder_gpu.py` | `9397a38934fd9cc0338397f35dbe60f1d7d24eecfb916bbba9adee307c4449ae` |
| `launch.py` | `457906c9a73127730fd8a3ae41871cde804466feade3c37619e66eb8335fcf23` |
| `score.py` | `529ee4c138795347f14ca825f236edac9be1106f417564a87bc0759ece867d51` |
| `shiftladder_model.py` | `62729349959b7ee505475bcf61aa841122eefeb7a5075eacc0342d869403695d` |
| `model_results.json` | `549016f842c2002f46cfc16adfb200a11cd649c36c66a5f706768526bbca61e5` |
| `campaign_checkpoint_b4.json` | `3a2d6fd7af7c15a235df72b9072f454b2c5292a4a9690bcb436f997e1a9d5d9b` |
| `campaign_checkpoint_b2.json` | `2668c49e86ef2e7971a3cd6afa2bf77a0c0099efe4894927b3a9b85649be286c` |
| `RESULTS.md` | `c24a98b204b665a029d35c380252423406924a8fa7f2c8bd040e6b20ab4c8771` |
| `BENCHMARKS.md` | `26b99e47c6006a83261da88244b7aaae0509fcabf08125d061a39b88c6f625e2` |
| `OPTIMIZATION_LOG.md` | `75c442115ab3b5a17aa0ec43c1505f9aa2b7e50f915662d9342215e4200fb310` |
| `evidence/a130003_discoveries.json` | `0468b5cfb75b16a65d65cfa7ef6009efd4c3e3c098d70add434c2c13ae5fd66a` |
| `evidence/a110096_discoveries.json` | `ffdddaa120703a7fc09a3ffdbebd1c5ddeb1221be064ae3233bfd292baf61887` |
| `evidence/A130003_a21_285661075490357310517.json` | `c6c1c55013b9ffaf8e3202bc22b5244b29672dd8de9e818c8fbd9b6c3af0ab36` |
| `evidence/A110096_a19_564052872977379795315735.json` | `54694dd0fcd0f6cf0397dc63ff2d7936c246ce078fd06ac5089509b3d2db99da` |
| `../huntlib/certificate.py` | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
| `../plus-two-cliques/plus2_gpu.py` | `82d0fdd9995cdf6bd1eeb4385ef281e361446a92ba31d57dd67c0621c593ce10` |
