# Product cliques: static mathematical review

**Author:** Codex (OpenAI). **Date:** 2026-10-20.
**Scope:** A034881 and A219761; all five public Python roles, mathematical
model, evidence, checkpoints, benchmark and optimization records.
The review team examined this project only, consulting the later
plus-two engine as a specific representation donor.

This follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md). Codex is always
static in this role: no GPU use, project imports or execution, models,
oracles, tests, benchmarks, searches or primality experiments. Only
documentation was edited. Numerical calculations below are arithmetic on
recorded data and explicit finite formulas. Historical certificates and
measurements were read, not independently rerun.

**Conclusion.** No supported new optimization turns the open terms into
one-day median searches. Current-filter rates are unmeasured; using the
previous campaign legs as surrogates, remaining median distances are
about **11 and 32 days**. Segments already close in roughly 20–32 minutes
at those surrogate rates, so confirmation latency is not the main barrier.

There are modest concrete opportunities: reuse repeated words inside
periodic sieve windows, revisit wide-round storage when considering a
larger wheel, and refilter a completed segment's full-run candidates after
a find. The report also derives a corrected tail representation for the
quadratic singular series, proves global nonforcing, and identifies the
need to halt greedy promotion on unresolved certificates.

## Definitions and actual campaign state

HEAD was `f8fdb200c56a54aa5e207c146882f7d2d7b87224`, with documentation
edits in the worktree. Source/data hashes appear below. Links name
symbols and snapshot line numbers.

Both sequences start at a(1)=1 and are strictly increasing greedy
cliques. For A034881, a(n) is the least integer x>a(n−1) such that
\(a_i x+1\) is prime for every i<n. A219761 additionally requires
\(x^2+1\) prime. There is no exact-run stopper and x itself is not
required to be prime. The entry's term is **a(n)**; x is merely code
notation. See [`forms` and `maxkills`](../product_reference.py#L227).

| Family | Current open index | Required forms | Maximum number of roots at one prime |
|---|---:|---|---:|
| A034881 | 20 | 19 linear product forms | 19 |
| A219761 | 19 | 18 linear forms and x²+1 | 20 |

The sequences diverge at a(4): A034881 takes 18, while 18²+1=325
excludes it from A219761. After that they have different prefixes.
One is not obtained by filtering the other's later terms, and no derived
entry is established here.

### Recorded discoveries and proof evidence

| Family | Recorded new terms | Latest term |
|---|---|---:|
| A034881 | a(16)–a(19), four terms | 2,412,240,527,764,607,793,810 |
| A219761 | a(12)–a(18), seven terms | 8,981,486,409,894,740,569,620 |

The [A034881 ledger](../evidence/a034881_discoveries.json) and
[A219761 ledger](../evidence/a219761_discoveries.json) link the evidence.
Latest files are
[A034881 a(19)](../evidence/A034881_a19_2412240527764607793810.json) and
[A219761 a(18)](../evidence/A219761_a18_8981486409894740569620.json).
[RESULTS](../RESULTS.md#L15) records an independent October 1 recheck
of all 11 files and 171 certificates: 79 BLS75 Theorem 1 and
92 deterministic MR. Every record has complete verified certificates
and no unproved required value. The largest recorded self-square value
has 44 digits; the largest ordinary product has 42.

These are repository evidence and verification claims, not certificates
rerun by Codex. The user's submissions may postdate the old October 1
OEIS export; no statement here describes current online submission
status. `FOUND` is still [empty](../product_reference.py#L154), and the
campaign registers checkpoint terms before constructing the new forms.
A fresh source-only opening and the historical model file therefore
still describe earlier frontiers.

### Saved coverage and partial work

Both checkpoints use unit 6, sieve q2=65536 and the same wheel:
{5,7,11,13,17,19,23}, {29,31,37}, {41,47,53}, omitting 43.
Its physical period is
\[
 W=757,887,406,446,280,110.
\]
Both selected windows have 160 configured periods but **145 live
periods**, on the narrow record. A full segment spans
\(S=145W=109,893,673,934,710,615,950\).

| Family | Saved timestamp | j; u / launches | Saved k | True new-filter floor k_start |
|---|---|---|---:|---:|
| A034881 n20 | 2026-09-29 22:52:33 | 3182; 4030 / 53760 | 2,411,597,727,312,063,310,020 | 2,412,240,527,764,607,793,811 |
| A219761 n19 | 2026-10-01 17:59:50 | 11850; 0 / 59400 | 8,980,965,766,388,419,303,500 | 8,981,486,409,894,740,569,621 |

Sources: [A034881 checkpoint](../campaign_checkpoint_a034881.json) and
[A219761 checkpoint](../campaign_checkpoint_a219761.json).
Both have `cover_x=0`, and their saved k is the containing period's
start below the greedy floor. Thus neither claims new contiguous
coverage beyond its last term. The partial u cursor is a set of
interleaved residue launches, not a numerical interval.

A034881 has 1,773 pending records with maximum run 13; A219761 has none.
No cached record is a full current-filter hit. The saved timestamps are
snapshots, not a claim about a currently observed running process.

For run counters, a full run is n in either family: A219761 first checks
the self-square, then both count one plus the number of successful prefix
products, capped at n. Shorter runs are census or near events. This is
not the exact-index classification problem of primorial-runs.

## Rates, models and one-day limits

The current filters have **no measured price and no frozen benchmark
shape**, as [BENCHMARKS](../BENCHMARKS.md) and
[RESULTS](../RESULTS.md#L179) explicitly state. The two relevant preceding
campaign rates are:

| Historical filter | Campaign rate | Stand-in comparison |
|---|---:|---|
| A034881 n19 | 9.0e16 a(n)-line/s | 8.1e16 on an earlier stand-in |
| A219761 n18 | 5.8e16 a(n)-line/s | 8.0e16 on an earlier stand-in |

Those campaign figures divide the term-to-term distance by wall time,
including verification and oversweep; they are not pure kernel rates.
A219761's 0.72 ratio remains unexplained. Its real wheel differed from
the stand-in wheel, so this is neither proof of a software regression
nor evidence that the current filter will reproduce that rate.

The October 1 scratch model was recomputed on the **real prefixes** and
is summarized in RESULTS. `model_results.json` remains the earlier
opening/projection record; later-index stand-ins are not actual forms.

| Family | Real-prefix median location | P90 | Remaining travel at previous-filter rate | Recorded model probability in 1 / 7 / 30 days |
|---|---:|---:|---:|---|
| A034881 a(20) | 8.8e22 | 4.3e23 | 11.01 days | 10% / 39% / 77% |
| A219761 a(19) | 1.7e23 | 7.8e23 | 32.13 days | 3% / 18% / 48% |

The day probabilities are model/throughput scenarios, not measured
probabilities or guaranteed finds. Earlier draws suggested early terms,
but the new 11 draws have mean E=0.87. Calling all future medians
“conservative” is not a mathematical guarantee. This review did not
reevaluate a probability or execute the model.

At those surrogate rates, the common segment takes **20.35 minutes**
or **31.58 minutes**. Ignoring startup, proofs, interruptions and promotion,
24 hours fits 70 full A034881 segments without partial credit, reaching
1.01042e22, or 45 A219761 segments, reaching 1.39262e22. A034881 could
close one more only with sufficient actual partial-time credit; its
7.50% launch fraction is not itself a clock measurement.

Even continuous travel to the rounded medians in one day requires
approximately **11.01× and 32.13×** the preceding-filter rates.
The stand-in current rates of 1e17 would still imply approximately
9.9 and 18.6 days of remaining median travel. No proposal below has
evidence of gains on that scale.

## PRC-001: reuse periodic words and revisit wide-round storage

**Disposition: Proposed.** Product-cliques already has the main
multi-period window sieve. The applicable later improvement is narrower:
avoid loading bits already determined by a short pattern period.

For a fixed filter, unit coordinate and post-wheel prime group of modulus Q,
the [existing pattern](../product_gpu.py#L1464) is Q-periodic. This is
true for any fixed killed set, including the roots of x²+1. If
\(P(t+Q)=P(t)\), then bit offsets 32i through 32i+31 can be taken from
offsets 32i−Q through 32i−Q+31 of earlier words once those bits have
already been formed. For Q>32 the dependencies precede word i.
The form degrees play no role after the exact killed set is constructed.

The later plus-two engine implements this in
[`window_plan`](../../plus-two-cliques/plus2_gpu.py#L1736).
For a 160-period window and suitable Q≤96, two overlapping-pair loads
replace three, with later words reconstructed by constant funnel shifts.
The [donor measurement](../../plus-two-cliques/OPTIMIZATION_LOG.md#L620)
was **1.019×**, with eight affected window primes at its own filter.
The current product wheel omits 43 and leaves later small primes outside
the wheel, but its actual selected groups must be inspected in future
implementation before claiming how many loads disappear.

This is exact repeated-work elimination. It has **no measured gain
here** and does not carry the donor's eight-prime count automatically.
Transfer pattern consumption while preserving the original oracle,
CPU Tonelli–Shanks root construction, exact quadratic root capacity,
and complete survivor stream. Test all pattern start positions, partial
last words, group products and ordinary nonperiodic fallbacks later.

### A larger-wheel prerequisite, not a current narrow-record win

Product's wide rounds retain
[`ROUND_WINDOW` rows](../product_gpu.py#L2545). The later donor instead
uses
\[
 \mathrm{offp}+j(W'\bmod M)
 \equiv \mathrm{offp}+jW'\pmod M.
\]
With offp<2^63, j<256 and M<2^31, the reduced numerator is below 2^64.
This allows packed Barrett rounds without the large per-residue
window-coordinate rows. The [donor](../../plus-two-cliques/OPTIMIZATION_LOG.md#L634)
measured 1.052× with its queue choice and reduced device storage from
4.32 to 1.40 GiB. Neither result is a product-cliques measurement.

Both current product plans are narrow, so this does not directly
accelerate them. It may reopen the **already priced** full-53 proposal:
[OPTIMIZATION_LOG](../OPTIMIZATION_LOG.md#L396) measured a 1.23× gain
on an A034881 n20 stand-in but rejected a global cap increase because
it worsened another stand-in plan and wide-row storage was expensive.
The actual current wheel already includes 53 and omits 43. Its missing
prime, row counts and clock tradeoff must be repriced from its real
prefix; the old 1.23× cannot be reused as the current gain.

There is a concrete actual-prefix full-53 construction. Use first level
{5,7,11,13,17,19,23,37}, second {29,31,41}, and third {43,47,53}.
Then W1=1,375,739,365, W2=3,948,078,067 and
W′=5,431,526,412,865,007,455. The exact row counts are:

| Actual filter | R1 | R2 | R3 | Additional-prime candidate reduction |
|---|---:|---:|---:|---:|
| A034881 n20 | 3,706,560 | 6,480 | 33,600 | 43/30 = 1.43333 |
| A219761 n19 | 4,371,840 | 6,750 | 38,016 | 43/32 = 1.34375 |

The moduli, uint16 secondary counts and existing residue capacity fit;
the first rows exceed the current 2^21 planning cap but fit a donor-style
exception-only 2^24 cap. These are arithmetic feasibility facts, not a
measured better plan. Every PB≥32 requires wide records: the conservative
64-bit narrow limit permits only two live periods. The physical period
grows 43-fold to 32,589,158,477,190,044,730. At the previous campaign
rates a PB32 segment would take about 3.22/4.99 hours, and PB160 about
16.09/24.97 hours. Neither the count factors nor the donor's measured
ratios may be treated as an end-to-end rate gain.

Any implementation must price the larger tables and confirmation span,
retain the donor's tchunk grid cap of 65535·tpb, validate the actual
prime union and explicit-list level interpretation, and preserve
overflow fallbacks. A smaller PB is an essential comparison. This is a
bounded way to revisit the earlier representation objection, not an
11× or 32× improvement.

Do not transplant all newer flags as a package or multiply their donor
ratios. Preserve the current narrow fallback. Add immutable current
n20/n19 workloads on fixed absolute intervals alongside all original
fingerprints. A changed mathematical interval legitimately needs a
separate fingerprint; a changed representation on the same interval
must reproduce the original complete stream.

## PRC-002: refilter a complete segment's full-run suffix

**Disposition: Deferred.** This is a newly identified local reuse
opportunity, distinct from the already priced find-triggered segment
truncation. It saves work only after a discovery.

Let F_n be the old form set and let a_n be its certified least hit.
For both families
\[
 F_{n+1}=F_n\cup\{a_nx+1\};
\]
the self-square, when present, remains unchanged. Therefore every valid
next candidate in the already completed segment is among the old
full-run candidates. A shorter old run has a proved composite required
value and can never become valid by adding a condition.

The [current loop](../launch.py#L1399) sorts all pending records, stops
at the first find and drops its suffix. The
[`follow_frontier` comment](../launch.py#L1118) says nothing previously
classified is useful. The form inclusion proves otherwise, provided
the surviving candidates are actually refiltered.

A correct discovery-only procedure is:

1. Finish the old segment and retain the sorted old full-run candidates
   above its least hit; no huge pre-MR survivor cache is needed.
2. Certify that least hit before admitting it to the prefix.
3. Test the appended product on the retained candidates in order.
   Independently verify and certify the first new full hit, if any.
4. Repeat after each further certified greedy term. When the retained
   list is exhausted, the old segment's numerical endpoint is valid
   empty coverage for the new filter.

Induction proves this: every future true candidate satisfied every old
required form, so it was retained; adding forms can only remove members.
MR failures are proofs of compositeness, while false-positive full runs
merely keep extra candidates for later verification. Prime-equality
exceptions remain covered by the existing small-value prefix and floor.

The cache must include its source prefix/filter, completed interval,
classification provenance and unresolved proof state. Commit prefix,
cache and carried boundary atomically, or replay safely after a crash.
An interleaved incomplete segment cannot support this numerical claim.

This preserves **discovery coverage**, not automatically a new filter's
censored census. Old shorter runs do not revive, but a different
wheel/depth can admit different census-only survivors. Separate
source-filter census provenance or reconcile it explicitly; avoid
counting retained records twice.

Current segments are only 1.09894e20 wide. Relative to the current
remaining median distance, that is at most approximately **0.128%**
and **0.068%**. These percentages compare line, not runtime, and a
future filter's rate can differ. There is no saving before the next
find, no full hit in the saved pending lists, and no supported one-day
breakthrough. The implementation complexity makes deferral reasonable.

## PRC-003: separate the quadratic character from the model tail

**Disposition: Proposed.** The model is already using the correct
finite killed sets. The improvement is a mathematically controlled
tail representation, not a corrected measured search density.

Let the prefix coefficients be \(a_1,\ldots,a_l\). For A034881, l=n−1
and m=l forms. Away from primes dividing
\[
 \Delta_{\rm lin}=\left(\prod_i a_i\right)
                  \left(\prod_{i<j}(a_j-a_i)\right),
\]
all m linear roots are present and distinct. For q>Q>m, their deficiency
\(m-w_q\leq v_q(\Delta_{\rm lin})\). The generic negative tail and
finite-collision correction give
\[
 -\frac{m^2}{2(Q-m)}
 \leq\log T\leq
 \frac{\log\Delta_{\rm lin}}{(Q-m)\log Q}.
\]
At the actual n20 prefix, m=19 and Q=200000,
\(\log\Delta_{\rm lin}\leq5302.98405\), using
\(\sum_i\log a_i+\sum_j(j-1)\log a_j\).
Thus the raw omitted log product is conservatively between
**−0.000903 and +0.002173**.

### The self-square creates a first-order character term

For A219761, l=n−1 and m=l+1. For odd primes outside the exceptional
set, x²+1 has \(1+\chi_{-4}(q)\) roots, so
\[
 w_q=m+\chi_{-4}(q),\qquad
 \log A_q=-\frac{\chi_{-4}(q)}q+O(m^2/q^2),
 \quad
 A_q=\frac{1-w_q/q}{(1-1/q)^m}.
\]
The raw truncated product therefore does **not** have the same
generic O(m²/Q) absolute tail as an all-linear tuple.
The existing [`log_singular`](../product_model.py#L150) supplies
no remainder bound; this observation does not prove its numerical
forecast is badly wrong.

Extract the known character:
\[
 C_q=\frac{A_q}{1-\chi_{-4}(q)/q},\qquad
 S=\frac4\pi\prod_q C_q,
 \quad \chi_{-4}(2)=0.
\]
Here \(L(1,\chi_{-4})=\pi/4\), from the alternating odd reciprocal
series, and the character Euler product supplies the reciprocal factor.
The [NIST DLMF Euler-product reference](https://dlmf.nist.gov/25.15)
states the Dirichlet L-function framework. The displayed cancellation
is derived here: the linear 1/q terms of log C_q vanish.

All exceptional missing/colliding roots are covered by
\[
 \Delta=\Delta_{\rm lin}\prod_i(a_i^2+1).
\]
A linear root meets a quadratic root only when q divides \(a_i^2+1\).
Root losses and coincident pairs are bounded by \(v_q(\Delta)\).
For Q>2(m+1), using
\(|\log(1-z)+z|\leq z^2\) for |z|≤1/2 and replacing the prime tail
by the integer tail gives the conservative corrected-remainder bound
\[
 -\frac{(m+1)(m+2)}Q
 \leq\log T_C\leq
 \frac{(m+1)(m+2)}Q+
 \frac{\log\Delta}{(Q-m-1)\log Q}.
\]
At current n19, m=19,
\(\log\Delta\leq5805.34016\), so the **accelerated remainder's**
omitted log product lies in **[−0.002100,+0.004479]**.
This is not a bound on the old raw character tail.

Finite q, including q=2 and every exceptional coefficient/resultant
prime, must use the actual local factor. Never replace them by the
generic root count. A future implementation should compute the extracted
product independently, preserve the original forecast artifact, and
state current-prefix forecasts with truncation uncertainty. No new
quantile, current intensity or explanation of historical bias is claimed.
The BH/Poisson assumptions and first-occurrence scatter remain separate.

## PRC-004: proof-gated promotion and optional partial-factor certificates

**Disposition: Proposed** for fail-closed settlement; the optional
partial-factor optimization below is deferred within this finding.

The source obtains `certs, unproved` at
[`record_discovery`](../launch.py#L1046), but calls `_settle` at line
1087 even when some required certificates are missing. Lines 1106–1111
explicitly let the find stand. Here an incorrect accepted term would
change every later form list. Unresolved required proof must stop before
prefix registration, proved evidence, promotion or coverage advancement.

All 11 historical evidence files have complete required certificates.
This is a source-contract weakness, not an identified wrong term.
The exact-run CENSUS problem from primorial-runs does **not** transfer:
here run<n includes a composite required value, and a true full hit
cannot be shortened by a one-sided MR rejection. False positives reach
the full-hit verification path. There is also no meaningful n+1
condition until a(n) exists, so no imported exact-run cap rule is needed.

[`certify_run`](../launch.py#L466) already shares one factorization of x
across all values \(a_ix+1\) and \(x^2+1\), using memoized prefix factors.
This structured N−1 route is valuable and already implemented. Proofs
can recurse beyond the deterministic MR bound; the configured term
ceiling is 1e40, not a 64-bit absolute candidate limit.

An optional mathematical refinement is to stop factorization early
once a fully proved known part \(F\mid x\) is sufficient. A conservative
common threshold is \(F^2>x+1\). For a linear value \(N=a_ix+1\),
the known part \(a_iF\) then exceeds sqrt(N), assuming the prefix
factorization is fully proved; for \(N=x^2+1\), the known part \(F^2\)
exceeds sqrt(N). The existing
[`certificate.prove`](../../huntlib/certificate.py#L519) accepts partial
factor information and [_prove_minus](../../huntlib/certificate.py#L462)
supports the sufficiently large factored part.

Use full valuations of every admitted prime, remove shared primes from
the residual cofactor, preserve coprimality/even-part requirements,
and verify the resulting certificates independently. A large claimed
factor must itself be proved. This could avoid a hard final cofactor,
but no material campaign cost is attributed to it by current evidence.
It is not a day-scale speedup and does not excuse incomplete proofs.

For representation or planner adoption, the current
[load checks](../launch.py#L695) assert stored n and W, despite broader
comments about stored units. They do not prove that a saved u means the
same work after PB, q2, launch decomposition or residue ordering changes.
Use a full enumeration fingerprint, retain the committed absolute
floor, and replay uncommitted work with pending/survivor/census
accounting reconciled. Do not reset u alone while retaining duplicate
partial pending records. A changed q2 also changes censored census
semantics even when mathematical empty intervals remain reusable.

The root-list capacity is already based on degrees:
NRES_MAX=32 allows filters through n33 for A034881 and n31 for A219761.
Current n20/n19 are safe. The squarefree unit guard is already present;
do not report the older repeated-factor unit defect here.

## PRC-005: prove that no further prime is forced

**Disposition: Proposed** as a documentation/proof improvement only.
Residue zero already proves local admissibility: every required
polynomial is 1 there. The source's
[involution discussion and finite gate](../product_reference.py#L515)
can be strengthened to a proof for every valid future prefix.

For any prime q≥7 take
\[
 r=q-2,\qquad s=(q+1)/2.
\]
They are distinct nonzero residues and rs≡−1 mod q. If the prefix
contained representatives in both classes, their product plus one
would be divisible by q and at least q(q−1)/2>q, contradicting
primality. Thus at least one coefficient class is absent.
The involution \(a\mapsto-a^{-1}\) exchanges r and s, so at least
one of those candidate classes survives every linear condition.

Neither candidate class is a root of x²+1: r²+1≡5 and
s²+1≡5/4 modulo q. Therefore it also survives A219761's self-square.
Together with zero there are always at least two allowed classes.
The strict product lower bound explicitly removes the prime-equality
exception that complicates an unqualified orbit-count argument.

For q=5, candidate 1 survives. A coefficient b≡4 would make b+1
prime and divisible by 5 because the prefix contains 1, forcing b=4.
But after the prefix contains 2, 2·4+1=9 forbids that term; earlier
prefixes do not contain 4 either. Also 1²+1≡2 mod 5.
Hence no q≥5 forces a single residue class.

Only the existing 2,3 restrictions remain, yielding x≡0 mod 6
from index 3 outside the independently covered small exceptions.
This proof does not justify restricting the hunt to one witness class;
all allowed classes remain eligible for the least term.
Ordinary linear-tuple infinitude is conditional on Dickson's conjecture;
the self-square case requires the corresponding prime-polynomial
conjecture such as Schinzel H/Bateman–Horn. Local admissibility is not
an unconditional infinitude theorem.

## Implementation priorities and limits

The current pair-load window, register extraction and packed narrow
rounds already produced the recorded 1.27–1.46× improvements. Their
microparameter sweeps, narrow window-coordinate loss, quad-table price,
and find-triggered truncation are [prior work](../OPTIMIZATION_LOG.md).
PRC-001 identifies later mathematical representations, not a request
to repeat those sweeps during this static review.

The immediate future evidence needs are already recorded: normalize the
11 discoveries in the reference with provenance, retain all historical
fingerprints, add actual current-prefix n20/n19 shapes, and replace
stand-in/current-rate assumptions with later authorized measurements.
For any accepted optimization, preserve the independent definition
oracle and CPU arithmetic, complete absolute-interval parity, prefix
validation and proof gating. For PRC-002 specifically, inject successive
finds in one completed interval and crashes before/after cache commits,
and distinguish discovery coverage from census provenance.

There is no known affine equivalence between the two diverged greedy
prefixes. Their similar formulas do not permit merging intersected
conditions without losing eligible terms. On the current common wheel,
the two survivor densities are 0.0000354943618632443 and
0.0000462572470024080, with intersection 0.000000255617832348467.
An exact coherent OR would reduce aggregate generated candidates by only
1.00314× versus separate enumeration, before branch overhead. This is a
finite CRT count comparison, not a runtime measurement or a reason to
build a joint engine. No extra local forcing or
large factorization exclusion was found. The appropriate outcome is
modest transferable work reduction and stronger mathematical/proof
documentation, with **no supported one-day next-term promise**.
Nothing in this report authorizes project execution or a campaign start.

## Snapshot hashes

SHA256 values pin files read on 2026-10-20. Project README navigation was
edited separately and is excluded from this source/data snapshot.

| File | SHA256 |
|---|---|
| `product_reference.py` | `a76cce6f58e514db51adc21cd673321725cc84ec9285731ed8be9ede11c93545` |
| `product_search.py` | `cfea7438d4581cb8500da7d75ce0f00fd21f51bcb41af3d922d217474e1920ef` |
| `product_gpu.py` | `58a59da9bd83d87d4be09ca0689dc8a98c55b21b30ccba3aa2ea153c48612a4e` |
| `launch.py` | `6c2f301c2a309a75850a446e8ffed9ed5fdd3b91fd31b2d79175bc6f1554ba9b` |
| `score.py` | `098f557eecea63cab48d11e9648a4cad3335c4a8508d6b4b48eb4f707b7285d0` |
| `product_model.py` | `af6ad7fd9f98f9ee77e6f867cc33165bdaa1015bf25d3d560be93ea375aaede0` |
| `model_results.json` | `26c712071f9d56ef7ca5878b7d37a4a1b2ff640750d79a4b2cc9156d8f11f2cc` |
| `campaign_checkpoint_a034881.json` | `5fcd23e513cc07bd1bc4e65b2b1fb4775747a29bd7a2e89ec5def9c46b26ef77` |
| `campaign_checkpoint_a219761.json` | `d599ad5a773a8705771fa2a5bd2d8b1eece6c446e7295e01fd4472d3467adb43` |
| `evidence/a034881_discoveries.json` | `35345fb5f60083fa2d7e9a2e2a4d288cb3ab38f17ef31131723da22ae7e115c4` |
| `evidence/a219761_discoveries.json` | `7e122c9cb04a18f6e051d3599311467844f9e2b873014038c3d8ec0f5f329a19` |
| `evidence/A034881_a19_2412240527764607793810.json` | `9f3b501190d99c696ce659e7d91b2511d25413696d96c8611ae9f2db3a857e47` |
| `evidence/A219761_a18_8981486409894740569620.json` | `2400a3b6dce80c21c709e0d0c4d581ec163a7d60b6b0c3b4c0b8c82cffb4d037` |
| `OPTIMIZATION_LOG.md` | `9b6221aa42d5812e7637668a6648294f1042c9e913fb32f0b06be83fb42240b3` |
| `BENCHMARKS.md` | `5b0a7c4938fd2eca9f22faef5fc1a60472f0eada135d15349f44996d397d1e9f` |
| `RESULTS.md` | `1b49ebb03377388cff8f44356e4b7695b661cd9ec85f9f42a80980a82365fbfd` |
| `../huntlib/certificate.py` | `4bd1d6d0e2c56d7aef7cbce17cf45faa514cbcb1c12f7fce790ee5c5a172f813` |
| `../plus-two-cliques/plus2_gpu.py` | `82d0fdd9995cdf6bd1eeb4385ef281e361446a92ba31d57dd67c0621c593ce10` |
| `../plus-two-cliques/OPTIMIZATION_LOG.md` | `744dfeefb96d5b764f1e7c1e8f84e2135f7308a23b8b0a6a6fa194ce75bcb036` |
