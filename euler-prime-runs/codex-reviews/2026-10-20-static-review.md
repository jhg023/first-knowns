# Euler prime runs: static optimization review and implementation handoff

| Field | Value |
|---|---|
| Author | Codex |
| Date | 2026-10-20 |
| Project | euler-prime-runs, OEIS A164926 |
| Intended reader | Claude or a later implementer |
| Review mode | Static source and record inspection only |
| Source revision observed | `f8fdb200c56a54aa5e207c146882f7d2d7b87224` |
| Objective | Identify missed mathematical or algorithmic improvements that could put another term within one day of hunting |
| Status | Proposed analysis; no implementation or destination benchmark |
| Workflow | [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md) |

No GPU operation, hunt-module import, self-test, benchmark or campaign was run
for this review. No engine, checkpoint, evidence, benchmark or model file was
modified. Read-only shell commands inspected source, records, Git state and
file hashes; arithmetic used the saved constants. There is no new experimental
result in this document.

This is also the permanent boundary for Codex review work: static mathematical
and algorithmic analysis only, with no GPU use, engine/oracle execution,
tests, benchmarks or campaigns. Future execution described below is a handoff
to Claude or another authorized implementer, never a plan for Codex to run it.
Known host-loop issues are incidental implementation observations, not
mathematical findings or a request for kernel tuning.

## Decision and evidence standard

**EUL-001 is the best-supported route to a one-day Euler search:** use the
newer polynomial window sieve as a candidate generator for the missing
A164926 a(20), through the exact shift to A230663 index 19. Its donor
configuration has both benchmark and campaign measurements. At half the
donor's recorded rate, the remaining line to Euler's documented conditional
median would take approximately 22.9 hours.

That statement is a rate-transfer scenario, not a forecast of the actual
implementation and not a guarantee of a find. The important experiment is
whether the adapted pipeline sustains at least `1.5922e17 p/s` at the current
Euler height, including classification. This is the continuous-line threshold;
setup and final segment completion require the additional allowance calculated
below. The exact reduction is proved below; the performance transfer is not.

EUL-002's safe one-sided rejection and EUL-003's stronger necessary conditions
are additional mathematical/algorithmic opportunities. EUL-004 and the
pool discussion are secondary engineering caveats. Their possible gains
overlap. Do not multiply the donor's rate advantage by the historical host
headroom.

This report uses four evidence labels:

| Label | Meaning here |
|---|---|
| Proved | An algebraic or coverage implication established in this report, with explicit assumptions |
| Code observation | Behavior visible in the inspected source or saved state; not timed |
| Recorded measurement | A measurement already in this repository, attributed to its configuration and date |
| Unmeasured hypothesis | A proposed destination implementation, performance transfer or cost reduction |

The mathematical identity in EUL-001 is already documented and gated in the
polynomial project. The new proposal is to use that project's newer engine for
an independently targeted Euler hunt. EUL-002's safe screening principle is
already implemented in sibling projects; the ordered pool discussed alongside
it was already priced but unbuilt in Euler's optimization log. EUL-003 and
EUL-004 are transfers of
practices already established elsewhere in this repository, identified here
as still absent from the current Euler implementation. None is presented as a
new number-theoretic discovery.

## Snapshot and source map

The Git status query for the Euler project returned no pre-existing changes
when this review started. The repository as a whole was not a clean checkout:
the coordinating review observed modified documentation and an untracked
power-ladders project. The hashes below identify the source bytes actually
reviewed; HEAD alone is not a claim that all repository files matched it.
Check the revision and hashes before relying on a
line reference. Links below are relative to this directory; the cited line
numbers are snapshot locations, and symbols are supplied because lines drift.

| Source | Snapshot location / symbol | Relevance |
|---|---|---|
| [launch.py](../launch.py) | lines 108-145, `CONFIG_KEY`, `CAMPAIGN_FOUND`, `SETTLED_ELSEWHERE`, `NEAR_FROM` | Stored configuration and per-index settled state |
| [launch.py](../launch.py) | lines 157-187, `three_way_verify` | Euler full MR, independent sympy and alternate CPU sieve |
| [launch.py](../launch.py) | lines 226-287, `settled_at`, `event_kind`, `next_target` | Exact-run discovery, near-miss and noncontiguous frontier semantics |
| [launch.py](../launch.py) | lines 309-408, `check_cursor`, `refuse_unreadable_cursor`, `migrate_cursor` | Period checks, restart refusal and existing migration |
| [launch.py](../launch.py) | lines 428-463, `canary_prelude` | Lower-filter and local known-value rediscovery |
| [launch.py](../launch.py) | lines 579-603, `rung_ladder`, `next_rung`; lines 765 onward | Uncached model rebuilds |
| [launch.py](../launch.py) | lines 657-755, segment loop | Serialized sieve/classification and committed coverage |
| [launch.py](../launch.py) | line 1066, `main`, `--n` | Default filter remains 17 |
| [euler_reference.py](../euler_reference.py) | lines 60-82, `value`, `run_length`, `oracle_search` | Definition and independent slow oracle |
| [euler_search.py](../euler_search.py) | line 85, `forbidden`; line 258, `mr_run_length`; line 276, `P_CEIL` | Native Euler killed set, full-base classifier, numeric ceiling |
| [score.py](../score.py) | header, constants and `_bench` around lines 58-109 | Three frozen n=17 survivor fingerprints |
| [euler_model.py](../euler_model.py) | `expected_count`, approximately line 45 | 4,000-point quadrature used by rung rebuilding |
| [campaign_checkpoint.json](../campaign_checkpoint.json) | `key`, `M`, `next_k`, canaries and counters | Actual saved cursor, distinct from rounded README position |
| [Euler optimization log](../OPTIMIZATION_LOG.md) | Phase 7, line 1182 onward | Historical 52% host share and known unbuilt pool |
| [Euler README](../README.md) | lines 315-317 | Conditional a(20) quartiles and median |
| [poly_reference.py](../../polynomial-runs/poly_reference.py) | lines 72-85; `run_of`, `index_of`, `constants` around 316-405 | Existing identity and donor index/run distinction |
| [poly_gpu.py](../../polynomial-runs/poly_gpu.py) | `plan`, line 725; `GpuEngine`, line 2613; `sweep`, line 4220 onward | Donor planner, class-space window engine and work cursor |
| [polynomial launcher](../../polynomial-runs/launch.py) | `plan_for`, line 145; `also_settles`, line 380; `sprp_run`, line 427 | Configuration, existing derived-entry behavior and host-screen example |
| [polynomial benchmarks](../../polynomial-runs/BENCHMARKS.md) | lines 85 and 126 | Exact n=19 donor plan and throughput |
| [polynomial results](../../polynomial-runs/RESULTS.md) | line 244 | Actual n=19 campaign rate |
| [huntlib/primes.py](../../huntlib/primes.py) | introduction and `mr_bases`, `sprp_base2` | 13-base correction date and safe negative tests |

Selected SHA-256 hashes of the bytes reviewed:

| File | SHA-256 |
|---|---|
| `launch.py` | `324E9A847F7E59DE0166E77BA72CBDEEBDDC7CEB242C363F18DD42587D9202F3` |
| `euler_reference.py` | `D6CD4C0AE9C24D445E996D03DF829DAE08AE325DE5B0E8C383EC7E7D488D4279` |
| `euler_search.py` | `2631EC494D23CEC3B434B7A27D438B4B9418F88ABAA0AD4D446F9B34CF70EFFE` |
| `euler_gpu.py` | `A73E1B4459BD7EA07A9B60243C3987DDDB540045655073D399660E2375E6E462` |
| `score.py` | `ADAEC578CE002ECF036F4A1C84525503A345C935EC7C6FFEAD873DD181182E7A` |
| `OPTIMIZATION_LOG.md` | `31AF68DB296F001E5534BA259D7E85A436232172AD4384030A6BCA3212A0A5D7` |
| `campaign_checkpoint.json` | `B13905B5DB8BC1928EE7B79020DCDA924DAB1E9D3CAEED070C3530772C84808F` |
| `../../polynomial-runs/poly_reference.py` | `CAC1C856AB0CC3B8A7108403C9F4C0CBD50D6C2368C1EC245F4FAE726CEE62D2` |
| `../../polynomial-runs/poly_gpu.py` | `4F5971BD643CA26622AB16C2CC9AA3B66669AAE3C52A85D1E818B7779265D11C` |
| `../../polynomial-runs/launch.py` | `C1B2B7682328989FB2F1B185FAFB6417204150BE24D7A301192E7D0C6359624B` |
| `../../polynomial-runs/BENCHMARKS.md` | `8233D584F0CE5FE23A6DC2B06CDC28AE165EBFD5ADCC835D3762FA0FF852E2AA` |
| `../../huntlib/primes.py` | `D8CB255728A99C23540BB1AF545C0D8D6D88CC400556E470C32FCE7E28EA8D3F` |

The local checkpoint has key
`euler-prime-runs/v4/n=17/wheel=37#/Q1=1024/Q2=65536/ceil=1e24`,
`M = 7420738134810` and `next_k = 504519925`. Its saved absolute boundary is

```text
p_boundary = M * next_k
           = 3,743,910,247,218,981,089,250.
```

This is the operational resume boundary, slightly behind the published a(19)
find and the rounded final searched bound. Use the conservative saved boundary
for migration and cost arithmetic. The checkpoint records `canaries_done=true`,
`a21_canary=true`, `survivors=1334119172`, `hits=1` and `wall_s=839633.0638`.
It has no `found` mapping and an empty `events` list; current source tables
already carry a(17), a(18), a(19) and the settled a(21). Do not reconstruct the
frontier from `hits`, `best_near`, or this old checkpoint alone.

## EUL-001: dedicated polynomial window sieve for Euler a(20)

**Status: proposed. Evidence: proved reduction, recorded donor performance,
unmeasured destination pipeline. Priority: first.**

### What is and is not new

The donor oracle already proves the shift relation. Its launcher uses it to
add an `also_settles` result when an A230663 first occurrence has its preceding
integer by two prime. That existing hook is not enough for Euler a(20).

A230663's own a(19) is already settled, and its current campaign uses n=21.
An Euler run-20 corresponds to A230663 index 19, so the ordinary n=21
campaign's sieve excludes it. A dedicated adapter must keep seeking index-19
candidates even though that A230663 term is settled. It must check every
relevant candidate, not only a new A230663 discovery.

### Exact indexing proof

In this subsection `p` is the published Euler prime, `q=p+2` is a temporary
coordinate for the donor's published prime, and `y` is the donor polynomial's
argument. These are explanatory coordinates, not replacements for the letters
in either entry's evidence header.

For every integer y,

```text
y*y + 3*y + q = (y+1)*(y+1) + (y+1) + p.
```

For Euler run exactly 20, its value at x=0 is p; its values at x=1 through
x=19 correspond to the donor values at y=0 through y=18; and the Euler
stopper at x=20 corresponds to donor y=19. Hence

```text
Euler run(p) == 20
iff
p is prime
and q=p+2 has A230663 index 19
    (prime at y=0..18, composite at y=19).
```

The polynomial project's `run_length` counts positive-argument shifts after
the base prime. At A230663 index 19 its internal run is **18**, because
`run_of("A230663", 19) == 18` and `index_of("A230663", 18) == 19`.
An implementation comparing that internal run to 19 would target the wrong
Euler term. Use the entry index or verify Euler directly after translation.

These two filters with "19" in their name are different:

| Filter | Required Euler values in its small-prime sieve |
|---|---|
| Native Euler n=19 | x=0..18 |
| Donor A230663 index 19, translated by q=p+2 | x=1..19 |
| Native Euler n=20 | x=0..19 |

Every Euler candidate with run at least 20 survives the donor's index-19
small-prime sieve, provided all relevant values exceed the sieve primes.
The donor sieve is a necessary-condition generator. It does not establish
primality of p, exact run length, minimality or the stopper by itself.
The exact-run equivalence above concerns fully classified values, not the
raw sieve stream. In particular, an Euler run-19 value whose x=19 stopper
has no small factor can still survive the donor filter. The adapter changes
which shorter runs are sampled; it does not remove every such run.

### Initial implementation shape

Use the donor GPU window mechanism at **A230663 filter/index 19**, translating
each proposed q to `p=q-2`. Keep the current Euler project and its five public
Python roles. A reusable GPU mechanism can be extracted into a Python helper
package if useful, but do not make the Euler oracle or CPU parity engine call
the GPU implementation or borrow its killed-set construction.

The deliberately conservative first implementation keeps the donor's known
configuration so its measured rate is a meaningful comparator:

| Setting | Donor n=19 value |
|---|---|
| Class | q = 1 (mod 6), hence p = 5 (mod 6) |
| First wheel level | 5, 7, 11, 13, 17, 19, 23 |
| Second level | 29, 31, 37 |
| Third level | 41, 43, 47 |
| Full absolute period | 47# = 614,889,782,588,491,410 |
| Sieve depth | 32768 |
| Window | 128 periods, narrow record |
| Block shape | (16, 2) in the donor's notation |

The algebra proves the map of the forced class as well. Avoid creating a
second unintended factor of six: the donor stores an absolute period `W`
and a class-coordinate period `Wp`, with `W=unit*Wp`. Its numerical `j`
cursor and its per-launch progress must be interpreted using the correct one.

Initially keep the donor's planner output explicit. Its `plan` optimizes for
A230663's own model and floor, not Euler's conditional remaining distribution.
Re-running that planner after transplant would not constitute Euler-aware
planning. Only compare alternative plans after the fixed donor configuration
is correct and measured.

A later native Euler window specialization could sieve all twenty forms,
including p, by using constants `{x*x+x: x=0..19}`. It might reduce the host
queue further and choose a better wheel. It is a separate experiment: its
rate and candidate density are not the donor rate, and it needs its own
fingerprint. The exact-shift adapter is the simpler initial hypothesis.

### Survivor streams and independence

Let S_D be the donor's pre-MR survivors at index 19 over
`[p_lo+2, p_hi+2)`. The adapter's raw proposed stream is exactly

```text
S_A = sorted(q-2 for q in S_D).
```

It should match an independently constructed CPU sieve for the Euler forms
at **x=1..19**, at the same sieve depth. That CPU construction can be a
separate explicit path in `euler_search.py`, using plain integer arithmetic;
the oracle remains slow and direct. Reusing donor root tables in both sides
would defeat the independence claim.

S_A does not generally equal the native Euler n=20 sieve stream: it has not
tested x=0, namely p. It also does not equal the current n=17 stream, which
tests a different form set and a different sieve depth. A parity test against
either stream without accounting for those differences is invalid.

Two valid contracts are available:

1. **Raw adapter contract:** freeze S_A against the independent x=1..19 CPU
   sieve, then verify/classify p on the host with Euler's native machinery.
2. **Complete Euler sieve contract:** independently test p for all sieve
   primes as well, so the filtered S_A matches the native n=20 CPU survivor
   set at that depth. Preserve both raw and filtered counts in the diagnostic
   harness so the extra filter cannot conceal a generation error.

Choose one and document it before timing. Do not use exact-run classification
as a substitute for equality of the appropriate pre-MR survivor streams.
Every retained proposed result is still classified in Euler coordinates;
the stop at x=20 is checked there. Longer runs must be read to their true
end and handled by Euler's per-index settled state.

The three existing n=17 fingerprints in `score.py` are:

| Existing anchor | Survivor count | Checksum |
|---|---:|---:|
| SCORE | 178 | 120489734542316 |
| SCORE128 | 178 | 133625321009290 |
| SCORE_WIDE | 6996 | 71330844491704598 |

They are historical cross-generation anchors and are not numbers the new
index-19 adapter should be made to match by editing constants. Preserve them
under their original form/depth contract when replacing a general Euler
engine. Add a distinct, independently justified fingerprint for the new
production contract and a long-enough live-filter benchmark. Record any
deliberate work-shape change explicitly. Do not carry a second superseded
public GPU engine merely to retain old behavior; maintain semantic coverage
in the new mechanism and keep retired implementation in history.

The donor's XOR of q is not Euler's XOR of p. Recompute the translated
checksum over exact integers; adding/subtracting two from an XOR is not a
valid conversion. Compare sorted lists in parity gates, not only XORs.

### Exception floor and numeric limits

Divisibility by a sieve prime does not imply compositeness when the form
equals that prime. At production height this cannot occur; it still matters
for canaries, fresh runs and gates.

The donor requires q greater than its sieve depth. Euler retains its own
`P_FLOOR=100000` and `P_CEIL=10**24`. For the adapter, require
`p >= P_FLOOR` and `q=p+2 > q2`; if an extra sieve of p is used, require
p greater than q2 as well. Handle the finite lower interval by Euler's
direct oracle/prefix path. Translate both bounds of a half-open window
exactly: `[p_lo,p_hi)` becomes `[p_lo+2,p_hi+2)`.

Do not inherit the donor's `10**40` ceiling as an incidental effect of engine
reuse. The initial adapter should retain Euler's current proof regime and
ceiling. Native Euler verification must still prove every value and identify
the actual composite stopper. Raising a ceiling is a separate task.

### Checkpoint migration, ordering and census

Migrate from the saved absolute **p** boundary, not from a donor checkpoint
and not by copying `next_k` into a different unit. For the shifted engine:

```text
q_boundary = p_boundary + 2
j_start = floor(q_boundary / W_new)
```

Retain the exact old p boundary as a lower clip. Re-sieve the overlapping
new period or segment, but do not count or rediscover p below that boundary
again. This avoids duplicating old census records across a seam much larger
than the old migration code anticipated.

Persist separately:

- the last fully classified coverage boundary in p;
- the donor period/window coordinates and slice/launch cursor for work
  inside that segment;
- pending classified candidates or the replay boundary sufficient to
  reconstruct them without losing candidates or counting them twice;
- the configuration, including family reduction, filter, sieve depth,
  record type, wheel levels, unit and window;
- existing discoveries, census, canary status and elapsed-time accounting.

The donor yields sorted survivors **within a launch**, while different
residue slices cover the same numerical segment. A candidate seen early
in one slice may not be the least p in that segment. Collect and classify
all required slices, then process qualifying candidates in ascending p
before advancing coverage or certifying a first occurrence. A process pool
must preserve this distinction too.

The old checkpoint's missing `found` field is not permission to forget
the source's campaign-known values. Preserve a(17), a(18), a(19) and the
settled a(21), and retain newly discovered exact-run indices independently.
Once a(20) lands the next target is a(22), because a(21) is already settled.
A donor filter of 21 would be relevant to that next Euler target, but only
after all candidates in the completed current segment have been classified
and its coverage safely carried.

The adapter's filter omits some shorter Euler runs by construction.
Specifically, a genuine run-19 near miss can fail the new donor sieve on
the Euler x=19 value and never reach classification. Existing census counts
are already counts of sieve survivors, not a complete count of all primes.
Log the changed filter/census interpretation and do not merge counts as
though their sampling condition were identical. If retaining a complete
stream of run-19 near-miss candidates is desired, a weaker adapter at donor
index 18 or a native Euler filter 19 is a separate rate/semantics choice.

Invalidate engine-specific canary completion on migration. Known shorter
runs need dedicated canary filters that can actually admit them; passing
the new target filter to every known run is not a valid positive control.
Keep the low-range exhaustive drills, above-2^64 canaries, the a(19)
frontier canary and the settled run-21 canary. Existing a(21) evidence
remains a known result, not a fresh discovery.

### One-day arithmetic and uncertainty

The README's conditional a(20) median is approximately `1.75e22`, after
conditioning on the prior empty search. From the conservative saved cursor:

```text
L = 1.75e22 - 3,743,910,247,218,981,089,250
  = 13,756,089,752,781,018,910,750.

R_24 = L / 86400
     = 1.5921400176829883e17 p/s.
```

The donor n=19 rate in its benchmark table is `3.34e17 p/s`; its actual
76.2-minute campaign leg held `3.44e17 p/s`. Use the smaller benchmark
number for the following scenarios:

| Sustained adapted rate | Fraction of recorded donor rate | Sweep time to Euler's conditional median |
|---|---:|---:|
| 3.34e17 p/s | 100% | 11.44 h |
| 2.505e17 p/s | 75% | 15.25 h |
| 1.67e17 p/s | 50% | 22.88 h |
| 1.59214e17 p/s | 47.67% | 24.00 h |

One full 128-period donor segment spans
`78,705,892,171,326,900,480` of p-line. At the donor rate that is
3.93 minutes, or 7.86 minutes at half rate. A least-value claim waits for
segment completion, so include that rounding, setup, canaries and final
verification when evaluating a strict 24-hour wall-clock budget.

For a setup/verification allowance B seconds, the rate criterion becomes
`R >= (L + segment_rounding) / (86400 - B)`, not merely R_24.
Near a 24-hour estimate a few minutes matter. This is time for the owner
to run a finished implementation, not time to design, validate and hunt
from scratch in the same day.

Uncertainty is material:

- The model median is a conditional 50% location, not a deadline or bound.
  The documented conditional quartiles are approximately `8.5e21` and
  `3.83e22`; even the Q3 sweep would take about 28.7 hours at the full
  donor benchmark rate.
- No Euler adapter or adapted host path has been timed. The donor's
  values, host screen, sieve depth and production filter differ from the
  old Euler implementation.
- The benchmark and campaign donor results support a comparator, but
  GPU clocks, workload and residue-height effects still require a paired
  destination measurement.
- Euler's historic `1.85e16 p/s` campaign rate predates the correction to
  thirteen MR bases above 2^64. It is not a current baseline measurement.

The rate threshold is more informative than asserting an "18x optimization":
the adapter needs approximately half the demonstrated donor throughput to
meet the median's one-day sweep budget.

## EUL-002: one-sided compositeness screen

**Status: proposed. Evidence: proved safe rejection rule, code observation,
and an unmeasured transfer from an existing sibling implementation.**

The central algorithmic idea is to pay for a proof of failure before paying
for a full primality decision on every prefix member. A failed strong
probable-prime test proves compositeness. For a candidate that cannot reach
the census floor, the exact short run is immaterial; for any candidate that
does reach it, recompute the true run with the complete verification chain.
This preserves every mathematically relevant result while avoiding full-base
tests on most discarded prefixes.

The segment loop calls `eng.survivors_pre_mr`, waits for all survivors, then
calls full `mr_run_length` serially for each (`launch.py`, lines 657-675).
The classifier tests every chain value with `mr_is_prime`
(`euler_search.py:258`). There is no batched process pool or two-pass
below-census screen in this path.

As secondary implementation context, Euler's Phase 7 optimization log
measured approximately 9.7e8 survivors at
77 microseconds each: 20.7 host hours within a 39.8-hour leg, versus
19.1 device hours. It explicitly proposed a host pool but did not build it.
Removing the entire historical host cost gives a 2.08x ideal ceiling for
that measured pipeline. Real batching, ordering and overlap costs reduce
that ceiling; the current MR base set changes the baseline. Do not quote
2.08x as a newly measured result.

Future implementation sequence for Claude:

1. Add a module-level worker function suitable for Windows spawn, with
   batches of survivors and no device initialization in workers.
2. Screen the Euler chain with `sprp_base2` until it fails or reaches the
   census threshold. A base-2 failure proves that value composite.
3. If the screened run is below `NEAR_FROM=13`, discard it for census and
   discovery purposes. Its exact short run need not be recorded. If it
   reaches the floor, recompute its exact run with the full base set.
4. Count all sieve survivors as before; only confirmed long runs affect
   the census, near misses, discoveries or certificates.
5. Overlap classification of a completed sieve segment with device work
   on the next, while committing only fully classified coverage.
6. Measure demand and size the pool from required core-seconds per second,
   not from the number of installed cores. Maintain the desktop load budget.

A base-2 screen can overstate a short run but cannot understate a true prime
run. The full re-read is essential: a pseudoprime at an early position must
not turn into a spurious exact run or census count. A cap reached by the
screen is not an exact stopper; re-read beyond it where required.

Parent-side collection must not announce results in completion order.
Preserve numeric order and segment coverage; do not submit individual
candidates as separate futures. Specify exception propagation, cancellation,
pool shutdown and pending-segment replay before calling the path resumable.
Use the existing shared pool/worker support where appropriate, retaining
Euler's independent oracle and verifier.

This work is useful even if EUL-001 is rejected. It is also likely part of
making EUL-001 reach its donor comparator. It cannot be treated as another
independent multiplier on top of that comparator.

## EUL-003: retire the fixed filter 17 with correct migration

**Status: proposed. Evidence: code observation and proved necessary-condition
implication; speedup unmeasured.**

`main` defaults to `--n=17`, the saved key pins n=17, and `hunt` constructs
one engine before its segment loop. `next_target` moves the reported open
term, but the sieve filter itself never moves. With a(17), a(18), a(19)
and a(21) settled, a(20) is the relevant first target.

For the existing native Euler engine, consider:

- **Filter 19:** every Euler run-19 near miss remains eligible, while
  constraints at x=17 and x=18 reject candidates that cannot matter to the
  next open term or its immediate near misses.
- **Filter 20:** directly focus on the first open term, with the changed
  near-miss sampling noted under EUL-001.

A larger required prefix only removes candidates that cannot have the
required run, above the exception floor. That correctness implication
does not establish a performance gain: the engine's wheel, per-thread
setup and derived queue shapes change with n. Measure each whole plan.

Two concrete integration traps make this more than changing a default:

1. **Same-period configuration changes are not migrated.** In the inspected
   `migrate_cursor`, `old_m == new_m` returns immediately before updating
   the key or resetting canaries (around lines 382-389). If both filters
   choose 37#, `--migrate-cursor` therefore leaves an n=17 key unchanged.
   The loader then refuses the n=19/n=20 key. Compare full configuration,
   not just M; keep the absolute boundary while updating the declared
   form contract. Changing a wheel period and changing a filter are
   distinct migration cases.
2. **Some canaries are shorter than the new filter.** `canary_prelude`
   creates `engine_factory(n)` and reuses it for the known run-18,
   run-21 and run-19 values. A shorter known run is not guaranteed to
   survive a longer filter, so this is not a valid forced positive
   control after promotion. Give shorter canaries appropriate dedicated
   filters; retain a populated positive control for the actual new filter.

The existing migration docstring allows a little census drift from an
overlapped period and assumes approximately three survivors. That historical
assumption must not be carried to a 47# period and a new slice-based engine.
The robust policy is an absolute lower clip and explicit coverage/counter
commit semantics, as described under EUL-001.

For runtime promotion, derive the lowest open exact-run index, accounting
for known a(21). A value with run 22 settles a(22) only, not a(20).
Process the complete classified segment before promoting, and preserve
which later indices have already been searched over that line. Version
the checkpoint and benchmark contract when filter behavior changes.

## EUL-004: incidental observation, live rung ladder

**Status: proposed. Evidence: code observation; destination cost unmeasured.
This is a known repository failure pattern still present in Euler, not a
mathematical finding.**

`rung_ladder` calls `rungs_for` on every invocation. `rungs_for` requests
up to four quantiles, each with 80 bisection steps; each step calls
`euler_model.expected_count`, which builds a 4,000-point numerical integral.
There are also ceiling checks and other model calls. The main segment loop,
`next_rung`, startup and heartbeat formatting all request the ladder.

The inputs that determine the quantiles are the current target, its model
constant, the chosen integration/rung convention and the enforced ceiling;
they do not change on every segment. The current absolute rung construction
does not depend on position. Keep its numerical answers initially and cache
that result on its actual inputs, using the shared `LiveLadder` pattern or an
equivalently explicit immutable cache. Rebuild on target/model/ceiling change.

Do not silently change from unconditional to conditional quantiles as part
of this performance patch. If conditional live rungs are wanted, that is a
separate semantics change: key their conditioning boundary too. Keep the
one per-status live probability calculation separate from the cached
quantile ladder.

The analogous shift-ladders bug produced a large measured gain elsewhere,
but its 3.47x/2.42x ratios do not predict Euler's ratio. Euler's shorter
quantile construction, segment duration and current device/host balance
are different. Record the rebuild count first, and later measure actual
wall time charged to the rung path.

The cache must be safe for a heartbeat read while the main thread changes
the target. Publish a complete immutable ladder keyed by its inputs, rather
than mutating a shared list in place. Retired a(20) rungs must disappear
when it settles; a(21) is already known, so the new target is a(22).

## Implementation order and future acceptance work

The steps here are addressed to Claude or a later authorized implementer.
Codex remains static permanently and does not execute these checks, including
CPU-only oracle or engine checks. This review leaves all gates and benchmarks
unrun. A later implementer uses the regular Python installation, no virtual
environments, and follows the owner's authorization and repository rules for
validation. Agents do not start production campaigns; the owner runs the
eventual hunt.

1. **Re-read the source snapshot and current checkpoint.** A later
   implementation must not assume this report's cursor is still current.
   Preserve existing results, read repository conventions, and identify
   the project authorized for the later validation window.
2. **Write the survivor and resume contracts first.** Choose EUL-001's
   raw or complete sieve contract, define the q-to-p mapping, lower clip,
   sorted segment commit, pending state and census behavior.
3. **Prove the independent CPU adapter and mapping on small windows.**
   Keep `euler_reference.py` slow and direct. Avoid optimization or donor
   table reuse in the oracle.
4. **Adapt the fixed donor GPU configuration.** Reuse its existing
   mechanism and constants before introducing a native twenty-form
   specialization or a new planner.
5. **Add the host path and configuration-aware migration.** Treat
   EUL-002/EUL-003 prerequisites as correctness work, then independently
   price their speed changes. EUL-004 is a small separable patch.
6. **Run future destination gates and freeze the new shape.** First
   validate populated parity and ordering; only then measure throughput.
7. **Run short paired destination measurements.** At the current Euler
   height, compare identical work and record device seconds, host
   core-seconds and full wall seconds per p-line. Use a second unchanged
   arm to quantify noise where necessary. Recheck the work fingerprint
   on each run.
8. **Record the decision.** Link each finding ID to implementation and
   measurements in the project optimization log and this directory's
   index. Supply the owner the eventual command and expectation only
   after the implementation and checks support them.

Required future correctness tests:

| Area | Acceptance condition / deliberately wrong variant to catch |
|---|---|
| Index map | Known Euler p maps to donor q=p+2 with the correct index; an internal-run off-by-one is rejected |
| Extra p primality | Donor candidates with composite q-2 never become Euler results |
| Exact stopper | x=20 composite distinguishes run 20 from longer runs; a run-21 value cannot be reported as a(20) |
| CPU/GPU independence | Populated pre-MR streams match the selected independent CPU contract at low, current, above-2^64 and near-ceiling windows |
| Shifted bounds | Half-open endpoint tests at p_lo, p_hi, and q=p+2 catch +/-2 clipping mistakes |
| Exception floor | Values equal to a sieve prime are handled by the prefix/oracle path, not silently killed |
| Fingerprints | Original n=17 contracts reproduce their frozen counts/checksums where supported; new production contract has its own independently justified fingerprint |
| Numeric ceiling | Adapter cannot silently inherit donor's higher ceiling or wrap offsets/periods |
| Slice ordering | A smaller hit placed in a later residue slice defeats an attempt to publish the earlier returned hit |
| Pool ordering | Deliberately reversed future completion does not change classifications, census, evidence or least claim |
| Resume | Unsplit stream equals split/resumed stream, including interruption before and after pending classification and segment commit |
| Migration | Different-period and same-period/different-filter migrations both preserve absolute coverage and update configuration; unknown keys are refused |
| Census | Replayed overlap is not counted twice; the old census remains intact with its original interpretation |
| Known terms | Old checkpoint without `found` still knows campaign a(17)-a(19) and settled a(21); neither is rediscovered as a new term |
| Canaries | Short known runs use appropriate filters; actual production filter has a populated positive control |
| Two-pass screen | Strong pseudoprimes cannot create false long runs; every counted or reported run agrees with full MR and independent oracle |
| Ladder cache | Repeated reads at unchanged inputs perform zero rebuilds; a target change performs one rebuild and retires stale rungs |
| Discovery protocol | Genuine known claim accepted, planted wrong claim rejected, independent sieve and stopper witness retained |

Required future performance decisions:

- **One-day criterion:** adapted full wall throughput at the live height
  meets the budget formula above, after realistic setup and segment
  completion allowances. A GPU-only number does not pass.
- **Reject the rate-transfer claim** if the adapted pipeline cannot reach
  that threshold; it may still be a worthwhile faster engine, but the
  one-day median case would not be established.
- **Reprice the host** after every material sieve change. Old 77-microsecond
  costs and donor 0.43-core demand are comparators, not destination facts.
- **Time the relevant window length.** The old absolute benchmark spans
  are smaller than the new full wheel period; they remain useful correctness
  anchors but do not resolve production throughput of the new design.
- **Keep unsuccessful experiments.** Record unchanged fingerprints, phase
  splits and paired ratios before deciding an option lost; do not turn
  analytical instruction counts into measurements.

## Already explored paths and coverage disposition

This review did not treat every familiar tuning idea as a new proposal.
The optimization log records:

- The 37# wheel was eventually implemented in factored form; its earlier
  memory, queue-shape and benchmark-shape rejections were superseded.
  Recommending "try 37#" would repeat completed work.
- Folded pattern tables measured approximately 0.685x; W=128 pattern
  expansion measured approximately 0.188x; CRT-paired tables hit a measured
  footprint cliff. These are not untested cheap wins.
- The old saturation guard lost at approximately 0.818x. A generic
  "skip dead words" recommendation must account for the warp branch
  behavior that was already measured.
- The 41# wheel was priced at approximately 1.708x fewer candidates at
  n=17, but never implemented in the latest Euler phase. That is an
  analytical candidate-count factor, not a runtime result. Its setup,
  segment shape, queue and changed-filter costs require remeasurement.
- The base-prime-only device primality screen was already priced as
  eliminating only about 18% of host time, approximately 9% of the old
  whole leg. The host's expensive survivors were elsewhere in the chain.
- Cold-stage compaction was bounded by a roughly 6% phase in the old
  profiles. It is not the leading route to an 8.6x end-to-end gain.

The modern donor engine already has packed window tables, compaction,
folded wide rounds, generated tail rounds and a cold overflow fallback.
Its 1.05-1.06x fallback/queue improvement is already inside the cited donor
rate. Do not count it again as an additional adapter improvement.

| Reviewed area | Disposition |
|---|---|
| Mathematical definition and exact-run indexing | Retain independent Euler oracle; EUL-001 reduction proved explicitly |
| Current frontier versus source defaults | Saved n=17 cursor and noncontiguous settled indices identified; EUL-003 |
| GPU representation and wheel | Current 37# factored engine understood; EUL-001 uses a measured newer donor mechanism |
| Host primality/classification | Serial full-base path remains; EUL-002 |
| Model/rung overhead | Repeated quadrature remains; EUL-004 |
| CPU/GPU parity and known-value tests | Preserve independent constructions; changed form contracts and canary filters need new drills |
| Checkpoint/resume and least-value ordering | Current whole-segment ordering does not directly cover donor slices; explicit migration/commit requirements above |
| Benchmarks and fingerprints | Historical n=17 anchors retained; new live-filter contract and longer performance shape required |
| Ceiling/certificates | Current 1e24 retained for initial adapter; raising it is unnecessary for this median target |
| Prior negative experiments | Read and listed; not repackaged as new speedups |
| External OEIS status | Not refreshed; the user reports submissions, and this review makes no claim about current external entry contents |

The unresolved questions are destination throughput, the best census/filter
tradeoff, host demand under the corrected primality bases, and the cost of a
correct slice-aware resume implementation. Those questions are concrete enough
for a future validation session performed by Claude or another authorized
implementer. Until it exists, EUL-001 is a strong
implementation candidate with a testable one-day threshold, not a completed
optimization.
