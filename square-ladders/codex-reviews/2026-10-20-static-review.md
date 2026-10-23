# Square-ladders static review, 2026-10-20

> Authorship: this review was written by Codex. The reviewed project code
> and its historical optimization records retain their existing Claude
> attribution. This document proposes work; it does not report a new
> implementation, test result, measured speedup, or mathematical term.

| Field | Value |
|---|---|
| Review date | 2026-10-20 |
| Reviewer | Codex |
| Method | Static source, documentation, checkpoint, and mathematical analysis only |
| Repository HEAD | `f8fdb200c56a54aa5e207c146882f7d2d7b87224` |
| Working-tree qualification | Root guidance and README files had pre-existing changes; `power-ladders/` was untracked. Source-file hashes below identify what was actually read. |
| Target | A089761 a(19), current filter n = 19 |
| Changes made in this review | This report and its review index only |
| Execution boundary | No GPU access, project imports, oracle/test execution, benchmarks, profiling, or campaign runs |
| Workflow | [Repository Codex review workflow](../../CODEX_REVIEWS.md) |

Codex reviews of this project are always static. All references below to
implementation, execution, measurement, or gates describe work for Claude
in a later authorized development session. They do not authorize Codex to
run that work or authorize anyone other than the owner to start a hunt.

## Decision and evidence strength

**The main opportunity is to amortize the same mathematical sieve across
consecutive wheel periods.** Square-ladders still tests a CRT prefix on
each generated candidate. Later sibling engines represent a whole
progression of candidates as a bit window and eliminate many candidates
with one pattern lookup. The square-specific residue condition admits
that transformation exactly.

This is a stronger lead than another pass over the old kernel's tuning
constants. It is also distinct from the larger-wheel, binary-search
proposal already considered in the square optimization log. Its benefit
on square-ladders has not been measured.

The existing model gives approximately 33 hours of continuous work from
the saved coverage boundary to the conditional a(19) median. A continuous
rate improvement of about 1.39x would cross the one-day threshold, but a
new period-window engine also needs to finish its whole coverage segment.
With 32, 64, and 128-period segments anchored at the saved boundary, the
required factors become approximately **1.52x, 1.69x, and 2.03x**,
respectively, to cover the rounded model median within 24 hours.

These are required factors, not predicted gains. The project's model has
a documented history of optimism, including the reported 3.7x aggregate
factor and the exceptionally late a(18). There is no basis for promising
an additional term in a day.

| Evidence category | What this review establishes |
|---|---|
| Source fact | The current hot prefix is per candidate; the independent CPU sieve and oracle use different constructions. |
| Mathematical deduction | The square killed sets can be transformed into periodic bit patterns over the wheel-period index without changing the survivor set. |
| Historical measurement elsewhere | Linear-ladders reports a large gain from this algorithmic change. |
| Unmeasured proposal here | A square-specific window engine with separately represented periods. |
| Planning arithmetic | Approximate memory, offset bounds, and complete-segment work at the current frontier. |
| Not established | A square-ladders speedup, a new term, a probability calibrated to the new search, or a successful implementation. |

## Current state, rather than the old benchmark headline

The reviewed [checkpoint](../campaign_checkpoint.json) records:

| Item | Value |
|---|---|
| Engine / key | `v5` / `a089761-v5-p123-p237-p347-q265536-seg16` |
| Coverage period | `j = 179` |
| Partial-period work cursor | `u = 546` |
| Wheel period W | `614889782588491410` |
| Covered below k | `110065271083339962390 = 179 W` |
| Current frontier | a(18) = `109927810420106024208` |
| Next open term / actual filter | a(19) / n = 19 |
| Pending, not yet counted records | Nine records from the incomplete period |
| Last saved timestamp | `2026-08-23 10:45:27`, copied verbatim from the checkpoint |

The checkpoint timestamp is not a current observation of a running
process. The checkpoint's exact coverage integer is authoritative for
this review. The prose in [RESULTS.md](../RESULTS.md), lines 165-167,
contains a slightly different exact integer; this report does not
silently substitute it for the checkpoint.

The current filter is reconstructed by `Campaign.frontier()` and
`filter_n()` in [launch.py](../launch.py), lines 269-278, and passed to
`GpuEngine` at line 250. It is n = 19, even though the three-level
benchmark shape is still n = 18 and the original headline `SCORE` is
n = 16: [score.py](../score.py), `SHAPES`, lines 90-101.

The documented campaign rate is `1.35e15 k/s`; the conditional depths
from [RESULTS.md](../RESULTS.md), lines 169-185, are:

| Quantile | Rounded depth | Published time from the frontier |
|---|---:|---:|
| Q1 | 1.71e20 | 12 h |
| Median | 2.72e20 | 33 h |
| Q3 | 4.82e20 | 77 h |
| P90 | 8.23e20 | 147 h |

These rates and depths are historical repository evidence, not fresh
measurements. The underlying rate was observed during the previous
campaign; it is not a new n = 19 calibration. The saved checkpoint's
`passed` list is also not a conditional probability estimate from today's
coverage boundary: the model ladder has its own frontier origin.

## SQR-001: amortize the sieve across wheel periods

**Priority: highest. Status: proposed, with a mathematical applicability
proof; speedup unmeasured.**

### What the existing engine repeats

In [sqladder_gpu.py](../sqladder_gpu.py), `lit_prefix` begins at line 409;
the `CAND` macro around lines 648-660 applies that generated prefix to
one candidate; `sieve` begins at line 708. The generator reconstructs
each candidate from CRT wheel indices, tests its prefix, compacts, and
tests the survivors further.

The last recorded phase split in
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), "Measurement E12", lines
1099-1113, assigns v5 8.6% generation, 40.7% prefix, 10.2% first queue,
21.2% round 2, and 19.3% tail. This is an old production-shape measurement,
not an n = 19 profile from this review.

Deleting only a phase worth 40.7%, with everything else fixed, would
have an Amdahl ceiling of `1 / (1 - 0.407) = 1.69x`. Therefore the
proposal should be evaluated as a replacement of the repeated generation
and sieve organization, including its compaction boundary, not as a
promise that faster prefix lookups alone will provide an arbitrary
multiple. A small prefix-only implementation may fail the 128-period
time-to-coverage threshold even if the prefix itself becomes very fast.

### Square-specific equivalence

For a prime q, define

`K(q,n) = { -(i^2)^(-1) mod q : 1 <= i <= n and q does not divide i }`.

The independent CPU construction is `killed_residues` in
[sqladder_search.py](../sqladder_search.py), lines 84-93. The oracle
`forbidden_k_residues` in
[sqladder_reference.py](../sqladder_reference.py), lines 105-117, instead
walks residues and tests direct divisibility. Keep that independence.

For odd q the proved count is `min(n, (q-1)/2)`; for q = 2 it is one.
The reason for the saturation is that the squares of
`1..(q-1)/2` enumerate the nonzero quadratic residues. For q > 2n,
different indices cannot collide under squaring because neither their
sum nor difference reaches q. Negation and inversion preserve the count.
The existing oracle documents and gates these facts.

Let r be one canonical surviving wheel residue, `0 <= r < W`, and
consider a block of B candidates

`k_j = W (J + j) + r`, for `0 <= j < B`.

Every sieve prime outside the wheel is coprime to W. Define
`d_q = W^(-1) mod q`, the transformed killed set
`H_q = {d_q c mod q : c in K(q,n)}`, and the starting position
`b_q = (J + d_q r) mod q`. Then

`k_j mod q in K(q,n)` if and only if
`(b_q + j) mod q in H_q`.

Thus one periodic q-bit pattern, read at position `b_q`, answers the
divisibility test for every period in the block. OR the killed masks
over the chosen prefix primes, complement them, mask away unused bits
in the final partial window, and extract the live period indices.
This produces exactly the same prefix survivors as testing each
candidate separately.

The transformation changes neither the admissible wheel residues nor
the definition of a prime run. The later sieve and host verification
remain necessary. In particular, it does not assume that half the
residues die for every prime: at n = 19 the post-wheel primes q >= 53
kill exactly 19 residue classes, not `(q-1)/2`.

### Existing implementation donors, and what their evidence means

The algorithm is implemented in
[linear-ladders/lladder_gpu.py](../../linear-ladders/lladder_gpu.py), lines
6-38 and `window_patterns` at line 632. Its v4 account in
[linear-ladders/OPTIMIZATION_LOG.md](../../linear-ladders/OPTIMIZATION_LOG.md),
line 864 onward, reports **8.8x at the live filters** and larger ratios on
some frozen shapes.

Read the detailed measurement at lines 1015-1045 before quoting a ratio:
some frozen-shape comparisons used the old engine without its pipeline,
and the log explicitly gives smaller comparisons against its pipelined
benchmark rates. Neither the 8.8x headline nor any larger frozen-shape
ratio is a square-ladders forecast.

The more suitable representation donor for this wheel is
[lcm-ladders/lcml_gpu.py](../../lcm-ladders/lcml_gpu.py), `window_patterns`
at line 1192 and the wide-record `TEST` explanation at lines 1308-1320.
Factorial and decimal also contain this representation. Decimal has
additional engineering changes, but transferring every tuning decision
at once would obscure whether the mathematical amortization pays.

### Why this was not rejected already

Square's "Open after v5" section, line 1185 onward, considered a
**larger wheel with binary searches into a contiguous k interval**.
That proposal changes enumeration to get past wheel prime 47 and pays
for those binary searches. SQR-001 instead keeps the existing wheel
and amortizes the post-wheel sieve over its period index. No binary
search or larger wheel is required.

The old observation that three CRT lookups are near the information
floor of a *single candidate's* prefix does not bound the work of a
representation which tests many related candidates at once.

## SQR-002: separate period and residue with explicit bounds

**Priority: prerequisite for the useful window sizes. Status: static
bounds and sizing only.**

### A larger reduction limit alone does not supply a 32-period window

The current engine enforces a conservative bound of the form

`(periods + 1) W + q2 < 2^63`.

See `REDUCE_MAX` at [sqladder_gpu.py](../sqladder_gpu.py), line 325, and
the actual checks at lines 1131-1140. With the present W and q2 = 65536:

| Representation of a window offset | Maximum B under that conservative bound |
|---|---:|
| Combined offset, limit 2^63 | 14 periods |
| Combined offset, limit 2^64 | 29 periods |
| Separate residue and period | No `B W` word-size restriction; other index, table, and coverage limits still apply |

Later engines establish the broader Barrett bound with their G19
emulations, for example [lcml_gpu.py](../../lcm-ladders/lcml_gpu.py),
`g19_reduction_bound_is_the_word` at line 3461. Merely changing the
constant here would still not allow 32 periods.

For the split record, reduce only `r < W < 2^63` on the device and
combine it with a precomputed canonical residue

`period_q[j] = W (J + j) mod q`.

Both modular pieces are below q, so their sum is below 2q and a single
correction suffices. Reconstruct the absolute candidate
`W (J+j) + r` using host big integers when collecting results. Do not
form `j*W` in a u64 temporary and only then split it.

The split route can retain the existing conservative 2^63 proof for
its within-period r. A 2^64 reduction-bound change is therefore
**optional and separately provable**, not a prerequisite merely because
the word "wide" appears in the design.

The CRT level bounds remain binding: W1 and the combined second-level
modulus must fit their current u32 representation; queue indices,
grid dimensions, signed counters, and all packed period fields need
explicit limits. A period index in one byte supports 0..255 only.
Any choice past 256 periods needs a new field width.

### Static memory and work sizing at n = 19

Using the existing three wheel levels and the oracle's residue-count
formula gives:

| Quantity | Exact count |
|---|---:|
| First-level residues, primes through 23 | 1,088,640 |
| Second-level residues, primes 29, 31, 37 | 4,560 |
| Third-level residues, primes 41, 43, 47 | 14,784 |
| Residues in the complete wheel period | 73,390,709,145,600 |

Do not materialize their Cartesian product. Keep the existing factored
enumeration and chunk first-/third-level indices across launches.

As an illustrative cutoff, not a tuned recommendation, the product of
survival factors `1 - 19/q` over the 21 primes from 53 through 151 is
approximately `0.00663922`. This reaches a 0.007 prefix-survival target.
It gives the following planning sizes:

- A u16 table with one initial position per first-level residue and
  window prime takes `2 * 1,088,640 * 21 = 45,722,880` bytes; u32 doubles
  that. Use u16 only after proving the actual stored, possibly
  noncanonical range fits, not solely because q is small.
- In the scalar donor layout, the periodic pattern allocation for a
  prime is `4 * (ceil((2q + 32 NW + 96)/32) + 1)` bytes, where
  `NW = ceil(B/32)`. Summed over those 21 primes, this is approximately
  988 / 1,072 / 1,240 bytes at B = 32 / 64 / 128.
- A straightforward u32 per-period table for `Nq` tested primes costs
  `4 * Nq * B` bytes. Its layout and lifetime must be counted alongside
  the survivor queues, x0 tables, tail masks, and double buffers.
- Queue capacities must include fallback or checked overflow. The
  survival product is a density over the joint modular period; it is
  not a bound on the survivors of one particular block.

These figures are arithmetic estimates from the proposed layout, not
an allocation trace, occupancy measurement, or performance model.

### Price the completed coverage segment

With segments starting at the checkpoint's covered boundary C, a
complete B-period segment covers `B W`. At the historical rate the
conditional median gap is approximately

`(2.72e20 - C) / 1.35e15 = 33.32 hours`.

For whole-segment coverage, replace the gap with
`ceil((2.72e20 - C)/(B W)) * B W`:

| B | Segment span in k | Whole segments to cover rounded median | Required rate factor to finish them in 24 h |
|---:|---:|---:|---:|
| 14 | 8.60846e18 | 19 | 1.40x |
| 29 | 1.78318e19 | 10 | 1.53x |
| 32 | 1.96765e19 | 9 | 1.52x |
| 64 | 3.93529e19 | 5 | 1.69x |
| 128 | 7.87059e19 | 3 | 2.03x |

The small nonmonotonicity comes from rounding to full segments. These
thresholds assume exactly that starting alignment, constant historical
baseline rate, and no setup time. Other alignments require recomputation.
The upper bound on additional work after encountering the least candidate
is one segment; the often-used half-segment average is a heuristic, not a
proof about a particular find.

Partial-segment masking or a policy for finishing an early candidate's
remaining smaller interval could alter this tradeoff, but would add
coverage-state complexity. Start with an explicit full-segment policy
whose least-claim can be audited.

## SQR-003: preserve the coverage claim when enumeration changes

**Priority: mandatory implementation prerequisite. Status: specification,
not a migration performed by this review.**

The current cursor has two meanings: j is completed-period coverage,
while u is progress through third-level residues. See
[sqladder_gpu.py](../sqladder_gpu.py), `sweep`, lines 1280-1310, and
[launch.py](../launch.py), lines 103-128, `load` at line 338, and
`swept_k` at line 373.

A window engine changes the interpretation of a partial launch cursor
even if W, q2, and the final survivor set remain the same. It must not
blindly inherit `u = 546` under a new enumeration.

A conservative adoption policy for this actual checkpoint is:

1. Preserve the original checkpoint as recoverable evidence in the
   implementation workflow; never conduct migration drills on the live
   file.
2. Adopt the exact covered boundary C, the settled terms, completed
   census totals, elapsed history, and discovery count. Start the new
   enumeration at C with a fresh work cursor. Here C is already a wheel
   boundary, so a window can start at period 179 without aligning down
   to a multiple of B.
3. Re-sweep the old incomplete period. Discard its nine uncommitted
   `pending` records from the migrated working state when replaying
   that period; retaining them and rediscovering them would double-count
   census events. Keep their original snapshot for audit.
4. If a chosen new wheel or alignment starts below C, retain C as the
   coverage and census floor. Suppress repeated census below C and
   alarm on a purported new discovery there, matching the existing
   adoption logic.
5. Give the new enumeration an explicit configuration/engine key.
   Campaign load, `--status`, and refusal checks must all use the same
   `CursorPolicy`. The existing version-only inheritance list cannot
   describe a new launch decomposition without additional proof.
6. Save resumable progress after completed work batches, but advance the
   claimed searched-empty boundary and process discoveries in k order
   only after the whole declared segment is complete.

Keep numeric floors explicit: CPU and GPU currently reject windows
starting at or below `max(K_FLOOR, q2)`. A divisibility hit is not a
compositeness proof when the value equals the divisor. Masking an initial
or final partial window must preserve that exception-zone policy and the
exclusive upper ceiling.

The existing `_resume_drill`, `_coverage_claim_drill`,
`_stop_on_discovery_drill`, and cursor-policy drills are starting points,
not proof that the new state machine works automatically. The
implementation needs cases with nonempty pending state, overlap below the
adopted boundary, a find in the middle of a segment, promotion at segment
close, and a stop/resume on both sides of that close.

## SQR-004: cache the model by frontier and audit the actual host path

**Priority: secondary. Status: source observation, no large speedup
claimed.**

`Campaign.ladder()` in [launch.py](../launch.py), lines 288-295, calls
`model.predictions(..., n_ahead=3)` each time. `next_rung` and
`check_rungs` call it again; `status_line` uses `next_rung` around
line 422. The model performs numerical integration inside each
quantile bisection:
[sqladder_model.py](../sqladder_model.py), `expected`, `quantile`, and
`predictions`, lines 74-140.

The frontier-keyed [LiveLadder](../../huntlib/rungs.py) mechanism already
exists at lines 170-220, and prime/linear/factorial/lcm/decimal launchers
use it. It is a suitable structural fix for repeated calculations whose
inputs have not changed.

However, square calls `check_rungs` at **period close**, line 628, and
the heartbeat normally runs every 30 seconds. It does not recompute
predictions on every GPU launch. The historic multi-fold fix in a
different project is therefore not evidence for a multi-fold square gain.

The current engine already queues the next launch before handing the
previous survivors to the host, and explicitly flushes the WDDM command
buffer; see [sqladder_gpu.py](../sqladder_gpu.py), `_sweep`, lines
1311-1375. Preserve that ordering. The old benchmark says host
classification then cost no measurable throughput, so a worker pool is
not a justified first optimization.

Two host costs deserve explicit accounting in Claude's later
implementation validation: serial classification as a much faster device
produces more survivors per second, and checkpoint JSON writes every
`CKPT_LAUNCHES = 16` launches. A new launch has different work, so this
old constant no longer implies the intended half-second interval. Neither
observation is a measured present bottleneck.

## SQR-005: keep proof-ceiling work separate from the one-day target

**Priority: deferred. Status: scope boundary with a possible future
mathematical route.**

`k_ceil(n)` in [sqladder_search.py](../sqladder_search.py), lines 59-81,
returns `(MR_VALID_BELOW - 2)//n^2 + 1`. At n = 19 it is approximately
`9.19e21`, well above the current median and P90. The proposed period
representation removes a word-size restriction on a batch; it does not
alter this proof policy.

A future higher ceiling can use the structure
`(k i^2 + 1) - 1 = k i^2`: factor k once, add the trivial factors of
i^2, and use the existing certificate machinery with recursive proofs
where needed. That route is used by later projects, but square's present
`record_discovery` calls generic `certificate.prove` per value
([launch.py](../launch.py), lines 470-485). A new ceiling therefore
requires deliberate wiring and its own proof, value-size, and
certificate-verification drills.

Do not bundle a ceiling increase into the window-port claim or change
the meaning of the existing near/census classification without stating
it. The current floor and exclusive ceiling should remain part of
SQR-001's equivalence contract.

## Implementation and validation handoff for Claude

This section specifies evidence needed for an implementation decision.
It is future work for Claude, not work performed or to be executed by
Codex as part of a static review.

1. Establish the n = 19 baseline on the actual planned wheel and a
   meaningful height near the saved cursor. Record end-to-end work,
   host load, survivor count, and complete-segment coverage. The old
   n = 16 `SCORE` and n = 18 `SCORE3L` are regression anchors, not the
   primary performance target.
2. Write the exact period-window invariant and a host emulation with
   assertions for every transformed residue, word bound, partial-window
   mask, packed index, and record reconstruction. Include boundary
   values on both sides of each proposed numeric dispatch.
3. Implement a minimal window variant using the existing square wheel,
   kill sets, and q2 first. Keep the CPU dense sieve and direct oracle
   independent. Use an implementation scaffold for comparison while
   developing, then follow repository policy for retiring superseded
   engines.
4. Compare exact sorted survivor sets on identical logical work:
   populated small-wheel windows the CPU can cover; high-base windows;
   crossings of 2^64 in absolute k; and windows near the existing
   ceiling. Include partial final windows and all planned period widths.
   Set equality alone should not hide duplicate emissions: verify
   multiplicity and exact counts as well.
5. Force each shared/global queue overflow path and verify its behavior.
   Check both the narrow and split records if both remain implemented.
   Do not discard an inconvenient survivor or change the mathematical
   predicate to fit a queue.
6. Run migration and campaign-state drills against scratch checkpoints.
   Require interrupted/resumed and uninterrupted executions to agree
   in coverage, census, settled terms, and pending state; verify every
   checkpoint reader accepts precisely the intended versions.
7. Measure alternatives with interleaved paired comparisons and exact
   survivor checks, at n = 19. Count actual candidates/work in partial
   launches. Include window widths and full-segment time-to-coverage,
   rather than choosing the largest isolated kernel throughput.
8. Keep all existing frozen fingerprints. A new launch decomposition
   cannot redefine the 600-old-launch `SCORE3L` work silently: express
   the same old logical candidate subset when checking that fingerprint,
   or preserve an explicit comparison during migration and document a
   separately frozen new shape. Add a headline day-filter shape whose
   workload and fingerprint are independently pinned.
9. Validate the normal engine/classification/checkpoint path using
   short, bounded engine harnesses; do not start a hunt. Record
   correctness gates, kernel and end-to-end rates, memory, occupancy
   concerns if relevant, host backpressure, and the precise baseline.
   Any GPU work must wait for the owner's authorized development
   window.
10. Record the accepted or rejected result under SQR-001/SQR-002 in
    `OPTIMIZATION_LOG.md` and update the [review index](README.md).
    Only a correct, measured improvement should become the default.

Acceptance is not "looks analogous to linear-ladders." The mechanism
must preserve the stream and coverage claims, and its end-to-end gain
must survive the new segment granularity. If the measured gain fails
the appropriate 24-hour threshold, report that result even when it
still saves several hours. If the period lookup, extraction, shared
state, or host load erases the amortization, record which part does so;
that falsifies this particular implementation, rather than proving
all period-window representations impossible.

## Other areas reviewed and their disposition

| Area | Static disposition |
|---|---|
| Quadratic-residue pruning | Already exact in the oracle and engines. No additional residue class can be removed merely because the form contains a square. |
| Forced unit / wheel | Parity forces even k outside the exception zone and is already in the wheel. No new general forced divisor was established. |
| Growing the wheel past 47 | Existing binary-search proposal is distinct and was priced at the earlier frontier. Defer until the simpler fixed-wheel window mechanism is understood. |
| Narrow 2^64 reduction bound | Useful representational option, but at this W it only raises the conservative window cap from 14 to 29. |
| Prefix early exits | Previously measured 0.906x in v5; do not re-propose as a new gain on the unchanged engine. |
| Warp-aggregated pushes | Previously measured 0.887x in v5. A different window extraction structure has a different cost model, but the old negative is real. |
| Larger CRT groups / blocks | Prior 0.33x wider-group result and block/occupancy losses remain relevant to the old engine; no new win established. |
| Persistent tail lanes | Previously measured 0.95x; no new static reason to revive unchanged. |
| Tail overlap | Bounded by the old separate tail share, 10.7%, and already listed as unmeasured. It cannot supply a multi-fold gain alone. |
| Shallower sieve | Old 1.026x device gain cost roughly three times host load; unsuitable as the main one-day strategy. |
| Later decimal engineering improvements | Potential implementation donors after the algorithmic change; their ratios are not square measurements and are not multiplied into this report's estimate. |
| Model and proof machinery | Preserve provenance and uncertainty; stale headline filters or rungs are not current throughput evidence. |
| Checkpoint, logging, promotion | Required correctness work when enumeration changes, including the real pending census in this checkpoint. |
| Independent oracle | Retain the direct divisibility and SymPy implementation; it must not become a wrapper around the proposed window logic. |

The rejected measurements above come from
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), "Priced and REJECTED in v5",
lines 1115-1152. Their scope is the old engine and configuration.
They prevent repetition of unchanged ideas; they do not prove that a
different mathematical organization has the same optimum.

## Source fingerprints

SHA-256 hashes identify the reviewed bytes. Line numbers in this report
refer to these source versions; follow symbols if a subsequent change
moves them. The dated report should retain these hashes after
implementation, while its index records the later disposition.

| File | SHA-256 |
|---|---|
| `sqladder_reference.py` | `F20A37C7FB05ED9C3A5BC7AA2EC38799EF0FB9787EBDAE4A816EAF958195EB82` |
| `sqladder_search.py` | `84354965B3224520BE9EBCBD94939178C13D608E01494E6CCE58FA2ECB1C8357` |
| `sqladder_gpu.py` | `8CD7E004A3CBFB22A10AFEEBA96649813A5FFB5A5C02B4F34D1E7878E082FF47` |
| `launch.py` | `D278EBEC8A6DF913226B8B3C0110E2500E2FE7DA9673AE6298DA1D7A4841910A` |
| `score.py` | `365B2414ED1764299BEC5D50C66409CD5A74D851DEE8AF0F7F15EE21DB3B63CE` |
| `sqladder_model.py` | `11D60E46AF55AA225ECF76D95C0D1EAB1A08B5A0ECB235F1F507350F9757CBF0` |
| `campaign_checkpoint.json` | `5DF64F2E6BDC64DA4AB1CCACDECE08F58AA3184AD891F49DF6870B95972BC563` |
| `linear-ladders/lladder_gpu.py` | `4C828282B8C65DA71364C3567614D2A77446C133E9B9E3F5827F20455F37A905` |
| `lcm-ladders/lcml_gpu.py` | `B35E12B120C966C9701A3E7DB75C5E5968E90473038B1C5088B119524A908ABA` |
| `decimal-ladders/decl_gpu.py` | `F5302045E72FADC978E09908AC1B9DB4814BAB9508A0C7EA17CDAC8C61FA7B0B` |
| `huntlib/rungs.py` | `F95233C2360016FF8D3313D6D3D0CE8888734C263DB6205398868B0D9F14148F` |
| `huntlib/checkpoint.py` | `5B81F9C1F2322A8790C8C24C769BD6C39E6D4614E8DB5F94BA7AC0667F74F02C` |

No source modules were imported to obtain these facts. The only
calculations performed were ordinary integer/floating-point arithmetic
on source-derived counts, bounds, and documented model numbers.
