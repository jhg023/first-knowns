# Primorial AP: static mathematical review

**Author:** Codex (OpenAI). **Date:** 2026-10-20.
**Scope:** A053647, its recorded discoveries, the current a(19) target,
all five public Python roles, model, evidence, checkpoint and optimization
history. The review team examined this project only.

This follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex is always
static in this role: no GPU use, imports or execution of project code,
oracles, models, tests, benchmarks, searches or primality experiments.
Only documentation was edited. Arithmetic below uses stored numbers and
explicit finite formulas; certificates and historical timing claims were
read, not rerun.

**Conclusion.** The strongest new algorithmic lead is to avoid the later
sieve work on bitmap words already completely rejected by a short dense
prefix, then test survivors using the AP's exact interval of normalized
roots. This changes repeated mathematical work, not the set of admissible
candidates. Its work bound is substantial, but no measured gain establishes
a one-day a(19): reaching the saved first quartile requires about **9.35×**
the recorded rate, and reaching the saved median about **23.1×**.
The present engine already implements periodic word tables.

There is also an actionable coverage-contract issue: the small-value pass
is not performed per new difference, and its endpoint does not meet the
aligned engine start. This report does not exhibit a missed AP or disprove
the recorded values. It identifies what the current source does not
establish for a contiguous least-term claim.

## Snapshot, definition and actual frontier

Repository HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`; the worktree
contained documentation edits. Hashes at the end pin the reviewed files.
Line references are snapshot locations as well as named symbols.

Write \(D_n=\prod_{i=1}^n p_i\), the product of the first \(n\) primes.
A053647(n) is the least prime \(p_1\) for which
\[
  p_1,\ p_1+D_n,\ldots,p_1+(n-1)D_n
\]
are prime. It asks for **at least** \(n\) prime values, not a composite
stopper at the next value. Different indices use different differences.
The known a(7)=7937 and a(8)=7703 already rule out monotonicity.
See [reference definition and known table](../ap_reference.py#L1),
`difference` at line 99, and `full_verify` at
[launch.py:372](../launch.py#L372).

| Index | Stored least term \(p_1\) | Recorded run under its own \(D_n\) | Evidence |
|---|---:|---:|---|
| 16 | 116781362669989 | 16 | [a(16)](../evidence/ap_a16_p116781362669989.json) |
| 17 | 2097209048106247 | 19 | [a(17)](../evidence/ap_a17_p2097209048106247.json) |
| 18 | 14042451608819603 | 18 | [a(18)](../evidence/ap_a18_p14042451608819603.json) |
| **19** | **Open in the repository** | Independent new filter | [checkpoint](../campaign_checkpoint.json) and [target_n](../launch.py#L328) |

The evidence contains 16, 17 and 18 required-value certificates respectively,
all labeled `deterministic-mr`, with `agree: true`. The a(17) overshoot is
a 19-term progression with \(D_{17}\); it does **not** settle a(18) or a(19).
The source's `CAMPAIGN_FOUND` at [launch.py:102](../launch.py#L102) records
all three discoveries even though the reference's original `KNOWN` table
ends at 15. The September 29 OEIS export mentioned in
[RESULTS.md](../RESULTS.md#L38) is historical evidence, not a new check of
the current website or submission status.

The saved checkpoint has:

| Field | Snapshot value / meaning |
|---|---|
| `n` | 18; the transition after the last discovery has not run |
| `next_u` | 468082715787598 |
| Numerical exclusive boundary \(30\,\texttt{next_u}\) | **14042481473627940**, under \(D_{18}\) |
| `found` / `hits` | Terms 16–18 / 3 |
| `canaries_done` | true |
| `survivors` | 1984305704 accumulated over the three stages |
| `best_depth`, `best_p` | 18, 14042451608819603 |
| `wall_s` | 17816.143181800842; historical undercount, not a usable rate |

The surviving census is the **n=18** census, with depths 6 through 17.
There is no saved partial-launch index or pending survivor cache: the
launcher persists completed classified segments. A segment ahead may have
been in flight at interruption, but it does not create checkpoint coverage.
`production` at [launch.py:518](../launch.py#L518) selects n=19 on resume;
`stage_reset` at [line 276](../launch.py#L276) resets its cursor and census.
There is **no saved n=19 coverage** to subtract from its model quantiles.
The small-value qualification in PAP-002 applies even to the old claimed
boundaries; do not silently replace it with an assertion of coverage from 2.

### Current representation, exceptions and proof crossing

The campaign configuration is n=19 on its next stage, depth 8192, three
classification workers, and a mod-30 bitmap with eight coprime lanes.
The GPU carries \(p_1=\text{base}+\text{offset}\), with an arbitrary-precision
host base and a u64 offset; it never needs to form a 26-digit start on the
device. `LAUNCH_U=2^27` and `SEG_LAUNCHES=64` give
\[
 S=30\cdot2^{27}\cdot64=257698037760
\]
of \(p_1\)-line per classified segment. See
[ap_gpu.py:89](../ap_gpu.py#L89),
[GpuEngine.survivors](../ap_gpu.py#L554) and
[engine_span](../launch.py#L182). Some nearby comments still describe an
older, smaller launch; the executable constants give the span above.

For a sieve prime \(q\), the forbidden start residues are
\[
 F_q=\{-jD_n\bmod q:0\leq j<n\},\qquad
 |F_q|=\begin{cases}1&q\mid D_n,\\n&q\nmid D_n.\end{cases}
\]
The second case has \(q>p_n>n\), so there are no repeated roots.
CPU construction is direct modular multiplication
([ap_search.py:95](../ap_search.py#L95)); the GPU constructs the same set
by repeated subtraction ([ap_gpu.py:150](../ap_gpu.py#L150)).
The oracle independently tests actual values
([ap_reference.py:146](../ap_reference.py#L146)).

A small prime divisor only proves compositeness when the value exceeds
that prime. The engines therefore refuse starts below
\(F=\max(10000,q2)\). Since all offsets are nonnegative and all sieve
primes are strictly below q2, the rejection is sound above that floor.
The exceptional prefix must be handled independently; increasing a wheel
or sieve range cannot erase this obligation.

For n=19,
\[
 D_{19}=7858321551080267055879090,\quad
 18D_{19}=141449787919444807005823620.
\]
The deterministic MR bound is \(M=3317044064679887385961981\).
Already \(D_{19}>M\): all 18 later values of a(19) need proof beyond this
MR bound, while its start at the saved target scale remains below it.
The recorded 51 required values at n=16–18 are below \(M\).
This is a statement about those values, not all possible starts below
`P_CEIL=10^26`. `CERT_VALUE_CAP=10^34` is a separate proof acceptance cap.

The current source handles an unresolved required-value proof correctly:
`full_verify` [lines 424–440](../launch.py#L424) sets `agree=False` if a
proof is missing, invalid or over the cap; `_finalize`
[lines 744–752](../launch.py#L744) raises before settling and before
committing the boundary. Preserve that behavior. A failed strong test
before n proves the candidate unsuitable; a passing probable-prime chain
does not itself authorize a discovery. Exact overshoot depth and NEAR
metadata above \(M\) are only as strong as the tests on those extra values:
the proof loop certifies the n required values, not every overshoot.

## What one day means with the recorded evidence

[BENCHMARKS.md:52–118](../BENCHMARKS.md#L52) records:

- **2.07×10^11 \(p_1\)/s** end to end on a bounded n=16 production
  workload at q2=8192, three workers and the present overlap scheme.
- **1.93×10^11 \(p_1\)/s** across the complete n=16–18 campaign, 23.4 hours
  for approximately \(1.626\times10^{16}\) of separately swept line.
- An n=16, q2=65536 frozen device-sieve workload with 192 survivors and
  checksum 4046714554. This is not a measured n=19 campaign rate.

`score.py` [lines 42–50](../score.py#L42) pins that older workload.
[OPTIMIZATION_LOG.md:236–281](../OPTIMIZATION_LOG.md#L236) explicitly warns
that n=19 classification uses larger integers and the n=16 host cost does
not transfer automatically. The checkpoint's 4.95-hour counter was a
documented clock-accounting bug; the discovery timestamps supplied the
23.4-hour historical measurement.

The following is scalar division of the unchanged
[saved model](../model_results.json) by the **old** 2.07×10^11 rate.
It is not a rerun, a current measurement, or a guarantee of finding a term.

| Target from its own floor | Saved start location | Ideal days at old rate | Rate required to reach it in 24 h |
|---|---:|---:|---:|
| a(19), Q1 | 1.672812079×10^17 | 9.35 | 1.936×10^12 |
| a(19), median | 4.124737717×10^17 | 23.1 | 4.774×10^12 |
| a(19), Q3 | 8.397938113×10^17 | 47.0 | 9.720×10^12 |
| a(20), median | 1.008288197×10^19 | 564 | 1.167×10^14 |
| a(21), median | 2.530124580×10^20 | 14147 | 2.928×10^15 |
| a(22), median | 6.747199442×10^21 | 377259 | 7.809×10^16 |
| a(23), median | 1.874144331×10^23 | 10478978 | 2.169×10^18 |

At the old rate, one full current segment takes about **1.245 seconds**.
Ignoring startup, proofs and host changes, 24 hours reaches about
\(1.78848\times10^{16}\), or 69402 complete segments from aligned start
10020, ending at 17884759216629540. Thus this project has no multi-hour
segment-confirmation barrier: the missing throughput is the dominant
one-day issue. The proof pause at a future find is additional and unmeasured.
The n=19 quartiles remain from-floor predictions because no n=19 interval
has been saved. Reaching Q1 or the median means a model probability of
25% or 50%, not a promised outcome.

## PAP-001: stop sieving dead words and use the exact interval tail

**Disposition: Proposed. Evidence: exact equivalence and complete-period
work counts; runtime and finite-window occupancy unmeasured.**

The current engine already inverted its dense marking loop:
`build_tab` [ap_gpu.py:150](../ap_gpu.py#L150) constructs a q-word periodic
mask, and `mark_shared` [line 203](../ap_gpu.py#L203) gathers every table
into every word's accumulator before performing the shared-atomic tail.
Compaction occurs only after all marking
([_launch, lines 580–640](../ap_gpu.py#L580)). The inner all-word gather is
at lines 237–250, shared marking at 266–305, global marking at 315–369,
and final compaction at 371–391.
At production depth the historical phase split is roughly 55% table
gathers and 45% shared atomics within marking
([optimization termination table](../OPTIMIZATION_LOG.md#L283)).
The table approach itself is shipped; a sibling periodic-window speedup
cannot be claimed again here.

The missed opportunity is conditional work: once all 32 bits of a word are
rejected, later primes cannot restore any candidate. Use a short dense
prefix, retain only non-full words together with their original word
indices, and apply later tests only to that retained work. Alternatives are
to compact clear-bit candidates at the prefix, or compact words first and
extract candidates after several further tables. These are representations
of the same exact survivor set, not additional conjectural exclusions.

### Exact interval test

For a tail prime \(q>p_n\), let \(d_q=D_n^{-1}\pmod q\). Then
\[
 q\mid p_1+jD_n\ \text{for some }0\leq j<n
 \iff (p_1d_q\bmod q)\in\{0,q-n+1,\ldots,q-1\}.
\]
Multiplication by the inverse converts n scattered roots into one cyclic
interval. One normalized residue plus two comparisons replaces n
root comparisons or individual progression marks on a surviving candidate.
For \(q\leq p_n\), the separate exact condition is simply \(p_1\bmod q=0\);
choosing the dense cutoff above \(p_n\) makes the remaining tail uniform.

The proof is multiplication of \(p_1+jD_n\equiv0\pmod q\) by \(d_q\).
The endpoints include j=0 and j=n−1 exactly. No candidate can be discarded
because of a normalized interval not corresponding to an actual sieve
prime. At fixed q2, this must reproduce the old complete survivor stream.

### A work bound without assuming independent bits in a word

At n=19, conditioned on one of the eight mod-30 lanes, for \(Q\geq67\) define
\[
 \rho(Q)=\prod_{7\leq q\leq67}(1-1/q)
         \prod_{67<q\leq Q}(1-19/q),
\]
where both products are over primes. For any one fixed bit of a bitmap
word, changing the original word index by one changes the start by 120.
Since 120 is invertible modulo every q≥7, CRT gives that bit's exact
survival fraction \(\rho(Q)\) over a complete combined period.

Static finite-product arithmetic gives
\[
 \rho(199)\simeq0.00489184575435,\quad
 \rho(251)\simeq0.00246303708104,\quad
 \rho(257)\simeq0.00228094484548.
\]
A word is live if at least one of its 32 bits survives. The union bound,
which needs **no independence between those bits**, gives a complete-period
live-word fraction at Q=257 of at most \(32\rho=0.0729903\).

There are 52 table primes from 7 through 257 and 306 from 7 through 2048.
Keeping the first 52 dense and gathering the rest only for retained words
therefore uses at most
\[
 52+(306-52)\,32\rho(257)\simeq70.54
\]
table gathers per original word on a complete-period average, compared
with 306 now: approximately **4.34× fewer table gathers**. This excludes
compaction, index traffic, arithmetic, synchronization, table construction
and the later tail. It is not a 4.34× runtime claim, and a single launch need
not attain the period average.

For direct tail tests ordered \(q_1,\ldots,q_t\), the exact complete-period
expected number of scalar tests per prefix survivor is
\[
 \sum_{i=1}^t\prod_{j<i}(1-n/q_j).
\]
Multiplying by \(32\rho(Q)\) gives tests per original word. Equal-cost
tests favor increasing q because the rejection probability n/q decreases;
different arithmetic costs require rejection probability per cost. This
ordering argument is not a claim about parallel device performance.
These formulas let a later implementation price word retention versus
candidate retention without inventing independent-word probabilities.
They do not give an output-buffer capacity bound.

### Implementation and validation handoff

Preserve the original word index: table phases depend on that index, never
on a candidate's position in a compacted queue. Retain live-bit masks, mask
the final partial word, and reconstruct offsets relative to the original
host base. Preserve the exclusive interval and return sorted offsets for
least-first classification. Keep queue overflow fail-closed; size or chunk
intermediate queues for a worst case, not \(\rho\)'s average. A current
launch has \(2^{30}\) candidate bits and \(2^{25}\) words. A worst-case
live-word queue of u32 index plus u32 mask uses 256 MiB. The existing
`SURV_CAP=2^22` protects final output, not this intermediate queue. Split,
retry or halt before committing coverage if a stage exhausts its capacity.

For the interval arithmetic, reduce the arbitrary-precision base by the
existing split-base mechanism, then combine its residue with the u64
offset and multiply by \(D_n^{-1}\bmod q\). Widen before multiplication.
Since every tested q is below q2≤\(2^{31}\), the product of two reduced
residues is below \(2^{62}\), within the existing `bmod` contract
([ap_gpu.py:137](../ap_gpu.py#L137)). The supported q bound and reduction
contract must remain explicit; do not
silently truncate a large p1 or use an inverse when q divides D.

Keep the reference oracle on the original AP definition and keep the CPU
and GPU constructions independent. Future Claude work should compare
complete survivor streams on identical absolute intervals, including n=19,
q2=8192, historical frozen n=16/q2=65536, phase boundaries, non-full words,
the engine floor, large bases, and alternative cutoffs. Force queue
overflow and interruption between stages. For this exact reordering the
old frozen 192/checksum fingerprint must remain unchanged; add a current
filter fingerprint rather than replacing the old one with a self-consistent
new result. These are future checks, not checks run during this review.

The resulting stream at fixed n/q2 is unchanged, so current census
semantics and certificate logic can stay unchanged. If the persistent
representation changes, version it and adopt the saved numerical
**classified boundary**, replaying any required containing interval and
suppressing duplicate census below that boundary. Do not persist an
intermediate compacted position as contiguous coverage. A changed sieve
depth would change the raw survivor census and needs separate provenance.
The current checkpoint key encodes q2 and p-ceiling, not algorithm or canary
revision ([launch.py:237](../launch.py#L237)); `canaries_done=true` from
the old engine cannot attest the new implementation. Version verification
metadata or explicitly invalidate that attestation on adoption, separately
from PAP-002's per-term low-range record. At unchanged n/q2 and proven
stream parity, retain completed numerical coverage and committed census;
replay only in-flight work unless a new representation requires overlap.

There is no measured reason to expect this alone to meet the 23.1× median
threshold. The recorded host arithmetic may become limiting as device
work falls; n=19's actual host demand is unavailable. This is the main
research proposal, not an authorization to start or alter a hunt.

## PAP-002: close the per-term low-pass and alignment gaps

**Disposition: Proposed. Evidence: direct source control flow; no missed
term exhibited. This is a correctness prerequisite, not a speedup.**

Three pieces of current behavior do not meet the documented contiguous
coverage contract:

1. `low_pass` [launch.py:472–480](../launch.py#L472) calls the inclusive
   oracle with `hi=floor−1`, covering \([2,F)\).
   `_floor_u` [line 271](../launch.py#L271) returns \(\lceil F/30\rceil\).
   The engine starts at \(B_0=30\lceil F/30\rceil\). At q2=8192,
   \(F=10000\), \(B_0=10020\), leaving **[10000,10020)** between the paths.
2. Startup runs the low pass only inside the global `canaries_done` guard
   ([lines 546–550](../launch.py#L546)). `stage_reset` preserves that flag,
   and the in-loop stage transition [lines 599–616](../launch.py#L599)
   performs no low pass. The saved n=18 checkpoint has the flag true;
   its n=19 resume therefore skips the new difference's low pass.
3. The low-pass return is ignored at startup. If the oracle finds a
   qualifying small start, the caller continues into the larger range
   instead of proving and settling that least candidate.

The source's evidence field `swept_from=eng.floor` does not itself prove
the omitted alignment interval was swept. The evidence files contain
membership proofs and repository leastness claims, but this static review
has not independently re-established their tiny prefixes. An external
historical low-pass check may exist; none was established by these source
paths. Do not convert this gap into a claim that a recorded term is wrong.

A future correction should separate the one-time engine canary from a
durable per-term coverage prelude keyed by n, D, sieve depth and actual
aligned first engine start. Independently cover **[2,B0)** on every new
stage, or persist verifiable evidence that the exact same prefix was
covered for that filter. Handle any low hit through a proof path that does
not reject it merely because it equals a sieve or wheel prime. Settle the
least low hit before any higher candidate can be announced.

On legacy resume, missing prelude metadata is unknown coverage, not proof
of completed coverage. Backfill the prefix independently and record the
result before new leastness claims. Preserve the existing large completed
intervals and evidence as separate facts. Test alignment residues, an
injected low hit, stage advancement with `canaries_done=true`, failed
verification, and interruption before/after prelude commit.
Existing `_drill_low_pass` [line 1105](../launch.py#L1105) and
`_drill_stage_advance` [line 1117](../launch.py#L1117) do not establish
these combined obligations.

## PAP-003: clarify the prescribed difference and bound the model tail

**Disposition: Proposed. Evidence: mathematical clarification and rigorous
tail bound. No candidate or runtime reduction follows.**

### The sequence fixes D; it is not the minimum possible AP difference

The introduction to [ap_reference.py:7–10](../ap_reference.py#L7) calls
the product of the first n primes the smallest possible common difference.
That explanation is false. For example, the four primes 5,11,17,23 have
difference 6, whereas \(D_4=210\).

For a generic n-term prime tuple, each prime \(q\leq n\) must divide the
difference to avoid covering every residue modulo q. Otherwise some value
is divisible by q; a finite exceptional AP may survive only when that
value equals q itself. Thus the smallest **admissible tuple** difference
is the product of primes **at most n**, not the first n primes.
A053647 nevertheless prescribes the latter; replacing it changes the
question and cannot be presented as an optimization.

For the prescribed tuple, admissibility is immediate: q|D kills one
residue, and q∤D has q>p_n>n and kills only n residues. There is no local
obstruction, but infinitude is conditional on the prime-tuples conjecture.
The known fixed-prime sieve already removes all these local obstructions.

### The finite product's omitted tail is small and one-sided

`singular_series` [ap_model.py:75](../ap_model.py#L75) uses
\[
 S_n(Q)=\prod_{q<Q}\frac{1-w_q/q}{(1-1/q)^n},
 \quad w_q=1\ (q\mid D_n),\quad w_q=n\ (q\nmid D_n).
\]
For the stored \(Q=100000>p_n\), all omitted factors have w=n.
Writing \(T_n=S_n(\infty)/S_n(Q)\), expansion of the logarithm gives
\[
 -\log\frac{1-n/q}{(1-1/q)^n}
 =\sum_{r\geq2}\frac{n^r-n}{r q^r}
 \leq\frac{n^2}{2q(q-n)}.
\]
Replacing the omitted primes by all integers and using the integral
bound yields
\[
 -\frac{n^2}{2(Q-n)}\leq\log T_n\leq0.
\]
At n=19 the lower exponent is approximately −0.00180534: the omitted
product decreases the truncated intensity by less than about **0.181%**.
There are no exceptional large collision primes because all differences
of shifts are \((j-i)D_n\), whose prime factors are at most p_n.

This controls only Euler-product truncation. It does not prove the
Bateman–Horn/Poisson waiting-time model, numerical integration accuracy,
or independence of first occurrences. `expected_count`
[ap_model.py:91](../ap_model.py#L91) correctly retains the unequal
\(\log(p_1+jD_n)\) denominators; flattening them to \(\log(p_1)^n\) would
be a severe error at this scale.

[RESULTS.md's model assessment](../RESULTS.md#L129) records E totals
4.30 for the three new terms versus expectation 3, and 9.94 for all twelve
validation/find terms versus 12. The sample does not justify a deterministic
speed correction. A sub-percent tail correction cannot explain away the
9–23-day first-quartile/median barriers at the recorded rate. The saved
future-index predictions remain historical predictions, not fresh
conditional forecasts.

## Prior work and alternatives not credited as new speedups

The full [optimization history](../OPTIMIZATION_LOG.md) was reviewed.
Shared-memory marking, host sorting, vectorized base residues, periodic
word tables, larger launches and classified-segment overlap are shipped
(rounds 4–8). The 34.7× gain over v1 already includes them.
The table cutoff was measured from both sides; moving all sparse primes
into dense tables had lost. PAP-001 instead changes which words receive
the later work.

The following remain bounded alternatives or non-solutions:

- Mod-210 instead of mod-30 removes about 14% of bitmap lanes but has
  larger setup. It was already priced and left unmeasured
  ([log:294](../OPTIMIZATION_LOG.md#L294)); it is not a new order-of-magnitude
  exclusion.
- Depth 4096 with eight workers, gmpy2 arithmetic and a device base-2
  prefilter were already discussed in
  [round 9](../OPTIMIZATION_LOG.md#L202). The recorded approximately 14%
  gain for much more host load does not meet the present day threshold.
  New host classification work should be justified by the new n=19
  bottleneck, not claimed from these old measurements.
- Reversal \(p_1\mapsto-p_1-(n-1)D_n\) permutes modular roots but leaves the
  positive search domain. It does not halve the least-term search.
- New n changes D. Old AP survivors are not all prime starts and cannot
  stand in for a complete sieve at the new difference. A long old run is
  not a rider unless the actual new-index forms are shown to occur in it.
- Every \(N_j-1\) shares \(\gcd(D_n,p_1-1)\), and every \(N_j+1\) shares
  \(\gcd(D_n,p_1+1)\). No universal lower bound makes these sufficient
  certificate factors, and the current prover already trial-divides.
  AP starts are coprime to D in the ordinary range, so the forced-divisor
  proof-ceiling theorem from prime-ladders does not apply.

The preferred future order is to repair PAP-002, then preserve exact
current-stream parity while investigating PAP-001 at n=19. Keep
PAP-003's definition and model distinctions in the documentation.
Any later acceptance needs end-to-end evidence including classification,
proofs and completed boundaries; the static work bound alone is not that
evidence.

## File provenance

SHA256 snapshots are of source/data read on 2026-10-20. Project README
navigation was edited separately by the coordinator and is intentionally
not hashed here. No checkpoint or evidence was edited.

| File | SHA256 |
|---|---|
| `ap_reference.py` | `ce1fe9c4733e28faf185926151b154c0a44268a04cf206a8067c90bfb3ad7f3f` |
| `ap_search.py` | `ed5ea60f4182f42d395374e045e84b040d82f0b1ef5e36da697e61b0d8804b8f` |
| `ap_gpu.py` | `dc99a04e5eaa80b906d224f6cdeeeaab4635616b1d3ff3a94601579c9e0b49aa` |
| `launch.py` | `3c2b6c69ea6fa083f9c6504c6009f14c787cfc5a01631636b7b22cc014d92dff` |
| `score.py` | `e947a9f5f596c1ee57900eb12b95091a36fc2201110214d8e92398c962d3da06` |
| `ap_model.py` | `680aa8b3d49f918a51238c1da59ab8e667378d48e6753ed98336a9d7ee21e5f8` |
| `model_results.json` | `0e212406493a6a06ffe73a88b4e6e197ff09eb29c408c6426966b86caa547b4c` |
| `campaign_checkpoint.json` | `f9c1e8e16c1c044f2992e3b7348d6a25c9f4aaa54876d473228f30eb033e3c3a` |
| `evidence/ap_discoveries.json` | `73dbcedb187bac5b747571b0105c6dcad4ce17dc14296dfd81546ccb082cd877` |
| `evidence/ap_a16_p116781362669989.json` | `6b228e467d7e2f2941633717d75fde3581ec66580595b2ee7c35b3e11ed619e0` |
| `evidence/ap_a17_p2097209048106247.json` | `f9f3db4ff88a0e4e66a9028717044678927bf3a74d822b72ec150dd4b5ff9bde` |
| `evidence/ap_a18_p14042451608819603.json` | `df8089411c13098b37b718933d52cc4a1b297abf6d79fec677225fbfb3d609a7` |
| `OPTIMIZATION_LOG.md` | `66ebb8d77cf3f5c69f62e54995e50299ead2ce87752ebcb9fc6c13fa5ce13b8d` |
| `BENCHMARKS.md` | `21e874e457c82aa2ad27936ecf82295ee01f199996c5a7d5f902886644ffae22` |
| `RESULTS.md` | `3e132b0987443b9b69400b1959b0177bd21573b4dd233fce25b1e7a51296b12a` |
| `../huntlib/certificate.py` | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
