# Clique ladders: static mathematical review, 2026-10-20

**Author:** Codex (OpenAI). **Scope:** A093483, A103828, A037100, A119752,
A119751, A133761, and their five affine-derived entries. **Status:**
analysis only; no optimization implemented.

This report follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex's role
is always static. Source, documentation, saved evidence and checkpoints
were read; hashes and lightweight arithmetic were used. No GPU, project
imports, model execution, oracle execution, tests, benchmarks or campaigns
were used, and no engine or checkpoint was changed.

**No new substantial speedup is established for the current searches.**
The existing engine already has the useful forced-class reduction,
period-window sieve, subset wheels, wide candidate representation and
depth planning. The most substantive new result is **CLI-001**: all six
families are locally admissible at every valid prefix, contrary to the
project's claim that a future prefix might cover every residue modulo a
prime. This is a proof and diagnostic correction, not an infinitude proof
or a new candidate filter.

**CLI-002** matters to the one-day question: saved forecasts and frozen
campaign benchmarks concern older prefixes, and A119752's checkpoint
contains three completed segments beyond its last find despite the results
document saying no family has such coverage. **CLI-003**, reusing the rest
of a find's completed segment, is mathematically valid but was already
priced and declined at a small benefit. Neither justifies promising another
term within one day.

## Evidence and snapshot

**Proved** means a mathematical implication derived here from its stated
hypotheses. **Observed in source/data** means a stored value or code path,
not fresh execution. **Previously measured here** identifies a historical
project measurement. **Model-derived estimate** is arithmetic under a
stated probability or rate assumption. **Unmeasured hypothesis** needs
future implementation and validation. No donor rate is used in this report.

The inspected Git HEAD was
`f8fdb200c56a54aa5e207c146882f7d2d7b87224`. The worktree had other local
documentation changes, so the following hashes identify the actual
reviewed source. Links are relative; symbol names and snapshot line numbers
make the references useful if files later move.

| File | SHA-256 |
|---|---|
| [clique_reference.py](../clique_reference.py) | `f6042dedc4abbcc8c30fe1e28f63dd26b332a68ec24bc0f840860373a2e43db3` |
| [clique_search.py](../clique_search.py) | `a30a8d6bcbf4d89f209b404cf905b5afc30b6a31a74c114dda91c96f3b41ff81` |
| [clique_gpu.py](../clique_gpu.py) | `c7c45c4fb31f7e3ad7fd8d199fbef94ffe2aec2d8386bbc3e4f82a65e9e1f54a` |
| [clique_model.py](../clique_model.py) | `c36d43750c25fec4c6e68a495b95726aa178dea568e59338ea04ef501c0aadf6` |
| [launch.py](../launch.py) | `86210e1bc2860a1b8676e415befa19d4b3281488aff4bbd7a697bf671d3e44b4` |
| [score.py](../score.py) | `3f4984f732ef9a56f98bc79cae481af633440b5c2e5ccb110ca8e89772f54525` |
| [model_results.json](../model_results.json) | `306b09ea05aba596c91124ba894ec4a63ec0fecb15d803ebe38ce0961912d550` |
| [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) | `0b4f84c182d3798370201f412fea42fc334c304ddd95a361a6a7c80fe6ef7c89` |
| [RESULTS.md](../RESULTS.md) | `ab391cafe5bbe4056476c667000ae7fe44e83c6b0839f5f799e40107e40297a7` |

## The object being searched

Every primary family chooses **a(n)** as the least integer strictly greater
than a(n−1) for which

`a(n) + a(i) + 1` is prime for every `1 <= i < n`,

with the following start and additional requirement. The published term has
no separate letter in the entry's definition; the source's candidate
variable `x` denotes a(n).

| Family | a(1) | Additional requirement | Recorded last term | Open index |
|---|---:|---|---:|---:|
| A093483 | 2 | None | a(21) = 217741095176373431678 | 22 |
| A103828 | 1 | None | a(21) = 4584245071483320696489 | 22 |
| A037100 | 4 | None | a(21) = 140672999403766760844 | 22 |
| A119752 | 2 | `2*a(n)+1` prime | a(20) = 23912359356224311448 | 21 |
| A119751 | 1 | `2*a(n)+1` prime | a(20) = 5566439406842300763219 | 21 |
| A133761 | 5 | a(n) prime | a(20) = 1206761188144986057371 | 21 |

Each current filter has **21 linear forms**: 21 shifts at index 22 for the
first three families, and 20 shifts plus an extra form at index 21 for the
last three. The form list is determined by the actual prefix, not merely by
the index.

The source of the definitions and maps is
[clique_reference.py](../clique_reference.py), `FAMILIES`, `KNOWN`,
`forms`, `run_length`, `is_term` and `first_x`. The recorded new terms are
in [RESULTS.md](../RESULTS.md) and the per-term [evidence directory](../evidence).
The evidence files carry the prefix, values, verification flags,
certificates and least-claim interval; the report has not rerun those
checks. For example, [A119752 a(20)](../evidence/A119752_a20_23912359356224311448.json)
has its prefix at line 13, verification at 85, certificate status at 212
and least claim at 225.

A **full run** means all conditions at the fixed filter hold. It is not an
exact-length prime ladder with an additional required stopping composite.
`run_length` returns zero if the extra condition fails, otherwise one plus
the number of initial compatible prefix terms, capped at the filter.
There is no requirement that `2*a(n)+1` be composite in a family without
that extra form. Strict ordering prohibits one integer from settling two
successive primary terms. The next filter is created only after a(n) is
settled. `launch.verify`, lines 408–412, accordingly supplies no stopper
for a full run.

The five derived entries are already exact, increasing changes of
variables; they require no separate search:

| Derived entry | Map from primary family | Preserved prime condition |
|---|---|---|
| A180565 | `2*A093483(n)+1` | Pairwise average becomes the primary sum plus one |
| A115760 | `2*A103828(n)+1` | Same identity |
| A128933 | `A103828(n)+1` | Definition is the translated sequence |
| A120403 | `A119752(n)+1` | Pairwise sum minus one and diagonal `2*b−1` become the primary forms |
| A113875 | `2*A119751(n)+1` | Pairwise average becomes the primary shift form; primality of each mapped term is the primary extra form |

The maps preserve strict order and the candidate domains used by their
definitions, so they preserve greedy leastness, not just primality of
already selected values. `g2d` checks the stored mapped lists and their
own conditions; `launch.also_settles`, line 472, writes the derived claims.
No further affine equivalence between the six different primary prefixes
was established.

## Existing sieve, exceptions and coverage

For a form `a*x+b`, a prime q not dividing a kills exactly
`x = -b*a^(-1) (mod q)`. Deduplication across all forms is essential.
When q divides a, the only relevant case is `2*x+1` at q = 2, which kills
nothing. `clique_search.killed_residues`, line 127, implements the algebraic
sets; the oracle independently walks residue classes.

A prime that leaves exactly one class forces a congruence, not necessarily
a divisor. The GPU writes `x = r0 + unit*t` and transforms the kill sets;
the CPU marks a dense x interval. The recorded units are 6 for A093483,
A037100 and A119752, and 30 for A103828, A119751 and A133761. The documented
classes are respectively 2, 0, 2 modulo 6 and 9, 9, 11 modulo 30.
`forced_unit`, `unit_residue` and `assert_unit` derive and validate this
representation; forcing modulo q never licenses forcing modulo q squared.

The period-window representation already amortizes sieve work over
consecutive wheel periods. `clique_gpu.window_patterns`, line 1327,
constructs the periodic patterns; the module's derivation at lines 12–31
explains the inverse wheel step. `wheel_candidates`, line 444, considers
greedy prime subsets by `-log(keep(q))/log(q)`; `plan`, line 565, minimizes
modeled time through the segment containing a find. It does not minimize
candidate density in isolation.

The small-prime equality exception is handled by the strict engine floor
`x > q2` (`clique_search.k_floor`, line 115), since every tested value is
at least x. All current floors are far above q2. The candidate ceiling is
the exclusive `10^40`, while the deterministic Miller–Rabin crossing is
the minimum over the forms of
`floor((MR_VALID_BELOW - 1 - b)/a) + 1`; it is about `1.66e24` for the
diagonal families and `3.3e24` for the others at these prefixes.
Above it, discovery certificates are required separately. The narrow
record requires `(segment_periods+1)*W' + q2 < 2^64`; the wide record
requires `W' + q2 < 2^64`. These are distinct from the candidate ceiling.
The current 21 forms also fit the 32-slot residue-list limit. None of
these limits is relaxed by a proposal in this report.

Saved checkpoints read on 2026-10-20 give:

| Family/checkpoint | Period j | Launch u / launches in segment | Period W | Periods per segment | Saved k, exclusive coverage boundary |
|---|---:|---:|---:|---:|---:|
| [A093483](../campaign_checkpoint_a093483.json) | 6 | 27751 / 203112 | 32589158477190044730 | 224 | 195534950863140268380 |
| [A103828](../campaign_checkpoint_a103828.json) | 122 | 7647 / 179998 | 37508276737897976010 | 224 | 4576009762023553073220 |
| [A037100](../campaign_checkpoint_a037100.json) | 4 | 543 / 290160 | 32589158477190044730 | 224 | 130356633908760178920 |
| [A119752](../campaign_checkpoint_a119752.json) | 422 | 5662 / 13392 | 614889782588491410 | 128 | **259483488252343375020** |
| [A119751](../campaign_checkpoint_a119751.json) | 170 | 0 / 181350 | 32589158477190044730 | 224 | 5540156941122307604100 |
| [A133761](../campaign_checkpoint_a133761.json) | 37 | 5855 / 154882 | 32589158477190044730 | 224 | 1205798863656031655010 |

The files' saved dates are September 19–20, 2026. These are saved states,
not observations of running processes. All have `cover_x = 0`. Runtime
checkpoint files may be absent from a published clone.

For five families, k is below `k_start = a(n−1)+1`: the initial period
starts below the greedy floor and has not closed. Their partial launch
work does not establish a later contiguous empty interval. **A119752 is
different**, as detailed under CLI-002. `launch.state`, line 799, stores
work and coverage separately; `swept_k`, line 885, returns `boundary*W`.
Only closing a full segment advances `boundary` at lines 1362–1364.

<a id="cli-001"></a>

## CLI-001: local admissibility is a theorem for all six families

**Priority:** mathematical correctness of the explanation and diagnostic.
**Disposition:** proposed correction, not implemented. **Evidence:**
proved. This proof was independently checked by two other reviewers.
There is **no claimed candidate-count or runtime reduction**.

The contrary statements are in
[clique_reference.py](../clique_reference.py), its “ADMISSIBILITY IS NOT A
THEOREM HERE” discussion and `admissible`; the
[project README](../README.md), “Admissibility is checked, not proved”; and
[launch.py](../launch.py), `_build_engine`, lines 690–702, which would report
an all-residues kill as a theorem that the sequence terminates.

Assume the stored prefix is a valid positive clique: every pair of
distinct terms has prime sum plus one. The proof does not assume an
unproved assertion about future prime values.

### Five families without the “a(n) itself prime” condition

Fix any prime q. The prefix cannot contain both a term congruent to 0 and
a term congruent to −1 modulo q. If it did, those terms would be distinct
and, by positivity, at least q and q−1. Their sum plus one would be a
multiple of q at least 2q, contradicting its primality.

Therefore at least one of these prefix residue classes is absent:

- If class −1 is absent, candidate class **0** makes every shift
  `x+a(i)+1` nonzero modulo q.
- If class 0 is absent, candidate class **−1** makes every shift nonzero
  modulo q.

For A119751 and A119752, the extra form `2*x+1` equals 1 or −1 modulo q
on these two candidate classes, and hence is nonzero too. This includes
q = 2. Thus every prime has an allowed class for A093483, A103828,
A037100, A119751 and A119752.

The lower bound of 2q is what removes the possible exception “the
divisible value is q itself.” No sieve-floor assumption is needed for this
prefix argument.

### A133761, whose terms are themselves prime

All terms are primes at least 5. For any prime `q >= 5`, the prefix
cannot contain both residue classes 1 and q−2. A prime congruent to 1 is
at least q+1, since 1 is not prime; a positive representative of q−2 is
at least q−2. These distinct terms would again have sum plus one a
multiple of q at least 2q.

If prefix class 1 is absent, candidate class **−2** survives every shift.
If prefix class q−2 is absent, candidate class **1** survives every
shift. Both candidate classes are nonzero modulo q, so the extra
requirement that x be prime adds no obstruction there.

For q = 3, no prefix term is divisible by 3 because all are primes at
least 5; candidate class −1 survives every shift and is nonzero. For
q = 2, all prefix terms are odd and candidate class 1 survives both the
shifts and the extra form. Thus this family is locally admissible too.

### Consequences, and what the proof does not permit

No valid prefix of any of these six families has a prime covering all
candidate residues. This rules out the particular modular termination
mechanism described in the documentation. It **does not prove that any
next term exists**, much less that a sequence is infinite: local
admissibility of a collection of linear forms is not a proof of their
simultaneous primality.

The surviving class exhibited by the proof is a **witness**, not the
complete allowed set. Restricting the search to that witness would discard
other allowed classes and could lose the least term. Existing exact
kill-set construction already removes every obstruction supplied by these
small-prime tests. The witness supplies no additional pruning.

A useful corollary is persistence of a forced class. In the first five
families, a single surviving class must be 0 or −1. A newly found term
in that class adds the opposite class as a killed shift residue, which
was already killed. For A133761 at q ≥ 5, a forced class must be 1 or
−2; adding its new shift likewise kills the other, already killed class.
The small-prime cases follow directly. This supports the existing monotone
forcing invariant; it does not enlarge the set of forced primes.

### Claude handoff

Correct the mathematical discussion and make a failed admissibility check
on these families an alarm to investigate the prefix, definition or
residue construction, rather than an automatic announcement of a last
term. Keep the exact check as a cheap invariant. Keep the oracle's direct
definition and residue walk independent of the witness construction.

Future validation should cover all six starts, the q = 2 and 3 cases,
small prefixes where a form can equal a sieve prime, and prefix examples
violating a theorem hypothesis. Check each witness against direct
divisibility and keep the full survivor set unchanged. No benchmark
fingerprint, coverage boundary, census population or numeric limit should
change as a consequence of this explanatory theorem.

<a id="cli-002"></a>

## CLI-002: current prefixes and censored coverage must precede a one-day forecast

**Priority:** high for interpreting current feasibility. **Disposition:**
proposed reconciliation, not implemented. **Evidence:** observed in
source/data and exact integer arithmetic. This is not a measured speedup.
The missing current-prefix model and benchmark shapes were already listed
as follow-up work; the A119752 coverage contradiction is a new observation.

`FOUND` is empty in [clique_reference.py](../clique_reference.py). The
launcher correctly restores its actual terms from each checkpoint through
`_register` before constructing the engine (`launch.py`, lines 668–706).
Standalone model and score execution, however, starts with the older
`KNOWN` prefixes unless the new terms are deliberately supplied.

[model_results.json](../model_results.json) explicitly marks every row
beyond each original opening as a projection using stand-ins.
`clique_model.forms_for`, `stand_in`, `log_singular` and `expected` show why
a newly known prefix can change both its singular series and the logarithm
denominators. Those old later rows are not current forecasts.
[score.py](../score.py), `SHAPES`, line 109, similarly freezes the original
opening indices 18, 19, 19, 15, 15 and 17, rather than the six current
filters. Their fingerprints remain valid historical workloads; a new
frontier calls for new shapes, not rewriting old answers.

### A119752 already excludes a substantial interval

[RESULTS.md](../RESULTS.md), “In progress,” lines 157–171, says no family
closed a segment after its last term. The saved A119752 checkpoint instead
has:

`k_start = 23912359356224311449`

`W = 614889782588491410, segment_periods = 128`

`j = 422, k = j*W = 259483488252343375020`.

The period containing the initial floor was 38, and
`422 - 38 = 3*128`. The checkpoint therefore records **three completed
segments**, proving its claimed empty interval

`[23912359356224311449, 259483488252343375020)`.

The current segment's `u = 5662` of 13392 launches is additional saved
work; it is not a contiguous extension of that interval. The next
candidate could still be anywhere in the unclosed segment. The checkpoint
hash was
`2b3847ddacc082662f1b280784fc0331a0db87737e8842a41e82d36b069462f5`.
This is an interpretation of the stored coverage claim and its writer,
not an independent rerun of the interval.

For a future forecast using the actual prefix, take
`L = max(a(n−1)+1, saved_k)` as the conservative lower search boundary.
The model's new interval probability is
`1 - exp(-E_actual_prefix(L, M))`, under its Poisson assumption.
For A119752, use the later boundary above. For the other five, use their
strict greedy floors. Do not convert a launch fraction into an empty
numeric subinterval or reuse a stand-in singular series.

The current launcher also derives `plan` and its opening predictions from
the predecessor term, not from an arbitrary later censored bound
(`clique_gpu.plan`, lines 574–591; `launch.run`, lines 1281–1285).
A future refreshed forecast should distinguish the original opening
distribution from the conditional remaining distribution. Whether changing
an already chosen plan after substantial coverage is worthwhile is
unmeasured and is a separate cursor migration.

### What can be said about one day without inventing a current median

The following rates are **previously measured here**, from
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 2, dated 2026-09-20,
lines 654–667. They are explicitly **kernel-only** measurements. Multiplying
them by one day is arithmetic, not a new sustained campaign measurement.
The segment clocks below use each saved W and segment width.

| Current filter | Recorded rate, a(n)-line/s | Nominal line in 24 hours | One complete segment at that rate |
|---|---:|---:|---:|
| A093483 n = 22 | `5.1e17` | `4.4064e22` | 3.98 h |
| A103828 n = 22 | `6.05e17` | `5.2272e22` | 3.86 h |
| A037100 n = 22 | `3.2e17` | `2.7648e22` | 6.34 h |
| A119752 n = 21 | `1.70e17` | `1.4688e22` | 7.72 min |
| A119751 n = 21 | No rate at this filter in that table | Not established | Not established |
| A133761 n = 21 | No rate at this filter in that table | Not established | Not established |

The `3.03e17` A119751 row was measured at **n = 20**, before the saved
promotion to n = 21, and cannot silently fill its missing row. The old
A133761 opening rate is at n = 17.

These line budgets are optimistic fixed-filter device scenarios. They do
not specify the probability of a find, the new filter's speed after a find,
or the time to build and validate an implementation. Confirming leastness
requires closing the containing segment; merely encountering a promising
candidate is insufficient. Saved partial launches can reduce remaining
device work without moving the conservative bound. A current-prefix
conditional model and a current end-to-end rate are needed to turn these
figures into a defensible one-day probability.

The historical validation mean E of 1.03 over the original 49 draws and
the successful first-opening comparisons are useful model checks, but
they do not turn later stand-ins into known prefixes. The repository also
warns of first-occurrence forecasts landing late in other hunts. No new
median or probability is asserted here.

### Claude handoff

Reconcile the 26 recorded terms with their evidence and make the actual
prefix available to standalone validation and model generation without
changing the original definition. Preserve provenance between published
knowns and campaign claims. Correct the A119752 status from the actual
checkpoint, then generate explicitly labeled actual-prefix,
coverage-conditioned forecasts in a later implementation task. Add
current-filter benchmark shapes while retaining the old fingerprints.
Populating `FOUND` alone does not change every fresh-campaign entry point:
`launch.open_n`, `c_front` and `Campaign._known_top` read `KNOWN`.
Choose and validate their intended behavior deliberately; restored
campaigns already register their saved `found` correctly.

If a plan changes, key it by family, prefix, filter, wheel, window and
depth, including the enumeration and launch decomposition. The existing
load path saves many of these fields but explicitly checks the stored
filter and W (`launch.py`, lines 646–657); equal W alone does not establish
equal meaning for u after a window or CRT-level change. This is a
prerequisite for future plan changes, not a claim that the present
unchanged configuration misreads its checkpoint. Preserve the old
contiguous bound; floor its physical candidate
coordinate onto the new period and clip overlap without skipping a gap.
Do not reinterpret old u under a different launch decomposition. Replay
or deliberately discard and redo partial work with its pending census
handled consistently. Future drills need A119752's three closed segments
plus a partial segment, a family still inside its first segment, and a
promotion whose new form uses a freshly registered term.

<a id="cli-003"></a>

## CLI-003: segment reuse is sound, but already priced too small

**Priority:** low at the recorded fronts. **Disposition:** deferred;
already priced and declined, not a new proposal. **Evidence:** proved
coverage implication; historical model-derived benefit; unmeasured
implementation.

[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 2 item 5,
lines 625–642, explicitly considers retaining survivors above the first
find and testing the one new condition. Its estimate is **0.1–0.7% of the
next term's clock**, not a multiple-fold gain. The earlier truncation
proposal at lines 369–374 addresses a different saving: completing only
the part of the current segment below a provisional find.

Let `[A,B)` be fully processed under a fixed old prefix, and let y be its
least verified full candidate. Every future candidate z > y must satisfy
all the old forms and the new form `z+y+1`. Consequently every candidate
that could be the next greedy term in `(y,B)` lies in the old raw survivor
set. Every old candidate with a proven composite old form remains
impossible, and every retained candidate can be checked against the new
form. In sorted order, the least surviving full candidate is the next
term; repeating the argument supports further promotions within the
buffer.

This proves that old data can be reused **after the new condition is
applied**. It does not justify blindly carrying the old boundary across
a promotion. The current restart in `launch.follow_frontier`, line 1068,
is conservative and correct. Its prose that the old data says “nothing”
about the next filter is stronger than necessary; the containment above
is the precise statement.

The existing completed `pending` list already contains every old full
candidate: `_drain` retains all runs at least `CENSUS_FLOOR`, and
`Campaign.run` sorts the completed list before breaking at the first find
and clearing the remainder (lines 1236–1260 and 1351–1361). It is therefore
unnecessary to add a massive raw-survivor cache merely to preserve future
discoveries. A candidate whose old run r is below n still fails the same
old form; a candidate with old run n needs the appended new form, followed
by normal independent discovery verification. Repeat this logic after
each accepted term. Proven compositeness of an old form remains a valid
exclusion even when the new filter chooses a different sieve depth.

This preserves discovery coverage, **not automatically the census of a
fresh new-filter sieve**. The new condition can remove old survivors,
and if q2 decreases, the new sieve can emit census-only candidates that
the old deeper sieve never retained. Even retaining the old raw survivors
cannot recover such candidates. Keep the census tied to the actual source
filter, reconcile it separately, or re-sweep for that purpose; do not claim
identical survivor populations merely because all possible discoveries
were preserved.

There is no new deterministic reduction in old candidate generation:
the completed old segment has already been paid for. Reuse can save
re-generating and re-sieving its upper remainder under the next filter.
It does not remove the current segment's confirmation cost, and all six
campaigns still need the current next term. The original small-benefit
assessment remains the evidence available here.

If a future frontier makes this worthwhile, a bounded implementation must
bind the buffer to the exact prefix, sieve depth, complete interval and
candidate fingerprint; apply each new condition before advancing its
coverage claim; verify every discovery with the untouched oracle; and
preserve or replay the buffer across interruption. Test against an
independent full re-sweep on published greedy terms, including two
promotions in one interval and no further hit. Census accounting must
distinguish old classifications from new classifications, and replay must
not count either twice. Refuse the optimization if completeness or
provenance of the buffer cannot be established.

## Other ideas examined and disposition

| Idea | Mathematical assessment |
|---|---|
| Use only the admissibility theorem's witness residues | Invalid for leastness: witnesses are a subset of the allowed classes. CLI-001 supplies no new exclusion. |
| Add more forcing or force prime powers | Existing exact kill sets already detect a unique class; q-squared forcing does not follow. A factor of one successful term is not a shared divisor theorem. |
| Treat diagonal families as subsequences of their non-diagonal siblings | Their greedy prefixes diverge, so later form sets differ. An extra condition does not make the resulting greedy sequence an indexwise subset after divergence. No valid cross-family leastness bound was established. |
| Intersect the six families' filters to share a sieve | An intersection would lose terms valid in only one family. A union with per-family membership could be correct, but admits more work and has no demonstrated favorable overlap or substantial benefit here. |
| Recover more terms by affine maps | The five proved derived maps are already implemented. They provide additional entry terms per discovery, not a new speedup of the primary searches. |
| Import the period-window representation from another project | Already present, including forced-class coordinates and the wide record. The earlier in-block window-coordinate proposal was implemented for wide records in round 2; it is not still an unbuilt gain. |
| Minimize wheel density or use a larger wheel indiscriminately | Ignores the segment required for confirmation, per-window costs and word bounds. The existing planner explicitly prices these; past alternatives and truncation were already measured or priced in the log. |
| Reuse the remainder after a find | Sound only with additional filtering and complete provenance; CLI-003 preserves the log's small-benefit conclusion. |
| Window-width, instruction and occupancy tuning | The log has known small opportunities and measurements, including a stale A119751 n = 20 case. Runtime profiling and hardware tuning are outside this mathematical review. These gains are not multiplied into a hypothetical new speedup. |

The audit found a useful structural theorem, a material coverage correction
and a precise explanation of which reuse is safe. It did not find a missed
search-space elimination or new representation that demonstrably moves
these current searches into a one-day regime.

## Handoff and execution record

All six primary families and all five derived entries were considered.
The mathematical and coverage findings were independently critiqued by
two peer reviewers before completion. The source snapshot includes all
five public Python roles, the model, historical optimization/benchmark
records, saved checkpoints and relevant discovery evidence.

Only this report and its [local index](README.md) were created. No engine,
model data, score, optimization log, evidence or checkpoint was modified.
No proposed runtime benefit was measured. Claude should recheck the
premises against the then-current files, record any implementation or
rejection under the stable CLI IDs in the existing optimization log, and
update the index with the actual outcome.
