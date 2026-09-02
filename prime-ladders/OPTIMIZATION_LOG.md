# OPTIMIZATION_LOG — prime-ladders

Every attempt: the change, the measurement, kept or rejected. Failures
included — they are the record that stops the next person retrying them.
Read [OPTIMIZATION.md](../OPTIMIZATION.md) first; its rules are binding
here, and this engine is a *transfer*, which changes what the first pass
has to establish: not whether the kernel is fast, but whether the
configuration is right for a problem whose survivor density is 140× lower
than the one the kernel was tuned on.

## v1 — square-ladders' engine, re-keyed to the primes (2026-09-02)

**What it is.** square-ladders' v5 GPU engine with `killed_residues(q, n)`
replaced by `killed_residues(q, n, s) = { -s·prime(i)⁻¹ mod q : i ≤ n,
prime(i) ≠ q }`, and one addition: a window may start inside period 0
(`k_min`), because both of this project's frontiers and the modelled
medians of the next two terms of each family sit inside the first
`6.15×10¹⁷` of line. The kernel, the three-level CRT wheel, the compaction
design and the `(k, off)` representation are unchanged and are documented
in square-ladders' log; nothing below re-measures what that log already
measured, except where this problem's density changes the answer.

**Design-time rules applied before a line was written:**

- **2.7, carry `(k, off)`.** Inherited. The enforced ceiling is the
  primality-proof bound `k_ceil(n, s) = (3.317×10²⁴ − 1 − s) / prime(n)`,
  `7.7×10²²` at n = 14, and no machine word appears in it (G10, tight to
  one k).
- **Choose the wheel that fits at every parameter the battery runs.** The
  same (23], (37], (47] wheel serves both signs and every filter the
  battery runs, because `w(q,n,s)` is sign-independent and the tables only
  shrink as n grows. What did *not* fit is recorded under "ceilings found".
- **Measure the campaign, not just the engine (5c).** The A/B below is
  over wheel *and* sieve depth, priced in device time and host
  core-seconds per unit of line together, because the two trade against
  each other here.

### Measured during the v1 build

**1. Wheel and sieve depth, paired and interleaved (3 rounds, n = 14,
s = +1, from `k = 7×10¹⁷`). KEPT: three levels, sieve 65536.**

| configuration | line rate (median) | [min, max] | candidates/s | survivors per unit line | ratio |
|---|---|---|---|---|---|
| **3L (23],(37],(47], q2 = 2¹⁶** | **1.077×10¹⁷** | [1.06, 1.08] | 1.03×10¹¹ | 4.79×10⁻¹³ | **1.000** |
| 3L, q2 = 2¹⁷ | 1.001×10¹⁷ | [0.999, 1.02] | 9.61×10¹⁰ | 2.04×10⁻¹³ | 0.929 |
| 2L (23],(37], q2 = 2¹⁶ | 6.23×10¹⁶ | [6.22, 6.29] | 1.73×10¹¹ | 4.78×10⁻¹³ | 0.578 |
| 1L ≤ 23, q2 = 2¹⁶ | 8.91×10¹⁵ | [8.90, 9.07] | 1.12×10¹¹ | 4.86×10⁻¹³ | 0.083 |

The third level is worth **1.73×** over two and the wheel as a whole
**12×** over one, at candidate rates within 1.7× of each other: the kernel
does the same work per candidate on every wheel, and the wheel decides how
many candidates a unit of line costs. The spread between rounds is 2%, so
the ratios are real.

The deeper sieve buys a 58% cut in survivors for 7.1% of the line rate.
That is not a tie, so the throughput rule keeps 2¹⁶ — but it is the
setting to reach for if the host ever binds (see 2), and the price is
written here so it does not have to be re-measured: **−7.1% device for
−58% host.**

**2. Host classification, on 3,257 real survivors of the production shape.
KEPT: the two-pass base-2 screen, and a 2-worker ramped pool.**

| classifier | per survivor | run lengths |
|---|---|---|
| deterministic 7-base chain on every value | 49.6 µs | reference |
| **base-2 strong test, confirmed with the 7-base chain only at run ≥ 8** | **13.1 µs** | identical |

A failed base-2 test is a proof of compositeness (huntlib.primes), so the
screen can only overstate a run, and every run it reports at or above the
census floor is recomputed deterministically. The classification drill
asserts the two agree on real survivors every selftest.

Sizing (CONVENTIONS.md "Sizing a hunt so it leaves the machine usable",
step 1): `4.79×10⁻¹³` survivors per unit line × `1.08×10¹⁷` k/s = **5.2×10⁴
survivors/s** × 13.1 µs = **0.68 core-seconds per second**. Two workers are
2.9× that requirement at about 35% duty each; one would run at 68% and
leave the device idle whenever a burst arrived. `WORKERS_DEFAULT = 2`,
ramped one at a time at below-normal priority, with `--workers 1` and
`--gentle` as the priced throttles. Not `cpu_count − k`.

The run-length histogram of those survivors — 1741 / 787 / 396 / 169 / 95 /
41 / 17 / 8 / 2 / 1 at runs 0 through 9 — is a geometric tail at ratio
≈ 0.45, which is what "each value is prime with probability about 0.55
after a sieve to 65536" predicts. Three of 3,257 reached the census floor.

**3. The segment loop's host side, timed without the device (400 launches
of 535 survivors through a real 2-worker pool, the device's 10.4 ms per
launch stood in by a sleep).**

| step | per launch | share of a 10.4 ms launch |
|---|---|---|
| `_submit` (chunk, pickle, enqueue) | 0.096 ms | 0.9% |
| non-blocking `_drain` | 0.037 ms | 0.4% |
| `checkpoint.save` with 3,000 pending | 6.7 ms every 128 launches | 0.5% |
| heartbeat `p_by` (one integral) | 29 ms every 30 s | 0.1% |
| rung ladder | cached on the frontier (`LiveLadder`) | 0 |

The backlog at the end of 400 launches was zero and the final blocking
drain took no measurable time: the pool keeps up with margin. So the loop
is about **98% device by construction** — but that is the components
summed, not the loop timed. OPTIMIZATION.md 2.14's rule is that the loop
owes a measurement of **wall clock per unit line against device time per
unit line, in the campaign's own configuration**, and only a campaign can
produce the first half. **PENDING the first run:** the `[STATUS]` rate at
n = 14 should read close to `1.1×10¹⁷ k/s`; anything under `1.0×10¹⁷` is a
per-launch cost that does not scale with the work, and the place to look
first is whatever sits between the launches.

**4. Period granularity against the early terms. KEPT: the coarse wheel,
with `k_min`.** A three-level period is `6.15×10¹⁷` of line — 5.7 s — and
a discovery is only the *least* k once its period closes, so a find costs
at most one period of over-sweep. The alternative was to open on the
two-level wheel (period `7.4×10¹²`) and migrate, as square-ladders did.
Priced: 0.578× the rate for finer narration of terms that will all be
inside the first ten seconds anyway. The coarse wheel's one real cost is
that period 0 contains the floor, which is what `k_min` is for.

### Ceilings found

- **The doubled bitmap must address in 32 bits.** `sum(2q)` over the
  sieve primes is `1.5×10⁹` bits at q2 = 2¹⁷ and `5.5×10⁹` at 2¹⁸; the
  offsets ride in slot `.w` of a uint4. Asking for 2¹⁸ surfaced as an
  `OverflowError` inside numpy during the A/B, and is now a stated ceiling
  the engine refuses (drilled). A deeper sieve than 2¹⁷ is a new engine
  version with a wider offset.
- **The sign must be ±1.** Refused rather than silently reduced.

### What the gates caught during the build

- A gate that failed with an **empty message**: G13's forced-divisibility
  check used a conditional expression whose false branch was `""`. The
  battery showed `FAIL ` with nothing after it, which is a bug in the gate
  and was fixed as one.
- **Three vacuous windows.** G4's n = 10 window, the resume drill's
  sub-period seam and the classification drill all came out with zero or
  one survivor at this project's density, and each refused itself rather
  than pass on nothing — the "empty-vs-empty does not count" rule doing
  its job. Every window was re-sized from a measured survivor count.
- G4 at its first working size cost 55 s of a 31 s battery; re-sizing it
  to shallower sieves and populated 10⁷-wide windows brought it to 11 s.
  The battery is measured on the same terms as the engine (Rule 1).

### Priced and declined, or not yet measured

Hypotheses with estimated ceilings, per Rule 5a — none of these is a
result, and the first pass after a campaign has run should start here:

| candidate | estimate | why it is plausible here and not in square-ladders |
|---|---|---|
| **The x-tile is 1,024 first-level residues and R1 is 2,800**, so the last block in each x-row is 73% full and 9% of x-blocks are partial. Re-sweep `CPT`/`SPB` (e.g. SPB 16, JPT 2) | ~1.05× | square-ladders' R1 was 1,088,640 and the tail was invisible |
| **Launch size** `CAND_PER_LAUNCH` 2³⁰ → 2³¹ (52 → 104 third-level residues per launch) | ~1.01–1.03× | 10.4 ms launches; the flat 2.6% square-ladders measured was at 32 ms launches |
| **Re-sweep `LIT_SURV` / `K2_SURV`** on this survival curve (LIT = 10 primes, K2 = 45 here against 7 and 25 there) | unknown; both directions | the curve is steeper: w = n from the first sieve prime |
| **Sieve 2¹⁷** | −7.1% device, −58% host | measured (1); take it if the host ever binds |
| **A084700 past the proof ceiling.** `N − 1 = prime(i)·k` is factored by construction, so BLS75 Theorem 1 proves every value once k is factored (a 23-digit k factors in milliseconds). Raises the ceiling from `5.4×10²²` | opens a(18): the model puts it below the current ceiling with only ~28% probability | dickson-ladders built exactly this path; A084701 cannot use it (its structure is on `N + 1`, an N+1 test huntlib does not have). **DONE in v3, below** — the first campaign hit exactly this ceiling |
| **Two campaigns at once** on one device (both families) | 2× wall-clock efficiency of the operator's time, ~1× device | the kernel is the same module; the two would time-slice the GPU |

**Do not rebuild:** everything in square-ladders' rejected list (its
`OPTIMIZATION_LOG.md`, "Things that did not pay") applies to this kernel
unchanged, since it is this kernel.

---

## v2 — the tail compacted, round 2 split, the loop pipelined. KEPT: 1.5x (2026-09-02)

`SCORE 202,524,485,715` (v1: 111,143,013,071 — a cross-run 1.82x on a GPU
whose ambient load moves absolute rates by 10% or more; the PAIRED ratio
against the v1 engine in one process is **1.52x** before the last
constant and about 1.57x with it). Every one of the five fingerprints is
identical to v1's: the same wheel, the same sieve depth, the same stream.
37/37 green.

All numbers below are from harnesses importing the engine and sweeping the
frozen `SCORE` window (period 1, the first 3,328 third-level residues, n =
14, s = +1) with the fingerprint `34281 / 714767005960532266` checked on
**every** run; configurations were measured interleaved and the ratio is
the claim (OPTIMIZATION.md rule 3). Absolute rates drifted ~10% between
runs on this desktop; ratios inside a run held to 1–2%.

### Measurement 1 — the phase split, which the transfer never took

v1's log listed hypotheses and no split. CUDA events around the two kernels
and a nested differential ablation of the sieve kernel (each variant a
prefix of the real one, removed work replaced by a data-dependent fold so
nothing hoists):

| phase | v1 | share |
|---|---|---|
| generation | 16.6 ms | 2.6% |
| CRT-combined prefix (5 groups, every candidate) | 198.5 ms | 31.4% |
| queue-1 push | 63.4 ms | 10.0% |
| round 2 (27 groups, branchless on every prefix survivor) | 189.6 ms | **30.0%** |
| global push | 6.5 ms | 1.0% |
| tail kernel | 156.4 ms | **24.8%** |
| host gap (device idle between launches) | 13.8 ms | 2.2% of wall |

Two things square-ladders' verdicts did not predict, because its survival
curve is a different curve: round 2 here is 27 group tests (19 of them
single primes — the 96 KB table budget halves `K2_GROUP_MAX` until the
pairs stop at 179) run branchless on 11% of candidates, most of which the
first few groups have already killed; and the tail is a quarter of the
device, against 10.7% there.

### Measurement 2 — what the tail was bound by (three wrong answers first)

- **"L2 misses on the 50 MB bitmap."** Masking the gather address to 2^16 /
  2^20 / 2^24 / 2^27 bits cut the tail to 31 / 78 / 124 / 154 ms against
  158. Read naively that says memory. Read properly, each mask also folds
  the *deep* primes' patterns onto dense low-prime patterns, so the rare
  deep items die early — the variants price the deep items, not the
  address spread. Building the memory fix anyway (a 128-bit mask prefilter
  plus exact residue list, no bitmap) measured **0.89x**: 215 ms against
  141 in the same run. Correct, and slower.
- **"Block stragglers."** Tail block width 32 / 64 / 128 / 256 with one
  item per thread: **within 1%** of the shipped 256 x 3 items per thread.
- **"Divergence, cured by rounds."** Fourteen compaction rounds over
  global queues (survival halving per round, one lane per item, one global
  atomic per block for the push): **179 ms — worse**. The per-round probe
  then said why, and it is the real answer:

| round | primes | items in | ms / launch |
|---|---|---|---|
| 0 | 17 | 5,944,811 | 0.125 |
| 1–5 | 23–91 | 2.9M → 173k | 0.081 → 0.034 |
| 6–7 | 134–201 | 86k → 42k | 0.049 → 0.071 |
| 8–13 | 308–2,110 | 21k → 690 | 0.104 → **0.748** |

**The six deepest rounds held 0.4% of the items and 80% of the tail.** A
round of 1,368 items against 2,110 primes is 43 warps on an empty device,
each a serial chain of 527 dependent batches. Rare-and-deep is not a
divergence problem; it is a *latency* problem, and no amount of packing
lanes fixes a chain.

### v2a — lanes per item in the tail rounds. KEPT: tail 2.43 → 0.85 ms/launch

A round whose expected item count would leave the device under
`TAIL_FILL = 2^19` threads gets 2, 4, … 32 lanes per item: each lane tests
every LPI-th prime of the round and the lanes vote (`__any_sync`) after
every batch, so the chain is LPI times shorter and the same tests are
done. LPI comes from the analytic survival, per round, on the host. With
the kernel generated once per LPI value in use (a runtime LPI cost the
shallow rounds 0.216 vs 0.125 ms):

| | tail / window | wall / window | rate |
|---|---|---|---|
| v1 | 157 ms | 637 ms | 1.12e17 |
| rounds, 1 lane/item | 179 ms | 659 ms | 1.08e17 |
| + lanes per item | 54 ms | 545 ms | 1.31e17 |
| + per-LPI kernels | **50 ms** | **464 ms** (with v2b) | |

The per-prime tables changed with it: one `uint4` (magic, q, base mod q),
a 4,096-bit mask per prime — the **exact** kill pattern for q ≤ 4096,
where 99.6% of tail items die, and a prefilter above it that sends about
n/4096 of tests to an exact residue list — 3.3 MB in place of the 50 MB
doubled bitmap, with the base folded by one add and one conditional
subtraction instead of a second copy. `MASK_BITS` 2048 / 8192 measured
0.998x / 0.995x: the mask is not where the time is any more, and the
bitmap ceiling (2^32 bits, reached at q2 = 2^18) is gone with the bitmap;
the residue list's `NRES_MAX = 32` slots are the new stated ceiling on n,
drilled.

### v2b — round 2 split into compaction rounds. KEPT: sieve 477 → 403 ms

`R2_SPLITS` names intermediate survival fractions between the prefix and
the global push; each is one more shared queue and one `__syncthreads`,
and it stops the later groups testing candidates the earlier ones killed.
One split at 0.03 (after the first 5 pairs) was **1.16x** on the whole
window; at the shipped K2:

| splits (K2 = 0.0057) | none | 0.05 | 0.03 | 0.02 | 0.05, 0.015 | 0.04, 0.012 | 0.06, 0.03, 0.012 |
|---|---|---|---|---|---|---|---|
| | 1.000 | 1.089 | 1.163 | 1.176 | 1.156 | 1.164 | 1.142 |

Two splits buy nothing over one; the second queue's sync costs what its
saved tests are worth.

### v2c — the loop pipelined

Launch i+1 is enqueued *before* launch i's survivors are read back, and
the readback is an asynchronous copy of the count and the first `PRE_COPY`
survivors into pinned host memory behind each launch, waited on by that
launch's own event — a plain `.get()` on the null stream queues behind the
next launch and waits for it too. Host gap 13.8 → 4.4 ms per 64 launches
(2.2% → 0.9% of wall), and the ~15 extra kernel launches per sieve launch
that the tail rounds add are hidden behind the device.

### The constants, re-swept on v2 (they moved, as they always do)

Single-knob sweeps on v1 first, for the record (ratio vs shipped v1):
`LIT_SURV` 0.14 **1.109**; `LIT_GROUP_MAX` 2^19 1.075; `tpb` 128 1.066;
`K2_SURV` 0.015 1.054; `--maxrregcount 80` 1.054; `UNROLL` 8 1.033;
round-2 table budget 256 KB 1.027; `spb` 4 1.027; a 2^31 launch 1.024;
`TAIL_BLOCKS_PER_SM` 256 1.010. Lost: `tpb` 512 0.909, `spb` 16 0.753,
`cpt` 64 / `spb` 16 0.667, every `jpt` = 11 shape 0.81–0.92 (the 73%-full
last x-block was a non-issue: the block finishes early), `K2_SURV` 0.002
0.878, `K2_GROUP_MAX` 2^17 0.895, `UNROLL` 2 0.923, `CAND_PER_LAUNCH` 2^29
0.964. Flat: `QCAP_SIGMA` 3 / 12, `LIT_GROUP_MAX` 2^16 / 2^17.

Then jointly on the v2 structure, where the answers changed (`LIT_GROUP_MAX`
2^19 went from 1.075 to **0.975**; a deeper prefix stopped paying once the
rounds behind it were cheap):

| configuration (K2, split, tpb, …) | ratio |
|---|---|
| 0.0057, 0.03, 256 (v2b as first measured) | 1.000 |
| 0.015, 0.03, 256 | 1.032 |
| 0.0057, 0.03, **128** | 1.094 |
| 0.015, 0.03, 128 | 1.111 |
| 0.015, 0.02, 128 | 1.102 |
| 0.01, 0.03, 128 | 1.106 |
| 0.015, 0.03, 128, spb 4 | 1.032 |
| 0.015, 0.03, 256, spb 4 | 1.054 |
| 0.015, 0.03, 128, LIT_SURV 0.14 | 1.064 |
| **0.015, 0.03, 128, LIT_SURV 0.19** | **1.123** |
| 0.015, 0.03, 256, maxrregcount 80 | 1.102 |
| 0.015, 0.03, 128, maxrregcount 80 | 0.896 |

Shipped: `TPB_DEFAULT` 256 → **128**, `LIT_SURV` 0.11 → **0.19** (three
prefix groups, 80 registers instead of 96), `K2_SURV` 0.0057 → **0.015**
(29 primes in-block, the rest to the tail rounds, which are now the
cheaper place for them), `R2_SPLITS = (0.03,)`. `TAIL_ROUND_DROP` 0.3 / 0.7
measured 1.004 / 0.965 against 0.5; `TAIL_FILL` 2^18 / 2^20 flat.

### Termination table (OPTIMIZATION.md Part 3), v2

| phase | v1 share | v2 verdict |
|---|---|---|
| prefix | 31.4% | three groups now; `LIT_SURV` and `LIT_GROUP_MAX` re-swept on v2, both at their knee. Still the largest phase; not re-split after the round change |
| round 2 | 30.0% | attacked: compaction rounds, 1.16x; split count and depth swept both ways |
| tail | 24.8% | attacked: latency, not memory or divergence — lanes per item, 3.1x on the phase; `MASK_BITS`, `TAIL_ROUND_DROP`, `TAIL_FILL`, tail `tpb` all flat |
| queue-1 push | 10.0% | untouched; square-ladders' warp-aggregation measured 0.887x on this kernel and was not retried |
| generation | 2.6% | below the 5% line |
| host gap | 2.2% | pipelined to 0.9% |

**Not done, priced, and the biggest thing left — a wheel to 53 by sieving
k/2310.** Every candidate at n ≥ 14 is a multiple of 2310, so the engine
can run on k' = k/2310 with kill sets K'(q) = 2310⁻¹·K(q) mod q. That
divides every wheel bound by 2310: W1' = 13·17·19·23·29·31 = 8.7e7 (u32,
856,800 residues), W2' = 37·41·43·47·53 = 1.6e8 (u32), W' = 1.4e16 < 2^63,
so 53 fits where today nothing does (adding it directly puts W2 at 1.5e11
and W at 3.3e19, past both u32 and 2^63). 53 kills 14 of 53 residues:
**1.36x fewer candidates per unit of line**, the prefix still five groups
(59·61·67, then pairs), so about 1.35x end to end. Costs: a k-period of
3.3e19 (2–3 minutes of over-sweep at a find, against six seconds now),
new SCORE/SCOREM fingerprints (the period-denominated 2L/1L/10 shapes
keep theirs), and every wheel gate re-derived in k' space. Not started
tonight; it is the next engine version, not a constant.

**Also not done:** CRT-combining the tail rounds' first primes (the tail is
now 11% of device, its shallow rounds two thirds of that); `spb` 4 at
`tpb` 128 (0.93x here, 1.03x on v1 — re-sweep after the wheel change);
overlapping the tail rounds with the next sieve on a second stream
(bounded by the tail's 11%).

### What the gates caught

- The first mask-and-list tail indexed its per-prime record with a stride
  in u32 units on a `uint4` pointer — it read prime 4i's magic for prime i
  and passed 5 million candidates through. The survivor buffer overflow
  (`HIT_CAP`) caught it before any fingerprint could.
- The generated in-block round counts were named `n1, n2, n3, …` and at
  three splits `n3` shadowed the kernel's global-queue counter pointer:
  a compile error, from the sweep harness rather than a gate, and the
  reason the generated names now carry a prefix.
- G15 was rewritten with the tables: residue lists and masks are checked
  against `killed_residues` on 40 sampled primes, the mask exact below
  `MASK_BITS`, and the fold is now `base mod q` itself.

---

## v3 — the ceiling raised past the proof crossing, the wheel to 53 in unit space, the constants re-swept. KEPT: 1.70× at the live filter (2026-09-02)

`SCORE18 6,156,431,019,029` — the new shape at the filter the campaign is
running, n = 18 — against the v2 engine's **3.58×10¹⁸ k/s** measured
paired on the same line the same morning: **1.72×** (1.70× in the
paired harness). Every one of the three k-space fingerprints identical
to v1's; `SCORE` and `SCOREM` re-frozen on the unit wheel and `SCORE18`
added. 41/41 green in 42 s (G1b, re-checking the four finds from the
definition, joined the battery with the documentation pass); `score.py`
2.5 min. The three k-space shapes
read 0.86–0.89× of v2's ledger row in this run with v2's own constants
— unpaired, an hour of sweeps into the GPU's day, and inside the 10%+
run-to-run band the v2 row already warns about.

**Why now.** The first campaign ran 4.4 h from `k = 10⁶`, found
`a(14)`–`a(17)` of A084700 ([RESULTS.md](RESULTS.md)), and stopped at
06:30 — not on a find but on the engine ceiling `k_ceil(18, +1) =
5.44×10²²`, the deterministic Miller–Rabin bound rearranged for
`61·k + 1`. The model had put `a(18)` under it with 24%. Both items below
were already in this log's "priced and declined" table; the campaign
made them due.

### 1. The ceiling (host side; no fingerprint moves)

- `pladder_search.k_proof(n, s)` is the old formula — the **proof
  crossing**, where the classification stops being a proof — and
  `k_ceil(n, +1) = MR_VALID_BELOW = 3.317×10²⁴` on `k` itself: past the
  crossing a discovery is proved by BLS75 Theorem 1 on
  `N − 1 = prime(i)·k`, and with `k` under the bound every prime factor of
  `k` is a deterministic-MR prime, so the certificate is one level deep
  (huntlib.certificate needs no subproof). A084701's ceiling stays at its
  crossing: its structure is on `N + 1`. 61× more line for A084700; the
  model's `P(a(18))` goes from 24% to **99.4%**.
- `launch.certify_run` factors `k` once (huntlib's bounded trial
  division, rho and ECM, then sympy's `factorint` on any 25-digit
  remainder — the bound `factor_witness` already accepts on the stopper)
  and proves every value on that factorization, **re-verifying each
  proof from scratch** before it is written; `certificates_verified`,
  `unproved` and `proof_routes` land in the evidence file. Measured: the
  first wheel `k` past the crossing factors in 30 ms and proves in under
  a millisecond; a `k` built from two 12-digit primes factors in 0.16 s.
- G10 rewritten (crossing tight to one `k` per `(n, s)`, both ceilings
  pinned); a certificate drill in the selftest (the frontier's 13 values
  by the deterministic route, a value past the bound by Theorem 1,
  re-verified, refused for `N + 2` and as a bare MR claim); one
  `[MILESTONE]` line per filter when the sweep crosses `k_proof`.

### 2. The wheel in unit space (device side; `SCORE`/`SCOREM` re-frozen, `SCORE18` added)

- `killed_residues(q, n, s, unit)` is the set of `k' = k / unit` that `q`
  kills, `unit⁻¹ · K(q, n, s) mod q`; a prime of the unit kills nothing.
  `assert_unit` refuses a unit that is not forced at the filter — the one
  way this could thin the line. The engine's wheels, tables, folds and
  offsets are in `k'`; `self.W`, the survivors and every bound check are
  in `k`; `_collect` is the one place the unit multiplies back in.
- `(..31], (31, 41], (41, 53]` at unit 2310: `W1 = 86,822,723`,
  `W2 = 162,490,421`, device period `1.41×10¹⁶`, period `3.26×10¹⁹` of
  `k` (53 v2 periods). At n = 18: `R = 94,080 × 500 × 28,080`, `nu = 22`,
  1,277 launches of `1.03×10⁹` per period, density `4.05×10⁻⁸` against
  the v2 wheel's `5.97×10⁻⁸` — **1.472× fewer candidates per unit of
  line** (1.359× at n = 14; 1.293× at n = 12, unit 210, where 11 is not
  yet forced). The split had to be this one: `31` must sit in level 1
  (`37·41·43·47·53 = 5.0×10⁹` overflows the u32 second modulus), and
  `(31, 41]/(41, 53]` keeps `R1·R2` under a launch at n = 14.
- Paired on one v2 period at n = 18, before any re-tuning: v2
  `3.583×10¹⁸`, v3 `4.626×10¹⁸` k/s — **1.291×**. Per candidate the
  kernel is 0.877× as fast: the first sieve prime is now 59 killing 16 of
  59 residues instead of 53 killing 17 of 53, so a candidate lives
  longer. The wheel bought 1.47× of density and paid 12% of it back.
- Gates: G7/G8 (unit wheels against the oracle's divisibility on
  `k = unit·k'`, the count formula over the primes not in the unit), G9
  (+8 unit-space parity windows, 21 in all, both units, heights to the
  A084700 ceiling and period 0 clipped), G13/G14 (the production unit
  wheels' constants and tables), G15 (base-shift invariance and residue
  lists with a unit), and **G17**: the unit wheel returns the *identical*
  293 survivors as the v2 wheel over v2 period 88434 at n = 18 — the
  coverage claim the cursor adoption stands on. The canaries rediscover
  `a(8)`, `a(9)` in unit 30; the resume seam is drilled in unit space; an
  adopt drill re-denominates the live v2 cursor (period 88434 of
  `6.15×10¹⁷` → period 1668 of `3.26×10¹⁹`, floored; `1.84×10¹⁹` of
  overlap re-swept as a cross-check, neither counted nor narrated, a
  discovery there an alarm).

### 3. The constants, re-swept on the new wheel (Rule 3a)

n = 18, period 1668 (the live cursor), 200 launches of work per run, 5
interleaved rounds, the fingerprint identical across every variant of
every experiment. Ratios are against the v2 value in the same run.

| constant | v2 | swept | kept | at n = 18 | elsewhere |
|---|---|---|---|---|---|
| `CPT` (candidates per thread) | 32 | 16, 64, 96, 128, 256 | **64** | 16: 1.117; **64: 1.203**; 96/128/256: 0.24/0.20/0.26 | — |
| `SPB` at CPT 64 | 8 | 4, 16, 32, 64 | **16** | 4: 0.884; **16: 1.049**; 32: 1.055; 64: 1.027 | n = 14: 32 → **0.565**, 16 → 0.949; n = 12 (−1): 16 → 1.122 |
| `LIT_SURV` | 0.19 | 0.12, 0.28, 0.40 | **0.28** | 0.12: 0.936; **0.28: 1.045**; 0.40: 0.230 | n = 14: 0.984; n = 12 (−1): **0.848** |
| `K2_SURV` at LIT 0.28 | 0.015 | 0.004, 0.008, 0.011, 0.03 | **0.008** | 0.004: 1.082; **0.008: 1.074** (with LIT); 0.011: 1.064; 0.03: 0.952 | n = 14: 0.997; n = 12 (−1): 0.842 (LIT's cost, not K2's) |
| `R2_SPLITS` | (0.03,) | (), (0.06, 0.03), (0.06, 0.03, 0.015) | keep | (): 0.877; two or three splits: 0.246, 0.261 | — |
| `TAIL_ROUND_DROP` | 0.5 | 0.35, 0.7 | keep | 0.35: 1.003 (a tie; 14 rounds for 21); 0.7: 0.938 | — |
| `TAIL_FILL` | 2¹⁹ | 2¹⁸, 2²⁰ | keep | 0.997, 0.991 | — |
| `CAND_PER_LAUNCH` (nu 22) | 2³⁰ | nu 11, 44 | keep | 0.961, 1.013 | — |
| `UNROLL` | 4 | 2, 8 | keep | 0.999, 1.004 | — |
| `QCAP_SIGMA` | 6 | 3, 10 | keep | 1.004, 1.002 | — |
| `tpb` | 128 | 64, 256 | keep | 0.997, 0.976 | — |

Final, same harness, v3 geometry and constants against v2's on the unit
wheel: **1.358× at n = 18**, 0.933× at n = 14, 0.937× at n = 12 (s = −1;
the geometry alone is 1.123× there and LIT gives it back). With the
wheel's 1.291× that is the 1.70× above.

**The cliffs are one mechanism.** Every 0.2–0.26× result — CPT ≥ 96, a
second or third in-block split, LIT 0.40, and SPB 32 at n = 14 — is
shared memory. The queues are sized from tile × survival and the group
tables from their budget, the kernel is occupancy-bound, and a
configuration that pushes the per-block footprint past a resident-block
threshold loses 4× at once rather than gradually. The cost model would
have said "more candidates per block amortise better"; it was not
consulted as evidence (Rule 3a).

**Two sets of constants, one per wheel family.** Under the unit wheel's
values the k-space shapes fell 20–33% (`SCORE2L` 0.79×, `SCORE1L` 0.77×,
`SCORE10` 0.67×) — constants tuned on one geometry, wrong for the other.
So `CPT/SPB/LIT_SURV/K2_SURV` keep v2's values for `unit = 1` and take
the swept ones for `unit > 1` (`*_UNIT`), and the k-space shapes return
to their v2 numbers.

### What the gates caught

- The resume drill's two-level case built the launcher's new `P1/P2` in
  k space: `W1 = 2.0×10¹¹`, and the u32 ceiling raised as designed.
- The first unit seam engine had `R3 = 17 < nu`: the drill refused a
  seam with no sub-period cursor rather than passing vacuously.
- Three of the first unit-space parity windows were empty at sieve 512;
  G9 refuses a vacuous window, and they were re-sized to sieve 128/64.
- A unit-space G9 window whose period overshot the ceiling by `3×10¹⁰`
  raised the ceiling check (the top windows now sit five periods under
  it, still above 2⁶⁴).

### Priced and declined, or left for the next pass

| candidate | estimate | note |
|---|---|---|
| **`LIT_SURV` per filter** | +15% at the A084701 opening filter (n = 12), where 0.19 beats 0.28 | a survival fraction is not yet a per-configuration optimum; sweep it at n = 12, 14, 16, 18 and store a small table |
| A084701 at unit 2310 from n = 14 | ~1.1× on its line rate once 11 is forced | a mid-campaign re-denomination (`adopt`) — the machinery exists |
| The 1.84×10¹⁹ adopted overlap | 3 s of device | re-swept once as a cross-check; not worth avoiding |
| CRT-combining the tail's first rounds; a second stream for the tail | bounded by the tail's share | unchanged from v2's list |
| `TAIL_ROUND_DROP` 0.35 | a tie at n = 18 with a third fewer tail launches | take it if the tail ever binds; ties go to less machine, but it was not re-measured at n = 14 |
