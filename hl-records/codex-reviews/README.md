# Codex reviews — hl-records

These are Codex-authored static mathematical and algorithmic analyses for
Claude's later implementation work. Follow the repository's
[Codex review workflow](../../CODEX_REVIEWS.md). The implementation and
historical project records retain their Claude attribution.

**Static review completed 2026-11-11.** The review covers A331940, the
class-group prefilter and exact tabulation, host verification, campaign
coverage, model, scoring and optimization history. The owner's hunt was
running; no project code, tests, benchmarks, GPU queries or GPU work were
executed. Proposals are not validated implementations or measured gains.

| Document | Snapshot / purpose | State |
|---|---|---|
| [2026-11-11 static review](2026-11-11-static-review.md) | Engine v2; HEAD the last published commit `83e5724ed335e68d5bba5592f3222af585db397e` plus unpublished local commits, dirty tree with this project untracked; precise source hashes and dated checkpoint observation in the report | Complete static analysis and implementation handoff |

| ID / report | Finding | Disposition | Basis / implementation evidence |
|---|---|---|---|
| [HLC-001](2026-11-11-static-review.md#hlc-001-tighten-the-bound-with-local-euler-factors) | Tighten the universal E bound with known local characters and reject directly from a lower bound on h | **Implemented and validated** (engine v3) | Proved unconditional bound; split prime 3 multiplies the E bound by 2/3. Preserves mathematical outputs but can change the raw stream. Built as the T-rule with Q(n) over p <= 251 in both engines: 1.21x a window at k = 10^12 and 1.26x at 3*10^12 on top of HLC-003 (paired); 143 removed survivors on 13 windows all classified below the floor, census unchanged; gates P0, P5, P6, S9 -- [OPTIMIZATION_LOG.md round 2.3](../OPTIMIZATION_LOG.md#23-hlc-001-the-local-euler-factors-in-the-rule-shipped). |
| [HLC-002](2026-11-11-static-review.md#hlc-002-descend-to-the-fundamental-discriminant) | Use the complete conductor formula before class-group work | **Implemented and validated** (engine v3) | Exact decomposition and class-number identities; can preserve the old raw survivor stream. Built in the decision-preserving form (h(-d) bound against the count 3 L S(f), genus factor of d, characters of -n kept in Q); replaces bound (4). 1.08x a window at 10^12, 1.06x at 3*10^12, stream identical; P5 parity on 16 constructed conductors, S8 against the counted h(-d) -- [round 2.7](../OPTIMIZATION_LOG.md#27-hlc-002-the-prefilter-in-the-fundamental-discriminant-shipped). |
| [HLC-003](2026-11-11-static-review.md#hlc-003-enumerate-modular-roots-and-price-a-sparse-fallback) | Enumerate modular roots for exact confirmation; price sparse and mod-3 hybrid production fallbacks | **Implemented and validated** (sparse production route, engine v3); confirmation enumerator **Deferred** | Proved canonical-form bijection and O(sqrt(d) log d) root-output bound for fundamental d. Built as the production count of every flagged k, with the roots replaced by their multiplicative number for a <= isqrt(4k - 1)/2 and found by Tonelli-Shanks/Hensel/CRT in the band: it replaces the flagged three-squares walk outright (no mod-3 hybrid needed), 3.79x a window at 10^12 and 5.08x at 3*10^12 alone; equal to the three-squares count on 16,592 discriminants to the ceiling (gate P7) -- [round 2.2](../OPTIMIZATION_LOG.md#22-hlc-003-the-sparse-exact-count-shipped). The leg-3 enumerator is priced and deferred in [round 2.11](../OPTIMIZATION_LOG.md#211-deferred-with-prices). |
| [HLC-004](2026-11-11-static-review.md#hlc-004-finish-the-squared-base-order-experiment) | Complete the previously proposed squared-base BSGS experiment | **Declined** | Known unfinished idea from [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 1.8. Measured in two decision-identical forms: steps by the squared prime form 0.900x at 10^12 (the p \| a fallback diverges: half the forms when the base prime is 3), lookups at even exponents only 1.003x at 10^12, 0.960x at 10^10 -- [round 2.5](../OPTIMIZATION_LOG.md#25-hlc-004-the-order-of-the-base-forms-square-declined-both-forms). |
| [HLC-005](2026-11-11-static-review.md#hlc-005-price-selective-use-of-published-class-number-data) | Price selective access to published fundamental class numbers | **Deferred** | LMFDB access and format located; exact reconstruction proved. Storage, I/O, provenance and reuse must justify adoption; no dataset files downloaded. Re-priced against engine v3, which sweeps everything below 2^38 in about 2.5 hours -- [round 2.11](../OPTIMIZATION_LOG.md#211-deferred-with-prices). |
| [HLC-006](2026-11-11-static-review.md#hlc-006-change-the-validation-contract-deliberately) | Update health checks, benchmark expectations and coverage migration alongside a stronger filter | **Implemented and validated** (engine v3) | Source dependencies identified; prerequisite for HLC-001 and internal fingerprint changes. Rule carried by both engines and the health check; cursor key `rule=p251-local` accepting v1/v2 cursors, with the old raw survivor count kept apart (`survivors_by_rule`) and a migration drill in the selftest; fingerprints re-frozen after the battery was green -- [round 2.10](../OPTIMIZATION_LOG.md#210-hlc-006-what-the-contract-change-needed), [BENCHMARKS.md](../BENCHMARKS.md). |

**Implementation 2026-11-11 (Claude):** engine v3, measured at the
heights the campaign's clock is spent (10^12 and 3*10^12, from the owner's
cursor at k = 1.26*10^10): 5.41x and 7.45x a window against engine v2,
paired. Nothing committed at the time of writing.

Before implementation, recheck the source snapshot and current state.
Update each disposition with links to dated correctness and performance
evidence in [OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) and
[BENCHMARKS.md](../BENCHMARKS.md). Keep the dated report as the historical
analysis; record rejected attempts as well as accepted ones. The saved
campaign state in the report is an observation, not a fresh verification
or a substitute for RESULTS and discovery evidence.
