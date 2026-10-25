# Cyclotomic-ladders: additional optimizations beyond the wheel

> **Authorship:** Codex (OpenAI), 2026-10-24. Static response to the
> owner's request for significant additional optimizations beyond the
> wheel exchanges and bounded-interval CRT proposal. This report contains
> future experiments and their mathematical requirements, not measured
> speedups. No project code, checkpoints, evidence, or machine settings
> were changed; no project code or GPU work was executed.

## Assessment and priority

Two additional experiments deserve attention:

1. **CYL-013: select the later sieve primes by rejection benefit and
   actual cost, rather than testing every prime below one cutoff.**
   Some strong primes above 8192 beat much weaker primes included below
   it. The previous depth sweeps did not test a sparse prime selection.
2. **CYL-014: move the first one or two cheap Fermat tests between sieve
   stages.** Keep every original test, but let an earlier primality
   rejection spare later sieve work when the measured cost balance favors
   that order. The previous depth sweeps did not test this ordering either.

Neither experiment currently has a measured runtime gain. The first is
the stronger new algorithmic lead. The second has an exact equivalence
proof and a clear, falsifiable cost criterion. They are distinct from
[CYL-011 and CYL-012](2026-10-24-long-index-followup.md): the wheel and its
numerical completion interval can remain unchanged in the initial tests.

The remaining analysis rules out several attractive-sounding large
improvements: shared ancestor catalogs, simply making primality arithmetic
faster, and transferring another project's live-word compaction ratio.
Parallel execution across independent GPUs is a separate way to obtain
severalfold wall-clock reductions, if devices are available; it requires
additional compute and a coverage coordinator, not less mathematical work.

## Evidence and snapshot

The reviewed implementation is still engine v2 from Claude's round 1.
Repository HEAD is `35f48897eac28a5ec0ac4f60c3ce2e3a92d8708c`; the project
source remains outside that commit. All nine source/data/log hashes in
the [previous follow-up's snapshot](2026-10-24-long-index-followup.md#source-hashes)
were reread and are unchanged. In particular:

| File | SHA256 |
|---|---|
| cyclotomic_gpu.py | `72B777C23E0F0D3B84837912793AF53D291DFD7D4AEEBAA74A98A3A8CD6F1DAB` |
| launch.py | `645940E02A2790C305398B21ED20D7B346EF34C483A789332D02F6BFD918E7DA` |
| OPTIMIZATION_LOG.md | `5707F6E204B155521FE3CA62E4D139E3BF3718BA9758E9048FD36F31E7051827` |

The n = 60 checkpoint observed at 00:47:56 local time had completed one
segment and reached u = 6431 in the next, with 2426.076 seconds elapsed.
Its cumulative equivalent-work rate remained close to 5.5e20 x/s. This
is a historical saved-state observation, not a live display, and offers
no new evidence of a large checkpoint/host bottleneck.

The static scope follows [CODEX_REVIEWS.md](../../CODEX_REVIEWS.md).
Arithmetic on explicit small constants, source hashes, and stored rates
was performed; no project engines, models, primality experiments, tests,
benchmarks, profilers, CUDA compilation, or GPU queries were run.

## CYL-013 — a sparse, cost-aware sieve-prime frontier

**Classification:** new mathematical scheduling and representation
proposal; unimplemented and unmeasured. This concerns primes used after
candidate generation, not the wheel-prime changes in CYL-011.

### What the current code does

[cyclotomic_gpu.py](../cyclotomic_gpu.py), `GpuEngine.__init__` at
3351–3374, builds the complement of the wheel from every eligible prime
q <= q2, then sorts that fixed set by rejection fraction. `PRP_Q2` is
8192. Sorting already puts strong primes first, but cannot select a
better prime above the cutoff or skip a weak prime below it.

Round 1's `PRP_Q2` sweep, recorded in
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md) at 309–317, changed entire
prime prefixes. It tried smaller and larger cutoffs at A070737 n = 13
and A072942 n = 90, with 8192 retained. This is useful evidence against
a naive deeper or shallower sieve; it does not decide whether a
noncontiguous set of primes is better at the same filtering cost.

### Exact mathematical benefit

For A072942, prime q rejects the roots of x^n = 1 modulo q. Thus

    g_n(q) = gcd(n, q-1),
    p_n(q) = g_n(q)/q,
    s_n(q) = 1-p_n(q).

For q not dividing the forced unit U_n and absent from the already
conditioned wheel/prime set, the forced-unit transformation and other
distinct prime tests preserve this exact rejection fraction over a
complete joint CRT period. A prime dividing U_n rejects none of the
forced-class candidates, which are all zero modulo that prime; it must
not be assigned this conditional fraction. These period averages are
not promises about one finite launch.

The rejection fraction has spikes at large primes whose q-1 shares many
factors with n. Examples excluded by the present 8192 cutoff:

| Index | Prime q | Forbidden residues | Rejection fraction | Beats any two-root prime q' above |
|---|---:|---:|---:|---:|
| 60 | 12289 | 12 | 0.09765% | 2048.17 |
| 72 | 12289 | 24 | 0.19530% | 1024.08 |
| 84 | 65521 | 84 | 0.12820% | 1560.03 |
| 96 | 12289 | 96 | 0.78119% | 256.03 |
| 90 | 65521 | 90 | 0.13736% | 1456.03 |

The final column compares p_n(q) with 2/q', assuming equal test cost.
It shows why prime size alone is a poor membership rule; it does not
claim those larger tests cost the same. The primality of the illustrative
constants is documented in primary sources: 12289 in the
[NewHope specification](https://www.newhopecrypto.org/data/NewHope_2017_12_21.pdf),
and 65521 in [RFC 1950](https://www.rfc-editor.org/rfc/rfc1950).
The root counts and fractions above are direct gcd arithmetic.

For an ideal scalar rejection cascade with fixed per-test costs c_i,
the expected cost over a full CRT period is

    sum_i c_i * product_{j<i} s_j
      + C_next * product_i s_i.

Exchanging two adjacent tests shows that i should precede j when

    c_i + s_i*c_j <= c_j + s_j*c_i,
    equivalently p_i/c_i >= p_j/c_j.

Inserting a test before downstream work with expected cost C_next is
beneficial in this model when c_i < p_i*C_next. For equal costs this
suggests selecting a threshold in g_n(q)/q, not in q alone. Because
g_n(q) <= n, a threshold p_n(q) >= tau gives a finite candidate universe
q <= n/tau. With costs bounded below by c_min, a threshold in p/c
likewise gives q <= n/(tau*c_min).

The generated GPU rounds execute every pack in a round before checking
the accumulated verdict. They do not stop after each prime. Therefore
the scalar formula is a ranking/design model, not the current kernel's
exact cost. Apply measured costs at actual compaction boundaries and
include pack formation, table traffic and queue costs. Simply sorting
the existing list by this formula is not the proposal.

### Correctness and representation requirements

Any finite selected set S of prime divisibility tests is a necessary
filter for the original all-prime target, once equality exceptions are
handled. Removing a sieve prime admits more composites; adding one
rejects only composites above the exception zone. Neither action loses
a true target solution. Full host classification and discovery proofs
remain required.

This preservation of true solutions does **not** imply that the old and
new sieve/PRP survivor lists, census counts, or near-event counts are
identical. A changed predicate needs an independently specified stream
and explicit evidence metadata. Do not relabel changed work as the same
frozen score workload. Any claim to preserve a particular census stream
needs its own proof or a retained reporting path.

The representation can hold some larger primes, but the costs are real:

- `_tail_tables` at 4588 stores an exact pattern over [0,2q), requiring
  `4*ceil(2q/32)` bytes. This is 3076 bytes for 12289 and 16384 bytes for
  65521, per prime before other tables/metadata.
- `tail_packs` at 4568 requires product M < 2^30, preserving the lazy
  remainder's u32 bound. Two primes near 12289 fit together; three do
  not. Two primes both above 32768 cannot share such a pack. The
  arithmetic cost can rise as the prime menu expands.
- The root-list cap bounds gcd(n,q-1), not q itself. These n <= 96
  targets remain within the current 128-root bound, but all table/index
  and record arithmetic still needs validation.
- Initially preserve the existing window and in-block prefix and modify
  only later per-candidate tests. Inserting large q into the window can
  exhaust its 12 KB pattern budget and change the layout. That would
  obscure the first comparison.
- The true maximum selected prime must replace the old cutoff wherever
  it defines equality-exception coverage or arithmetic headroom. See
  [cyclotomic_search.py](../cyclotomic_search.py), `k_floor`/`zone` at
  161–177, and GPU record bounds at 3296–3301 and 3674–3678. Leaving
  q2 = 8192 as misleading metadata while testing larger primes is unsafe.
- The exact prime list and order need identities in configuration,
  checkpoint and benchmark manifests. Every generated, generic and
  overflow fallback route must apply the same selected predicate.

### First bounded experiment for Claude

Keep the wheel, numerical interval and six device forms fixed. Preserve
the existing early sieve stages. Compare the current later-prime set
with small, explicitly recorded selections drawn from maxima 16384,
32768 and 65536. Those maxima bound the selection exercise; they are
not instructions to sieve every prime through those bounds. Use matched
test-count and matched table-byte alternatives, then price actual pack
and phase costs. A selection with fewer final survivors but slower
completed coverage is a rejection.

First examine n = 96, where the root-count spike is especially clear,
and n = 90, where current depth-sweep evidence exists. Include n = 72
before extrapolating a result to the rest. Use an independent explicit-set
CPU comparator, known true values, populated intervals, equality-zone
fixtures, record bounds, and overflow fallback cases. Keep original
frozen shapes intact and document any new stream's independent expectation.

After an isolated result is established, jointly retune the chosen
membership and stage boundaries. Reprice it with CYL-011's wheel if that
change also succeeds; their gains share some of the same saved work and
cannot simply be multiplied.

## CYL-014 — interleave cheap Fermat rejection with the sieve tail

**Classification:** new exact ordering experiment; no measured gain.

The current sequence is the complete sieve, followed by the six-form
Fermat chain. Try instead:

    existing strong sieve prefix
      -> Fermat test of Phi_1(x) = x-1
      -> remaining original sieve tests
      -> remaining original Fermat forms.

A second arm can move Phi_2(x) = x+1 alongside Phi_1. Every original
predicate remains present. Their conjunction is order-independent, so
the final survivor set is exactly unchanged when arithmetic and fallback
paths are correct. A Fermat pass is not a primality proof and never
justifies deleting any remaining divisibility test.

This is distinct from round 1's depth sweep: that experiment removed a
different sieve suffix and sent more items through the full Fermat chain.
Here the same tests remain, in a different order.

### A falsifiable cost criterion

Let T be the tail suffix under consideration and F the first one or two
Fermat tests. On the **same incoming cohort**, let t and f be their
passing fractions. With conditional average costs, compare

    T then F: C_T + t*C_(F|T)
    F then T: C_F + f*C_(T|F).

If per-input costs are unchanged by conditioning, F first wins precisely
when

    c_F*(1-t) < c_T*(1-f),

before new queue/launch costs. This identity does not require the pass
events to be independent. For two Fermat tests, use their joint pass
fraction and `c_F = c_1 + P(pass F_1)*c_2` under the fixed-cost model.
Measure conditional costs when candidate bits or active-lane behavior
make that approximation inaccurate.

Even with individually fixed c_1 and c_2, the two-form chain's aggregate
cost after T is `C_(F|T) = c_1 + P(pass F_1 | pass T)*c_2`, which need
not equal C_F. The simplified inequality for that arm requires the
aggregate conditional cost to be unchanged too; otherwise use the
general formula above.

If CYL-013 and CYL-014 are later combined, also measure conditional
prime-rejection fractions. After Fermat filtering, the incoming cohort
is no longer described by the unconditional CRT fraction g_n(q)/q.
For example, two-root primes reject only x = +1 or -1 modulo q, the
roots of the two linear forms. Their remaining value may fall after
those forms pass Fermat, but pseudoprimes prevent treating the tests
as redundant by proof.

Do not insert Fermat so early that its much larger input population
outweighs the tail work saved. Round 1's failed shallower-sieve cost model
is a specific reason to treat the inequality as a screening criterion,
not a prediction from instruction counts alone.

### Implementation and validation scope

Use existing generated-tail round boundaries as the initial cut points
([cyclotomic_gpu.py](../cyclotomic_gpu.py), rounds at 3848 and generated
tail emission at 1306–1399). Compare the same full prime set and six-form
conjunction over identical absolute workloads, separately from CYL-013.
The complete sorted survivor vector should match exactly in this experiment.

The tail queues hold offset records, whereas the PRP stage carries
indices into a stable offset array (`prp_stage` at 1591 and `_prp_enqueue`
at 4549). Earlier PRP buffers must be sized from survival at the chosen
cut, not the final-sieve survival used at 4508. Queue overflow and every
generic fallback must still visit every predicate. Validate empty/full
queues, limb transitions, partial final batches, restart, and the high
campaign bases. A correct main path with an incomplete overflow path
cannot ship.

First compare one-form and two-form cuts before the last tail round and
at one earlier round boundary. Record incoming counts, all pass fractions,
tail and PRP time, queue conversion/capacity, total device/host cost and
full completion cost. Reject a cut that loses its advantage after buffer
management or produces a different final stream.

## What these two proposals could realistically affect

The measured n = 60 split in
[OPTIMIZATION_LOG.md](../OPTIMIZATION_LOG.md), round 1 at 336, is 51.6%
sieve kernel, 30.4% generated tail and 17.9% Fermat. With the early sieve
fixed, tail plus Fermat accounts for about 48.3% of device time. Even
eliminating both would give only 1/(1-0.483) = 1.93x under that fixed
phase-share assumption.

For scale only, halving tail cost and reducing Fermat cost to one fifth
would give approximately

    1 / (0.517 + 0.304/2 + 0.179/5) = 1.42x.

Those hypothetical phase improvements have **not** been measured or
predicted by this report. A 20% reduction in total cost would be a useful
1.25x speedup and could save hours; neither new proposal has yet shown
it. Phase shares for 72/84/96/90 must be measured before transferring
the n = 60 bound to those indices. These are moderate-gain experiments,
not a demonstrated answer to the previous 6.5–11.3x median-time targets.

## Other routes investigated

### Live-word compaction: valid, but no large benefit established here

The current window accumulates all prime masks before extracting live
candidates (GPU lines 2995–3055). A new midpoint queue could retain only
live 32-bit words together with their original coordinates, then apply
the remaining pattern tests to those words. This is distinct from the
existing candidate compaction.

If a fixed bit survives a prefix with complete-period density rho_k,
a union bound gives live-word fraction at most min(1,32*rho_k), without
assuming independent bits. For L original window primes, the logical
word-test count would be at most

    k + (L-k)*min(1,32*rho_k)

per original word, before compaction and reconstruction costs. At n = 60
the recorded L is 87 and final density about 0.0064. Applying that final
density to all 87 tests would be an error: those tests were needed to
reach it. Sorted killing power gives rho_k <= rho_L^(k/L); at k = 70
this proves only about 79.3 tests instead of 87, roughly a 1.10x logical
test-count reduction. Actual prefix products might improve the case,
but they must be inspected.

Sparse words also lose the current phase/load amortization across eight
words. The [primorial-ap proposal](../../primorial-ap/codex-reviews/2026-10-20-static-review.md#pap-001-stop-sieving-dead-words-and-use-the-exact-interval-tail)
had a much longer tail after its sparse prefix; its 4.34x gather-count
argument does not transfer. Keep this below CYL-013/CYL-014 unless real
prefix counts and a full cost model establish a stronger case.

### Shared ancestor catalogs: the numerical overlap is too small

Common forms do not make primality tests at different x reusable. For
two targets a,b, their shared forms are D(gcd(a,b)). After this common
modular sieve, the extra forced-prime conditions alone make identical-x
work sparse. For 60/90 the duplicated fraction of separately routed
common-prefix work is 1/664, approximately 0.1506%; for 72/96 it is
1/16582, approximately 0.00603%; for 84/96 it is 1/2030, approximately
0.04926%. These condition the older raw 60/90 forcing calculation,
whose 1/3984 fraction was not a later-stage overlap estimate.

For clarity, put g = gcd(a,b), and let A be the product of
`q-gcd(g,q-1)` over primes forced for a but not g, with B similarly for
b. The extra-prime sets are disjoint. CRT gives separate densities
1/A + 1/B and overlap 1/(A*B), hence duplicated fraction 1/(A+B).

For the full modular filters through Q, define

    d_a = product_q (1-gcd(a,q-1)/q),
    d_ab = product_q (1-(gcd(a,q-1)+gcd(b,q-1)
                         -gcd(gcd(a,b),q-1))/q).

The intersection formula follows because the intersection of the two
root subgroups has order gcd(gcd(a,b),q-1). Adding a new prime multiplies
d_ab by a factor no larger than either branch's factor, so
`d_ab/(d_a+d_b)` cannot increase as Q grows. Arithmetic through 97 gives
0.0440190% for 60/90 and 0.0365196% for 84/96; every other pair is smaller.
A pairwise union bound caps all-five duplicate modular-density work at
0.1761%, and the four future targets excluding 60 at 0.1096%.

These are full-CRT-period density statements, not finite-window counts
or bounds on the later PRP-conditioned population. They are nevertheless
a strong negative case against a multi-fold shared-generation benefit.
Any challenge should measure actual identical-x overlap and work saved
after the complete target-specific sieve.

Generating an ancestor catalog before applying target-specific modular
conditions increases expensive work. For example, through prime 97,
D(48) has exactly 49 times as many modular survivors as D(96), due to
the additional forcing at q = 97. D(24) has 657 times as many as D(96)
and 15925 times as many as D(72). Applying the child conditions first
recovers the present per-target strategy. Stored first occurrences and
census totals are not complete ancestor catalogs for later replay.

### Faster primality alone and batch trial division

The entire current Fermat stage is only 17.9% at n = 60: deleting it
would yield at most 1.22x there. Degree ordering is already implemented;
the existing log prices symmetric Montgomery squaring at about 1.04x
overall. A monolithic six-form kernel would trade queue savings for
sparse active lanes, since the current chain already compacts between
forms. These do not support a new multi-fold claim.

Batch trial division with product/remainder trees is a real alternative
to independent scalar divisibility tests; see the primary
[FactHacks algorithm description](https://facthacks.cr.yp.to/batchtrial.html).
For this family, `gcd(product(q), x^n-1)` exactly detects a divisor from
the chosen prime set above equality exceptions. But materializing these
large integers, building trees and moving data could cost more than
the current small-modulus GPU tables. No campaign-sized operation or
memory case was established here. Do not recommend a port merely from
the algorithm's asymptotic advantage on a different workload.

### Algebraic substitutions do not supply another exclusion

For odd d, `Phi_d(x)*Phi_(2d)(x) = Phi_d(x^2)`. The right side is supposed
to be a product of two primes when the required pair succeeds; demanding
that it itself be prime would reject valid targets. Enumerating y = x^k
on exact powers preserves the original candidate count, while sweeping
all y expands it. The forced class also gives no reason to require the
parameter t = x/U to be prime.

Cyclotomic order identities cannot safely replace the independent
primality screen with a base-x Fermat test. For example,
`x^3 = 1 mod Phi_3(x)`, and when 3 divides x, 3 also divides
`Phi_3(x)-1`. The base-x Fermat condition is then automatic, including
for composite values. Such identities are useful for structural
certificates under their full hypotheses, not as extra rejection here.

## Parallel execution if independent devices are available

Multiple independent GPUs can reduce elapsed time by dividing the
existing work. More processes on the same saturated GPU do not create
that compute capacity. Running different indices on separate devices
reduces the total calendar time for the collection, but does not itself
shorten any one index's search.

To shorten one index, split a fixed segment's immutable launch manifest
among devices, or assign disjoint numerical tiles with the same exact
predicate. For a fixed segment, every launch is assigned once, each
result is independently checked, and the segment is committed only
after all assignments are complete. For numerical tiles, the committed
frontier is the largest gap-free verified prefix. Discovering a candidate
in a later tile does not establish leastness before earlier tiles finish.

Required engineering includes deterministic assignment identities,
durable completion receipts, retry/deduplication, source/predicate hashes,
per-device independent buffers, common sorted pending results, and
coverage/certificate gates. Workers must not concurrently write the
same campaign checkpoint or evidence ledger. Initial assignment can
use the present decomposition; it does not require a larger wheel.

With P equally fast devices, T/P is an ideal limit for perfectly balanced
parallel work; coordination, the slowest assignments and serial proof
work reduce the gain. No scaling measurement was made, no device
inventory was queried, and no machines or services were provisioned.
This is a resource-dependent option, not a promised software-only speedup
or a purchase recommendation. Only the owner starts campaigns.

## Claude handoff and acceptance

Prioritize CYL-013, then CYL-014, independently of the previous wheel
experiments. Keep the regular Python installation, independent oracle,
host verification and certificate route. Follow the short-invocation and
active-project rules in [CLAUDE.md](../../CLAUDE.md); isolate later tests
from the owner's running hunt. Scratch harnesses remain outside the
public project surface.

Record exact absolute workloads, selected prime/form predicates,
source hashes, heights, phase counts, table/queue memory, paired A/B
results with A/A controls, host cost and complete-segment time. Require
the relevant public selftest and score checks for any final code change,
with a separately justified new fingerprint when the predicate changes.
This review executed none of them.

Reject any design that loses a true target, mishandles equality or
overflow, changes a cursor's meaning without migration, or improves
only a partial-kernel metric while worsening completed coverage. Update
the [finding ledger](README.md) with kept/rejected/inconclusive results
and links to actual evidence. A static proof of safe filtering is not
evidence of a speedup.
