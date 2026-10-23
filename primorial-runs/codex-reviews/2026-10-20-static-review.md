# Primorial runs: static mathematical review

**Author:** Codex (OpenAI). **Date:** 2026-10-20.
**Scope:** A257466, A257467 and A258035; the five public Python roles,
model, checkpoints, evidence, benchmark ledger and optimization history.
The review team examined this project only.

This follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex is always
static in this role: no GPU use, project imports or execution, models,
oracles, tests, benchmarks, searches or primality experiments. Only
documentation was edited. Computed numbers below are lightweight
arithmetic on recorded data or explicit finite formulas. Certificates and
historical measurements were read, not independently rerun.

**Conclusion.** No new pruning theorem or representation establishes a
large throughput improvement. The modern window sieve, folded rounds,
wide records and quad pattern tables already exist. The useful immediate
planning distinction is **encountering a candidate versus confirming it
within a day**: A257466's current segment takes about 55.7 hours at its
recorded rate. A smaller, already measured wheel can close intervals
within the deadline, even though it lost the original comparison of
expected time to a confirmed find.

The saved conditional median travel times remain about **4.7 days,
76 days and 6.2 days**. Changing segment geometry does not turn those
medians into one-day medians. The other material finding is correctness:
exact-run coverage needs proved exclusions of open indices when shifted
values exceed the deterministic Miller–Rabin bound. That crossing has
already occurred here. All recorded discoveries have complete
certificates, but that alone does not certify every earlier exclusion.

## Definitions, discoveries and snapshot

HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`, with documentation
edits in the worktree. File hashes appear below. Links give snapshot line
numbers together with symbols so the argument remains traceable if lines
move.

Write \(P_k=\prod_{i=1}^k p_i\), and set
\[
 c_k=\sum_{i=1}^kP_i\quad\hbox{(A257466)},\qquad
 c_k=P_k^2\quad\hbox{(A257467)},\qquad
 c_k=\sum_{i=1}^kP_i^2\quad\hbox{(A258035)}.
\]
In each entry, a(n) is the least prime p for which
\(p+c_1,\ldots,p+c_n\) are prime and \(p+c_{n+1}\) is composite.
There are **n+1 required prime values**, including p. The sequences are
indexed from zero and runs are **exact**, not at least n. An earlier
term is not a floor for a later index, and one integer settles only its
own exact index. Definitions are in
[`shift_k`, `constants`, `is_term`](../runs_reference.py#L262).

The reference's [published tables and errata](../runs_reference.py#L173)
preserve the historical A258035 discrepancy. The repository's claim is
that its old listed a(11),a(12) belong at a(12),a(13), and that the true
a(11) is 23,569,356,649. The sweep found the smaller run-12 value before
the run-11 value. This is a recorded correction, not a new result of
this review. The user's submissions may be newer than the project's
October 8 export; no claim is made about present OEIS status.

| Family | Recorded discoveries | Latest recorded term | Actual open index |
|---|---|---:|---:|
| A257466 | a(16)–a(20), five terms | 9,588,149,987,699,367,569 | 21 |
| A257467 | a(15)–a(19), five terms | 418,446,268,390,828,120,903 | 20 |
| A258035 | a(11)–a(18), eight terms | 438,392,474,524,896,220,603 | 19 |

The ledgers are
[A257466](../evidence/a257466_discoveries.json),
[A257467](../evidence/a257467_discoveries.json) and
[A258035](../evidence/a258035_discoveries.json). Representative final
evidence is [a(20)](../evidence/A257466_a20_9588149987699367569.json),
[a(19)](../evidence/A257467_a19_418446268390828120903.json) and
[a(18)](../evidence/A258035_a18_438392474524896220603.json);
the corrected [A258035 a(11)](../evidence/A258035_a11_23569356649.json)
has separate evidence.

[RESULTS](../RESULTS.md#L21) records an independent October 8 verification
of 18 files and 309 certificates: 248 deterministic MR, 58 BLS75
Theorem 1 and three Theorem 15. Static inspection finds every file marked
`certificates_verified=true`, with empty `unproved`, and a factor of its
composite stopper. These support the displayed terms' membership.
The least-term claim additionally depends on exhaustive classification;
PMR-002 explains the distinction without asserting a missed term.

`FOUND` remains [empty](../runs_reference.py#L201), and
[model_results.json](../model_results.json) still records original
frontiers 15,14,10. This is deliberate historical forecast data, not
the current campaign state. RESULTS already lists normalization of
the discoveries and frozen current-filter workloads as work owed at a
future resume. Existing score shapes remain at indices 16,15,11.

### Committed boundaries versus partial work

These are saved snapshots, not a live-process observation:

| Family | Saved timestamp | Filter / sieve q2 | W, the physical period | j; u / launches |
|---|---|---|---:|---|
| A257466 | 2026-10-06 00:47:18 | n21 / 16,384 | 32,589,158,477,190,044,730 | 3; 113,323 / 7,862,580 |
| A257467 | 2026-10-07 07:47:08 | n20 / 32,768 | 614,889,782,588,491,410 | 750; 0 / 573,376 |
| A258035 | 2026-10-08 09:28:23 | n19 / 32,768 | 757,887,406,446,280,110 | 581; 8,745 / 387,600 |

Sources: the three checkpoint files
[A257466](../campaign_checkpoint_a257466.json),
[A257467](../campaign_checkpoint_a257467.json),
[A258035](../campaign_checkpoint_a258035.json).
All use unit 6. The prime class is 5 mod 6 for A257466 and 1 mod 6
for the squared families. Current widths are respectively 160 wide,
160 narrow and **145 live periods** on the last family's selected
window/record.

| Family | Saved complete-boundary claim B = k = k_start = cover_x | Pending count / largest run |
|---|---:|---:|
| A257466 | 103,916,373,257,455,048,290 | 11,317 / 16 |
| A257467 | 461,167,336,941,368,557,500 | 0 / none |
| A258035 | 440,747,276,254,476,331,140 | 1,637 / 14 |

No pending record reaches its current filter; there is no cached full
candidate awaiting a quick confirmation. B denotes the repository's
claimed classified interval below that boundary, subject to PMR-002's
proof obligation. It is not `jW+u/L` of a segment. The boundary can
exceed jW after an earlier wheel's completed interval has been carried.
[`x_start` and `k_min`](../launch.py#L582) retain that numerical floor
and clip the containing new-wheel segment correctly.

Classifying a full segment before promotion is the right mathematical
structure for exact runs: every candidate whose true run reaches the
filter can settle its own index, including a higher index found early.
The launcher [handles all sorted pending records](../launch.py#L1199)
before [carrying the numerical boundary](../launch.py#L923).
This reuse already exists; it is not a new suffix-reuse proposal.
Its validity depends on exact, uncensored, proof-safe classification.

The exception zone is [p≤q2](../runs_search.py#L144), where divisibility
by q cannot reject a value equal to q. The host classifies that prefix,
including the exceptional primes 2 and 3, with per-filter `zone_n`.
This review found no reason to transplant the different low-pass gap
from primorial-ap into this launcher.

## What the recorded clocks mean

The current filters were priced on their actual constants and planned
engines in [BENCHMARKS](../BENCHMARKS.md#L64): 2.60e16, 6.40e15 and
1.04e16 p/s. These are historical engine-API measurements, not rates
measured during this review. The completed earlier campaign legs matched
their prices at 0.97–1.08×; the paused current filters did not each run
a full segment. A257467's preceding leg includes a long pause, so its
wall-clock rate is not its active throughput.

[RESULTS](../RESULTS.md#L305) supplies the October 8 forecasts conditioned
on the saved B, calculated then in a scratch process. They are more
relevant than the original `model_results.json` opening rows:

| Family | Conditional median location | Conditional P90 | Median travel from B at priced rate | Reported probability in 1 / 7 / 30 days |
|---|---:|---:|---:|---|
| A257466 n21 | 1.07e22 | 6.49e22 | 4.72 days | 21% / 59% / 91% |
| A257467 n20 | 4.27e22 | 1.94e23 | 76.39 days | 2% / 9% / 28% |
| A258035 n19 | 5.99e21 | 2.48e22 | 6.18 days | 13% / 54% / 92% |

These are BH/Poisson probabilities of the event occurring within a
numerical interval, not proof of its occurrence or a promise that the
containing segment closes by the deadline. In particular, the A257466
day probability must not be advertised as a day-confirmation probability
on the unchanged plan.

The 18 recorded discoveries had mean E=0.70, against 1 under the
model, so they arrived early in aggregate. The log explicitly withdraws
its generic instruction to budget a 1.5–2× delay. Neither that old
multiplier nor its inverse is a justified deterministic correction to
future terms. No new model was evaluated here.

At unchanged rates and before startup, proof work or promotions:

| Family | Full current segment | Time for a full segment | Useful 24-hour completed-boundary scenario |
|---|---:|---:|---|
| A257466 | 5.21427e21 | 55.71 hours | Fresh segment does not close; saved partial work is only 1.44% of launch count |
| A257467 | 9.83824e19 | 4.27 hours | Five complete segments, B becomes 9.53079e20 |
| A258035 | 1.09894e20 | 2.94 hours | Eight complete segments without partial credit, B becomes 1.31948e21 |

A258035 could close a ninth only with sufficient remaining-time credit;
its saved 2.26% launch fraction is not by itself a time measurement.
The first family's equal-cost-per-launch approximation gives 54.91
hours remaining, but that is explicitly an approximation, not a measured
remaining clock or an unconditional proof of zero chance within a day.
Reaching the rounded conditional medians in a day requires respective
continuous-line speed factors of about **4.72×, 76.39× and 6.18×**,
before confirmation and proof costs.

## PMR-001: plan for a confirmed result before the deadline

**Disposition: Proposed.** This is a change in objective and coverage
geometry, not a newly measured faster kernel. The current planner
[`plan`](../runs_gpu.py#L697) minimizes expected clock to a confirmed
find using whole segments and the original floor 2. Its historical
full-53 choice was reasonable under that objective. With a fixed
24-hour deadline, maximize the complete boundary attainable by then,
conditioned on the actual saved B and remaining work.

For a fixed filter, the model probability is monotone in the covered
endpoint. Thus among plans with equivalent proof/classification
obligations, the largest **completed** endpoint is the relevant target.
A faster line rate that leaves every new candidate in an unclosed
segment may be worse for this deadline.

### An already measured alternative

[Round 1's wheel comparison](../OPTIMIZATION_LOG.md#L166) at A257466 n21
measured the full wheel through 47, narrow, 160 periods at **1.96e16 p/s**,
versus 2.55e16 for full-53 wide. Its expected-confirmed clock was worse,
338 versus 289 hours, so the wide plan was retained. These are expected
clocks from the old floor, not current median clocks.

The narrow period is \(W_{47}=614889782588491410\). The saved boundary is
exactly \(B=169W_{47}\), so this adoption needs no numerical floor overlap.
A full 160-period interval takes approximately **1.394 hours** at that
recorded rate. Seventeen complete intervals fit into 24 hours before
startup/proofs, reaching
\[
 B'=1,776,416,581,898,151,683,490.
\]
This establishes a concrete deadline alternative to evaluate, not a
new speed measurement or a computed probability. It still ends below
the original unconditional Q1, about 2.50e21, and far below the saved
conditional median. Even an ideal implementation does not make a
day-term likely merely by creating a commit boundary.

### Shorter windows on the current full-53 wheel

For fresh h-period windows at the current W, a first closure in one day
requires rate at least hW/86400:

| h | Required rate | Fraction of recorded PB160 rate | First endpoint from j=3 |
|---:|---:|---:|---:|
| 32 | 1.20701e16 p/s | 46.42% | 1.14062e21 |
| 64 | 2.41401e16 p/s | 92.85% | 2.18347e21 |
| 96 | 3.62102e16 p/s | 139.27% | 3.22633e21 |

No measured current-filter PB32/PB64 rate is established here.
Inherited `CREL_WIDTH` constants are scenario inputs, not acceptance
measurements. The 64-period threshold leaves little room for any lost
throughput, whereas 32 periods has more headroom but a smaller endpoint.
Compare both with the already measured narrow plan using complete
confirmation time, not candidate rate alone.

`seg_cap` merely batches whole live windows in
[GpuEngine construction](../runs_gpu.py#L2944); setting it to 64 while
retaining a 160-period window does not produce a 64-period committed
interval. Either rebuild with the intended width or implement a truly
clipped endpoint. Keeping a PB160 pattern while clipping its live
range still pays its window work and cannot inherit a PB32 rate.

### Future implementation and migration

Price the chosen current filter and deadline using its actual B and
complete segment cost; preserve the distinction between model-dependent
probability and arithmetic completed coverage. Keep all original frozen
shapes and add a fixed absolute interval at n21. The mathematical oracle
must remain the original exact-run definition.

A changed wheel requires re-denominating B, not copying j. A changed PB,
live window, table decomposition or residue ordering invalidates the
partial u cursor even when W stays unchanged. Preserve committed claims;
replay uncommitted work and any necessary floored overlap, suppressing
duplicate census below B. Pending records and partial survivor counters
must be discarded/rebuilt or reconciled together. The existing
[width-mismatch reset](../launch.py#L518) resets u while
[load](../launch.py#L722) retains pending records, so it is not a complete
adoption recipe.

A same-enumeration clipped interval may reuse earlier completed launch
stripes, but only if its active numerical endpoint is durably stored,
pending records above that endpoint are held apart, and resume cannot
silently switch back to a larger window while skipping unseen suffixes.
The existing [`_sweep`](../runs_gpu.py#L4081) has the necessary partial
`nper` primitive and preserves launch enumeration for a shortened j1;
the campaign's `segment_end` and checkpoint need to persist that choice.
This can retain the saved launch prefix, but its PB160 pattern cost
remains and no smaller-window throughput follows from that fact.
All accepted boundaries must satisfy PMR-002 before being described as
proved exact-index coverage.

## PMR-002: prove exact-index exclusions before committing coverage

**Disposition: Proposed.** This affects the strength of the least-term
claim, not just future speed. The deterministic MR bound is approximately
3.317e24. The shifts exceed it from n19 for A257466 and n12 for the
squared families, so this issue is already relevant at the current
filters and during some historical classifications.

### PRP overstatement can hide an exact index

The source's statement that a PRP chain can lengthen a run but never
hide one is insufficient for exact-run sequences. Suppose a candidate's
true run is an open index n, but its composite stopper passes the MR
bases and the apparent run is r>n. If both r and r+1 are already settled,
[`event_kind`](../launch.py#L207) labels it CENSUS and
[`handle`](../launch.py#L805) returns without independent verification
or certificates. The candidate for open a(n) has been discarded.

This is a logical source counterexample, not a constructed pseudoprime
or an identified historical missing term. The existing files certify
their displayed prime values and composite stoppers. They do not store
enough proof material to turn every historical probable exclusion into
an independently checked exact-run exclusion. Keep that limitation
separate from the repository's recorded minimality claims.

A sufficient remedy proves the exact classification of every candidate
that might reach an open index. A cheaper valid remedy proves only what
is needed to exclude each relevant exact index: if the apparent run is
r and n<r is open, a certificate that \(p+c_{n+1}\) is prime excludes
exact run n, regardless of whether every other apparent pass is proved.
A failed MR test at j proves compositeness and excludes all runs ≥j.
Unresolved potential stoppers must hold a durable coverage boundary.
For an actual new exact term, prove p, its entire required prime prefix,
and the composite stopper.

### Failed certificates must stop settlement

[`record_discovery`](../launch.py#L842) obtains `certs, unproved`, but
still mutates `found` at line 893 and announces the result. Lines
915–920 explicitly let an unproved find stand. Future proof-grade
settlement must stop before changing found, writing a proved discovery,
promoting the filter, or advancing the boundary when any required
certificate is unresolved. The current 18 files have no such unresolved
required value; this is a source-contract gap, not a claim that those
certificates failed.

The measured certificate study at
[OPTIMIZATION_LOG:67](../OPTIMIZATION_LOG.md#L67) tested only 12 random
primes per height. First-pass successes were 11/12 at 1e45 and 12/12 at
1e50,1e55,1e60; the largest individual time at these heights was 2.75 s.
That supports a bounded attempt, not guaranteed proof success. Retry
success at 1e60 and large stopper factoring were explicitly unmeasured.
Certificate work added by proof-safe exclusions is an additional cost
not present in the historical throughput assumptions.

### Capped classification must retain its cap

The pool captures a cap of filter+8, but
[`handle`](../launch.py#L795) compares a returned run against the
**current** `run_cap()`, which follows the mutable frontier. During the
sorted pending loop, an earlier discovery can fill a low hole and move
the frontier past indices already found. A later record that reached
the old cap can then fall below the new cap and evade rereading. If
its apparent index and successor are settled it can become CENSUS.

Persist a censor flag or the cap under which each record was classified.
Reclassify every old cap hit based on that metadata, independently of
intervening discoveries. `RUN_EXACT_CAP=64` is also finite: a hit at 64
does not prove an exact run and must not become a term or a completed
coverage assertion without resolving its stopper.

The configured value ceiling is 1e60, with last shift-supported indices
36,21,21; the term ceiling is separately 1e40. These are not all executable
engine limits: [`NRES_MAX=32`](../runs_gpu.py#L828) and the constructor's
[n+1 form-capacity check](../runs_gpu.py#L2511) limit an A257466 filter to
n31 without a representation change. Host classification can reach a
longer run, but following the frontier to n32 would fail. The current
filters are unaffected. The value limit is on each
actual value p+c_k and on proof capability, not a license to classify
arbitrarily far above the filter. An apparent longer run outside the
supported proof range should be held or excluded from targeted indices
by sufficient proved stoppers; it must not silently certify coverage.
`n_max` checks the shift alone, while discovery has no explicit actual-value
ceiling guard; that guard belongs before proof-grade acceptance.

Future validation should inject: an MR overstatement landing in an r
with **both r and r+1 settled**; a required certificate failure; a
same-segment frontier jump past an earlier classification cap; a cap-64
hit; and a crash with an unresolved coverage fence. Check that no
claimed empty interval or settled index crosses unresolved work.
These are later implementation tests, not tests executed by this review.

## PMR-003: bound the model tail and complete exact-run admissibility

**Disposition: Proposed.** This is mathematical assurance, not a search
speedup. [`log_singular`](../runs_model.py#L62) truncates the Euler
product below Q=200000. Shift differences here can have prime factors
above Q, so one cannot assume every omitted prime has n+1 distinct roots.

For a list \(0=c_0<c_1<\cdots<c_n\), let m=n+1 and
\(\Delta=\prod_{i<j}(c_j-c_i)\). For q>Q>m, put
\[
 A_q=\frac{1-w_q/q}{(1-1/q)^m},\qquad
 G_q=\frac{1-m/q}{(1-1/q)^m}.
\]
If a residue class contains h coincident constants, its deficiency h−1
is at most its pair count, hence \(m-w_q\leq v_q(\Delta)\).
Consequently
\[
 0\leq\log(A_q/G_q)
 \leq\frac{v_q(\Delta)}{q-m}.
\]
Summing the generic negative tail and this positive collision correction
gives the rigorous bound
\[
 -\frac{m^2}{2(Q-m)}
 \leq\log T_n
 \leq\frac{\log\Delta}{(Q-m)\log Q},
 \qquad T_n=\prod_{q>Q}A_q.
\]
No factorization is needed for
\(\log\Delta\leq\sum_{j=1}^n j\log c_j\).
Arithmetic from the stated first 22 primes gives conservative bounds
(rounded outward):

| Family / index | m | Lower / upper bound on omitted log product |
|---|---:|---|
| A257466 n21 | 22 | −0.001211 / +0.003764 |
| A257466 n22 | 23 | −0.001323 / +0.004397 |
| A257467 n20 | 21 | −0.001103 / +0.006387 |
| A257467 n21 | 22 | −0.001211 / +0.007520 |
| A258035 n19 | 20 | −0.001001 / +0.005378 |
| A258035 n20 | 21 | −0.001103 / +0.006387 |

The exact-run intensity is a **difference**, already implemented in
[`_density_curve`](../runs_model.py#L89). If a,b are the truncated
at-least-n and at-least-(n+1) curves, and
\(L_n\leq T_n\leq U_n\), then the corrected difference satisfies
\[
 L_na-U_{n+1}b
 \leq d_{\rm exact}
 \leq U_na-L_{n+1}b.
\]
Do not apply the small relative bound on a directly to a−b:
near cancellation can amplify relative error, and the model's zero
clamp is not a proof of exact intensity. A future model update should
propagate both products' intervals, preserve original forecast files,
and report conditional current-boundary predictions separately.
These bounds address product truncation, not the BH conjecture,
integration error or first-occurrence scatter.

### Exact-run admissibility

The already implemented bound
\(w(q,n)\leq1+\min(n,\pi(q)-1)\) proves ordinary tuple admissibility.
It also proves that no q≥5 forces a single residue; only the existing
2,3 classes are forced outside their prime-equality exceptions.
The [squarefree unit guard](../runs_search.py#L237) is already correct.

Ordinary tuple admissibility alone does not state that the *next*
shift is composite. To complete the exact-run argument, choose a prime
\(\ell>c_{n+1}\), set \(p=\ell t-c_{n+1}\), and require the n+1 forms
\(\ell t-c_{n+1}+c_i\), i=0..n, to be prime. Modulo ell they are all
nonzero; modulo any other q, invertible scaling and translation preserve
the original admissibility. The forms are primitive and eventually
positive. Dickson's conjecture predicts infinitely many such t, and
for t≥2 the stopper \(p+c_{n+1}=\ell t\) is composite.
This is a conditional infinitude proof, not permission to restrict a
least-term search to that chosen class.

## Existing work and rejected mathematical directions

The source already has periodic window masks, subset three-level CRT,
narrow and wide records, lazy folded rounds, sparse tails and overflow
fallbacks. [Round 2](../OPTIMIZATION_LOG.md#L302) shipped quad tables and
minimal reads for a measured 1.010–1.015× at the long-running filters.
Repeating a generic window-sieve or folded-round donor would duplicate
existing work. Its instruction profiling is historical context, not a
proposal to profile hardware during this review.

The larger wheel at A257467 n20 was already
[priced and declined](../OPTIMIZATION_LOG.md#L202); the next prime 59
at A257466 was [declined for segment size](../OPTIMIZATION_LOG.md#L379).
Those candidate factors are too small to meet 76× or 4.7× median-travel
requirements, and their intervals worsen confirmation latency.
For the actual A257467 n20 filter, q53 keeps **42**, so adding it gives
53/42=1.26190 fewer generated candidates, not the old log's optimistic
1.43 bound. The canonical full-53 partition needs 29,113,344 first-level
rows, 73.53% above 2^24. Its minimum 32-period segment would take about
45.26 hours at the old rate, or 35.87 hours even under ideal count-to-rate
scaling. This sharpens the existing negative disposition.
Pre-shifted tables, CRT pairing, one-bit extraction and the quad-occupancy
tradeoff were also priced or measured. No new substantial improvement
to those alternatives was established.

Pooling the two squared families offers little duplicated work to remove.
For the current n20/n19 shapes on the same full-through-53 wheel, direct
finite residue counts give densities
\(d_A=0.0006112318216\), \(d_B=0.0003475940540\), and intersection
\(d_I=0.000005029886616\). The ideal aggregate count ratio
\((d_A+d_B)/(d_A+d_B-d_I)\) is only **1.005274**. This is a complete-CRT
count comparison, not their actual different-wheel runtime. A coherent
family mask would be needed across all primes; taking per-prime unions
alone is not the global union. That small upper opportunity does not
justify a joint-engine proposal here.

Reflection of offset sets modulo primes does not map positive least
prime starts to positive least starts. Exact n cannot be isolated by
requiring the next shifted value \(p+c_{n+1}\) to be prime; that discards
the desired composite stopper. Conversely,
keeping only candidates whose stopper has a small factor would discard
valid exact terms with rough composite stoppers, unless a second
exhaustive stream remains. The current classified-segment carry already
shares work across open exact indices; PMR-002 concerns making that
classification sufficiently proved and uncensored.

Before later implementation, normalize the recorded frontiers with
provenance and retain all historical fingerprints. Add the owed frozen
current-filter intervals and make engine/version labels unambiguous:
the checkpoint says v1 while the historical kernel ledger says v2 for
a stream-identical change. Version proof/canary rules separately from
raw survivor equivalence. A parity-preserving speed change cannot by
itself resolve an earlier proof gap.

The independent oracle should remain the simple original definition.
CPU/GPU parity must compare identical absolute ranges and complete
streams, including the prime-equality prefix, exact stoppers, pending
records, and census boundaries. No report checklist authorizes runtime
work or a campaign start. The supported opportunity is a deadline-aware
choice among concrete plans; a major new throughput speedup remains
unestablished.

## Snapshot hashes

SHA256 values pin files read on 2026-10-20. Project README navigation was
edited separately and is excluded from this source/data snapshot.

| File | SHA256 |
|---|---|
| `runs_reference.py` | `e2d1bb73b5e4bad8c7bfbc1975d29e2fda13764c782a3ed4d5b0cc5b83fc49fc` |
| `runs_search.py` | `3bdd1099cda69890557e5b6ad15798c9ecfba478a8988a8672fd1ec00c7fc394` |
| `runs_gpu.py` | `d21c8044d535b5fdcacdd6fcbaede047f0cef6fd2dbdb63282980090e4153abe` |
| `launch.py` | `0f554d6f56616f3c07649e047fd182eb23d8e7a7b2874b5a64f284583e89e6ca` |
| `score.py` | `06fdba104b60bf99c1ac70a77ff2724374ab9898cf86285a9ebfdd5068223009` |
| `runs_model.py` | `dd7a7d2f1f93b5d29bd815aaa02820a75680ab56c643c14b14295378cf721aa7` |
| `model_results.json` | `e2ad89a7901b7e9a701a16602ba5a51431e6d2a7e01c09386cb7c0faa6f43f4b` |
| `campaign_checkpoint_a257466.json` | `4838bdfa23ae4c187705eb208edafa68ebe1b7882d97e39b2e01888a69405a14` |
| `campaign_checkpoint_a257467.json` | `0a21d932c531ae2dbbefb41d79f92c5b3cf6570c8449361ddc657df472807010` |
| `campaign_checkpoint_a258035.json` | `68045c556e519b260d087ab435c7faae9544c1ada123df8cc4c9c024c2bc3d37` |
| `evidence/a257466_discoveries.json` | `ac1277bfe2e925621d18e9d74edd2cfd98539f4f4fc1d8c1b97a3a9af7ee5e4a` |
| `evidence/a257467_discoveries.json` | `320d1ccd9b15cdb2af5e1b622466b2395f9585e4e3d02470ca949e826cd5c9a7` |
| `evidence/a258035_discoveries.json` | `52c932569eea7851dfbb772f65061a04016f9ca8d5f84d5cd7e8ae127cefe57e` |
| `evidence/A257466_a20_9588149987699367569.json` | `a05678939d4e48003120f22245b3903b3ee622cb063619afc98e3c5d232c8400` |
| `evidence/A257467_a19_418446268390828120903.json` | `d2459c4ad25e1b195f1c71d3db5e7c2591d15b1d670ae56a6093e3bc35f82d86` |
| `evidence/A258035_a18_438392474524896220603.json` | `f2cfebee404a71314de57ebd85f7a44659752bdbdb2d96dbcc538ed973cc2e11` |
| `evidence/A258035_a11_23569356649.json` | `37f92bff392905e334d181df4ba0dafb5aedc5f417e7c1a86aa29bf2bf6f8ff6` |
| `OPTIMIZATION_LOG.md` | `203f9a6ecfd3baedec649d8b6edcbb1d9103d63b7f6c0393ad0a742f7da92542` |
| `BENCHMARKS.md` | `de47bfbe728227e1cfee2e4d8f10b6d5b61f5a5120b7b4b5b38c03308aa990d8` |
| `RESULTS.md` | `b62b94ddc07dd7e5d7af74c3477fd52452ea4f60a5aa1a6aeea0ff20e2eb1907` |
| `../huntlib/certificate.py` | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
