# OPTIMIZATION_LOG — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt, its measurement and its verdict — including the rejects and
the things rejected without implementing, with their prices. The process is
[OPTIMIZATION.md](../OPTIMIZATION.md); the rule that matters most here is
its corollary to Rule 1: **a constant tuned before a structural change is
stale after it**, and this project inherited its engine from a problem whose
wheel is 2,400× stronger, so *every* constant started stale.

All ratios are medians of three interleaved rounds of ten launches each,
paired (OPTIMIZATION.md Rule 3), at the configuration named. Absolute rates
move ~30% with ambient load; the ratio is the stable quantity.

---

## v1 (2026-09-06) — the engine, and what the regime change moved

The engine is `linear-ladders`' v4 window sieve with the multiplier list
swapped from `i` to `L(n)/i`. Everything problem-specific enters through
`killed_residues`, so the kernel needed no mathematical change — but the
*regime* changed completely, and five constants moved with it.

### Measurement 1 — the phase the whole design turns on: the wheel is weak

`w(q,n) = floor(n/q^e)` for q ≤ n against the linear ladders' `min(n, q−1)`.
At n = 15 the wheel to 43 keeps **4.21e-5** of x where theirs keeps 1.3e-10.
Two consequences, both structural:

* the candidate density is 3.2e5× higher, so a given window holds vastly more
  survivors — every gate window and drill span inherited from that project
  was 40–2,400× too wide, and three of them (G9, G17, the resume drill) ran
  for minutes or hours until they were re-sized;
* the singular series is 4,600× larger (1.34e8 against 2.9e4), so terms are
  correspondingly denser in x. What the engine loses in candidates per unit
  of line it gets back in terms per candidate.

**Kept as the design premise.** Nothing to optimize; it is why the rest of
the numbers are what they are.

### Measurement 2 — the window width: 64 → 192, **1.288×** (with the queue)

`PB_BY_C` shipped 64 below c = 16 and 128 above, tuned at the linear
ladders' form counts. Swept at n = 15 of A078502:

| pb | 32 | 64 | 128 | 160 | 192 | 224 | 256 |
|---|---|---|---|---|---|---|---|
| x/s (12 KB queue) | 2.92e16 | 4.17e16 | 5.09e16 | 5.11e16 | **7.09e15** | 7.03e15 | 5.96e15 |

The collapse at 192 looked like a hard cliff and was a **shared-queue
overflow**: a wider window puts more live words in shared memory,
`QUEUE_BYTES_MAX` capped what was left for the queues, `q1cap` fell
1280 → 768, and every block took the in-block fallback — the documented
0.67× failure, worth 7× when it is the rule rather than the exception.

That is OPTIMIZATION.md §2.11 exactly: *a budget that binds on one axis was
silently setting a shape parameter*. Raising the queue budget inverts the
verdict:

| QUEUE_BYTES_MAX at pb = 192 | 12 KB | 20 KB | 28 KB |
|---|---|---|---|
| x/s | 7.07e15 | **5.40e16** | 5.36e16 |

and re-sweeping pb at 20 KB gives 128 → 5.04e16, **192 → 5.37e16 (1.066×)**,
224 → 4.96e16, 256 → 5.00e16. **Kept: PB_DEFAULT = 192, QUEUE_BYTES_MAX =
20 KB.** 20 KB and not more: it is flat once it fits, and shared memory is
what sets blocks per SM.

### Measurement 3 — the sieve depth, which is a LOAD decision

q2 trades device time against host time, and a sweep that measures only
throughput cannot see the second (OPTIMIZATION.md Rule 7). At n = 15,
A078502, pb = 192, with the host cost measured separately at 17 µs per
survivor standalone (12.4 µs inside the pool):

| q2 | 32768 | 65536 | 131072 | 262144 | 1048576 |
|---|---|---|---|---|---|
| x/s | 5.43e16 | 5.44e16 | 5.33e16 | 5.28e16 | 3.84e16 |
| ratio | 1.000 | 1.001 | 0.981 | 0.972 | 0.706 |
| survivors/s | 7.02e5 | 2.69e5 | 1.07e5 | 4.52e4 | 6.66e3 |
| cores needed | 12 | 4.6 | **1.8** | 0.77 | 0.11 |

The device rate is flat over a factor of eight in q2 while the host cost
moves 16×, so "fastest" does not decide this and the load budget does. And
it cannot be a constant: the survivor rate per candidate at a fixed depth
moves an order of magnitude between filters (4.8e-8 at n = 15, 1.3e-8 at
n = 17), because w(q,n) = n for every q above the wheel and n is in the
exponent. A depth tuned at one opening is 4× wrong at the next.

**Kept: `plan_q2`** — the smallest depth whose *analytic* survival is under
`SURV_TARGET = 5e-8`. It picks 131072 at n = 15 (0.981×, 1.8 cores) and
32768 at n = 17, which is that filter's device peak (1.000×, 1.8 cores) —
the same host load at both, which is the point. The analytic survival
matched the measured survivor rate to better than 2% at every opening.

### Measurement 4 — the wheel plan is enumerated, not swept

The feasible three-level splits number in the hundreds, every constraint
(W1 < 2³², W2 < 2³², W1·W2 < 2⁶³, R2/R3 ≤ 65535, and a window worth having
under the 2⁶³ reduction bound) is exact and cheap, and so is the objective
(candidates per unit of line). So `wheel_plan` enumerates. What was *swept*
is the two constants that trade candidate density against window width:
`top` and `PV_MIN`. At n = 15 the plan reaches 43 with a 192-bit window;
reaching 47 would cut candidates 1.47× but caps the window at 29 periods.
At n = 16 the unit is 34, the period is 17× shorter and 47 fits with a full
window — which is why n = 16's line rate is 8× n = 15's and n = 17's.

### The bug the parity gate caught

`off_of` unpacked a queue entry's period index with `qi & (PB - 1)`. That
mask is only correct when PB is a **power of two**; at 192 it is
`0b10111111`, which clears bit 6 of every period index above 63, rebuilds
the candidate at the wrong period, and lets it survive. G9 caught it as
+18 survivors in 2e6 of line at n = 9 the first time a non-power-of-two
window was tried. Fixed to `qi & ((1u << LOGP) - 1u)`; every width from 32
to 256 now reproduces the CPU engine exactly. **The same latent bug is in
`linear-ladders`' engine**, where it is unreachable because 64 and 128 are
the only widths that project runs; its gates were not run (CLAUDE.md rule 2).

### A performance bug found by a gate's wall clock

`plan_q2` materialised `primerange` to the top of its ladder — 1.07 million
primes — on every engine build, about 3 s each, and it is called from
`GpuEngine.__init__`. The families drill took 78 s and was doing nothing.
Fixed by walking the ladder rung by rung and using the closed form
`w_closed(q,n)` (a division) instead of `len(killed_residues(q,n,fam))`
(n modular inversions), which G2b proves equal. Planning all eight campaign
openings now costs **0.15 s** in total, against ~40 s.

### Priced and declined

| candidate | price | verdict |
|---|---|---|
| pb = 160 | +2.3% over 128 at 12 KB queue | superseded by 192 at 20 KB (+6.6%) |
| pb = 224 / 256 at 20 KB | 0.995× / 1.012× | flat; 192 kept, no reason to move |
| QUEUE_BYTES_MAX = 28 KB | 0.994× against 20 KB | costs shared memory for nothing |
| q2 = 32768 at n = 15 | +1.9% device, **+2.8 cores** | declined under the load rule |
| q2 = 1048576 | 0.706× | the sieve stops paying long before the host stops caring |
| wheel to 47 at n = 15 | 1.47× fewer candidates, window 192 → 29 periods | not measured end to end yet — **open, and the first thing to price next** |

---

## Round 2 (2026-09-06) — the phase split, and the thing it was hiding

### Measurement 5 — the phase split, and why the instrumented one lies here

CUDA events between eagerly-issued kernels, at three openings:

| | n = 15 | n = 16 | n = 17 |
|---|---|---|---|
| sieve kernel (window + in-block rounds + extraction) | 84.3% | 87.6% | 90.2% |
| all tail rounds | 15.7% | 12.4% | 9.8% |
| device / wall | 100% | 100% | 100% |

So the sieve kernel is the phase. **But the split cannot be used to choose a
constant**, and that is worth recording because it nearly cost an afternoon.
Instrumenting removes the overlap between a launch's sieve kernel and the
previous launch's tail rounds, so it over-weights the sieve. Sweeping the
window depth `lit` on the INSTRUMENTED path says 40 is 1.116× better than
31; sweeping the same knob on the PRODUCTION path says 31 is the peak and 38
is 0.96×. OPTIMIZATION.md Rule 7's corollary, in this project's own numbers:
**an instrumented path is not the production path.** Every verdict below is
from the production path.

### Measurement 6 — the constants, re-swept at n = 15 (production path)

All at pb = 192, q2 = 131072, three interleaved rounds of 8-10 launches:

| knob | values | best | verdict |
|---|---|---|---|
| `BIT_SURV` (window depth) | .02 / .012 / .0085 / **.007** / .005 / .0035 | .007 | inherited value confirmed; 0.02 is a 15× cliff |
| `lit` directly, k2 fixed | 28 / **31** / 34 / 38 / 42 | 31 | agrees with BIT_SURV |
| `K2_SURV4` (in-block depth) | .003 / .001 / **.0003** / .0001 / 3e-5 | .0003 | inherited confirmed |
| `spb` | 2 / 4 / **8** / 16 / 32 | 8 | 0.83 / 0.95 / 1.00 / 0.12 / 0.08 |
| `tpb` | 64 / **128** / 256 | 128 | 0.76 / 1.00 / 0.14 |
| `R2_DROP` | .7 / **.5** / .35 / .2 | 0.5 | 0.11 / 1.00 / 0.96 / 0.83 |
| `BIT_GROUP_MAX` | **1** / 120 / 600 / 3000 / 15000 | 1 (single primes) | 1.00 / .99 / 1.00 / .94 / .87 |
| `K2_GROUP_MAX4` | **1** / 200 / 2000 | flat | keep 1 |
| `X0_SHARED` | **False** / True | False | 1.00 / 0.79 |
| `PAT_SHARED` | **True** / False | True | 1.00 / 0.94 |
| `EXTRACT_EVERY` at nw = 6 | **1** / 2 / 4 | 1 | 1.00 / 0.95 / 0.83 |
| `QCAP_SIGMA` | 3 / **6** / 10 / 16 | 6 | flat within 1% |
| `ROUND_ILP` | **1** / 2 / 4 | flat | keep 1 |
| `TAIL_TPB` | 128 / **256** / 512 | flat | keep 256 |
| `TAIL_FILL` | 2^17 / **2^19** / 2^21 / 2^23 | flat | keep 2^19 |
| `CARVEOUT_PCT` | 25 / 50 / 75 / **100** | flat within 1.1% | keep pinned |

Two moved, and both are recorded at their constant: **`CAND_PER_LAUNCH4`
2^35 → 2^37** (1.034× at n = 15, 1.082× at n = 17, 1.048× at n = 16) and
**`TAIL_ROUND_DROP` 0.5 → 0.7** (1.014× at n = 15, 1.000× at n = 17).

### Measurement 7 — the deeper wheel, measured at last: **0.646×, declined**

The one candidate the first round left priced but unmeasured. Wheel to 47 at
n = 15 cuts candidates 1.47× — and drops the window from 192 periods to 29,
because `(PV + 1)·W' + q2 < 2^63` and W' goes 6.5e15 → 3.1e17. Measured
paired against the planned (19,31,43): **0.646×**. That is OPTIMIZATION.md
§2.8's second limit exactly — the wheel's benefit and its cost are both
proportional to the same factor, and here they invert. A third split of the
same primes, (23,31,43), reads 0.993×, so the level boundaries themselves
are worth nothing; it is the prime set that matters.

### Measurement 8 — the kernel is NOT occupancy-limited

Both rooflines put the sieve kernel at ~26% (shared-memory bandwidth: 8.2
lane-loads per SM-cycle against ~32; issue: ~25 lane-instructions against
128), so it is latency-bound, and the obvious remedy is more warps. Shared
memory caps it at 5 blocks/SM (19.3 KB × 5 = 96.6 KB of 100) where the 79
registers would allow 6.

**The remedy is measured and it is not there.** `spb = 4` already compiles
to **6** blocks/SM (24 warps against 20) and `spb = 2` also to 6 — and they
measure **0.948× and 0.832×**. More warps with less work each is worse: what
`spb` buys is amortisation of the per-thread x0 loads and the per-block `ne`
across more second-level residues, and that outweighs occupancy over the
whole range. So the 3.2 KB of shared memory a three-byte queue entry would
save (u16 index + u8 period instead of u32) is **not worth building**: it
buys the block per SM that spb = 4 already proves is not the constraint.

### Measurement 9 — THE ONE THAT MATTERED: 34 ms per launch off-device

CONVENTIONS.md's "measure WALL CLOCK per unit of line alongside device and
host, in the segment loop" — the measurement a benchmark and a gate both
structurally cannot make. Timing the campaign's own per-launch methods
against a scratch checkpoint:

| | before | after |
|---|---|---|
| `check_rungs` (per launch) | 2.9 µs | 2.7 µs |
| `ladder()` | 0.9 µs | 0.9 µs |
| `state()` | **33,214 µs** | 3.4 µs |
| `mark_boundary` (per launch) | **34,105 µs** | 2.5 µs |
| `save()` (rate-limited) | 34,316 µs | 914 µs |
| one launch of device | 56 ms | 56 ms |
| **per-launch off-device work** | **~60% of a launch** | **0.01%** |

`x_floor` called `plan_for`, which enumerates every admissible three-level
wheel split and walks the sieve primes: 33 ms, a pure function of (family,
filter), called from `k_min` every segment and from `state` every launch.
The tell is the one shift-ladders left — an absolute per-launch constant
that does not scale with the work — and the fix is the same one:
`functools.lru_cache` on `plan_for` and `x_floor` (and on `wheel_plan` and
`plan_q2` inside the engine, which also cheapens every gate that builds an
engine). **13,600× on that call, and it would never have appeared in a SCORE
or a gate.** This is why Rule 1's third paragraph is in the process.

### Round 2 result

44/44 green. SCORE 52,652 → **53,408**; SCORE16 305,119 → **309,337**;
SCORE9 6.46 → **6.95** — the benchmark sees only the tail-round change,
because the shapes pin `nu` (score.py says why). The campaign sees all of
it: the off-device work per launch went from ~60% of a launch to 0.01%.

---

## Round 3 (2026-09-06) — occupancy, correctly this time

### Measurement 10 — the padding ablation: occupancy DOES matter

Round 2 concluded from the `spb` sweep that the kernel is not
occupancy-limited. **That conclusion was wrong**, and it was wrong for the
reason OPTIMIZATION.md 3.3 warns about: `spb` changes two things at once
(blocks per SM *and* how much per-thread setup is amortised), so it is not
an ablation.

The ablation that changes one thing is a **dummy shared array**, written and
read so the compiler cannot remove it, whose only effect is to lower blocks
per SM. Identical instruction mix, identical work, identical results:

| pad (words) | 0 | 1024 | 2048 | 3072 | 4096 | 6144 |
|---|---|---|---|---|---|---|
| shared | 19,328 | 23,424 | 27,520 | 31,616 | 35,712 | 43,904 |
| blocks/SM | 5 | 4 | 3 | 3 | 2 | 2 |
| ratio | **1.000** | 0.920 | 0.820 | 0.815 | 0.589 | 0.589 |

The rate tracks blocks per SM almost linearly. **A block is worth about
8%.** Both facts stand together: occupancy matters, *and* `spb = 4` is still
slower than `spb = 8` despite having one more block, because the
amortisation it loses is worth more than the block it gains.

### Measurement 11 — the queue margin was spending a block, at n = 16

The queues are two thirds of this kernel's shared memory, and `QCAP_SIGMA`
sets them. At n = 16 the inherited 6.0 put the footprint at 20,044 bytes —
just over the line — for **4** blocks per SM where 5 were available:

| `qcap_sigma` at n = 16 | 1.5 | 2.0 | 2.5 | 3.0 | 6.0 |
|---|---|---|---|---|---|
| shared / blocks per SM | 17,740 / 5 | 18,124 / 5 | 18,380 / 5 | 18,508 / 5 | 20,044 / 4 |
| x/s | 2.86e17 | 3.23e17 | 3.46e17 | **3.46e17** | 3.23e17 |
| ratio | 0.825 | 0.933 | 0.999 | **1.000** | 0.933 |

Both ends are real: 6.0 costs the block, and 1.5 costs more than the block
is worth because the queues then genuinely overflow and the in-block
fallback becomes the rule rather than the exception.

**Kept: the margin chooses itself.** `_pick_sigma` computes the analytic
shared footprint (accurate to ~70 bytes against what the compiler reports,
checked at four filters) for each margin in a ladder and takes the LARGEST
margin that still reaches the best blocks-per-SM any of them reaches. It
picks 5.0 at n = 15 and 16, 6.0 at n = 17 and 18, 3.0 at n = 19 — and every
campaign configuration now compiles to 5 blocks per SM (7 at n = 19, where
registers cap it), which is why `OCC_MIN_BLOCKS4` went from 4 to 5. This is
OPTIMIZATION.md 2.11 for the third time in this project: a budget that binds
on one axis was silently setting a shape parameter.

### Measurement 12 — `sal` in registers: 16.3 KB of shared, 242 registers, **declined**

The other three kilobytes of shared are `sal`, the per-thread buffer of live
window words between the sieve loop and the extraction loop. Every access is
the thread's OWN slot, so with `EXTRACT_EVERY == 1` it does not need to be
shared at all — and reusing `acc` for it (dead by then) costs no extra
registers in principle.

In practice the compiler responds by keeping the whole 31-group load chain
live: **242 registers, 2 blocks per SM**, against 79 and 5. Shared did fall
to 16,256 bytes as predicted, which would have been the 6th block. Variants
tried: a separate local array (same 242), hoisting `acc` out of the residue
loop (same), `#pragma unroll 1` on the residue loop (same),
`__launch_bounds__` (168 registers and 368 bytes spilled to local). Reverted.

The lesson for the next attempt: the 3 KB is worth a block and the block is
worth 8%, but it has to come out of the QUEUES (a three-byte entry — u16
index plus u8 period — would save 3.2 KB and never touches the inner loop's
register allocation), not out of `sal`.

### Round 3 result

44/44 green. SCORE 53,408 → **53,664**; **SCORE16 309,337 → 336,231
(1.087×)**, which is the n = 16 block; SCORE17 38,219 → 38,135.

Device rate at the four campaign openings, against the untuned engine this
project started from:

| filter | start | now | ratio |
|---|---|---|---|
| n = 15 | 4.179e16 | 5.632e16 | **1.348×** |
| n = 16 | 3.131e17 | 3.451e17 | 1.102× |
| n = 17 | 3.740e16 | 4.082e16 | 1.091× |
| n = 18 | 3.885e17 | 4.338e17 | 1.117× |

and the campaign gets, on top of that, the 34 ms per launch that round 2
took off the segment loop.

---

## Round 4 (2026-09-06) - the three-byte queue entry, and a bound that is not the one you think

### Measurement 13 - the queue entry: 4 bytes to 3, **6 blocks per SM everywhere**

Round 3's best-priced unbuilt item, built. The entry packs
`(ss*TPB + tid) << LOGP | j` -- 18 bits at spb = 8, tpb = 128, pb = 192 --
so it had been a u32, and the queues were two thirds of this kernel's shared
memory. Split across an `unsigned short` index array and an `unsigned char`
period array it is three bytes; the PACKED form is rebuilt on read, so
`off_of`, the round tests and everything downstream are untouched, and only
the declaration, the two pushes and the reads change.

| | before | after |
|---|---|---|
| shared, n = 15 | 18,944 | **15,520** |
| blocks/SM, n = 15..18 | 5 | **6** |
| registers | 79 | 79 (no spills) |

| filter | before | after | ratio |
|---|---|---|---|
| n = 15 | 5.632e16 | 5.621e16 | 0.998x |
| n = 16 | 3.451e17 | 3.513e17 | 1.018x |
| n = 17 | 4.082e16 | 4.259e16 | **1.043x** |
| n = 18 | 4.338e17 | 4.456e17 | 1.027x |

Less than the ~8% the padding ablation put on a block, and that is the
honest reading: the marginal block returns less than the ones below it, and
the extra shared access per push and pop eats some of what is left. Kept
anyway -- it is 1.043x at the filter that costs the night's time, free at
the others, and it leaves 3.4 KB of headroom for anything later that wants
shared memory. **SCORE17 38,135 to 40,679 (1.067x).**

### Measurement 14 - lifting the 2^63 reduction bound: **declined, and not for the reason expected**

The wheel is capped by `(PV + 1)*W' + q2 < 2^63`, the bound on the offset the
Barrett tail reduces. Reducing `off_p` (within a period, < W') and
`p*(W' mod q)` (< 192*q < 2.5e7) separately would bound it by W' alone, and
the wheel could reach 47 at n = 17 -- 1.567x fewer candidates -- with the
window still 192 periods. The engine even already carries the `W' mod q`
table (`_wmod`), and the absolute launch base is already folded per prime.

**There is a second bound, and it binds first.** The survivor buffer holds
the offset within the launch as a **u64**, and `_collect` adds the launch
base on the host. With wheel-47 at unit 2, W' = 3.07e17 and a 192-period
segment, that offset reaches 5.9e19 -- past 2^64, never mind 2^63. So the
reduction bound is not what caps the wheel here; the emitted offset is, and
lifting it means changing the survivor format, the pinned readback,
PRE_COPY and `_collect` as well. Priced at ~1.35x **at n = 17 and 18 only**
(n = 15 and 16 would not take the wheel anyway -- there one wheel-47 period
is 6.15e17 against a modelled median of 1.18e17, so the over-sweep would
exceed the search), and declined against that scope.

Worth writing down precisely because the first bound is the one the code
documents and the second is the one that decides.

### Measurement 15 - the constants re-swept at n = 17 (rule 5g)

`pb`: 128/160/192/224/256 read 1.000/1.012/**1.041**/0.976/0.968 -- 192
confirmed at the expensive filter as well as at the opening. `BIT_SURV`:
0.012 is a 6.8x cliff, 0.007 and 0.004 tie, 0.002 is 0.87x. `spb`: 4/8/16
read 1.000/**1.026**/0.175. No constant moves.

### Round 4 result

44/44 green in 222 s. SCORE **54,030**; SCOREP 54,054; SCORE16 **337,058**;
SCORE17 **40,679**; SCORE2L 21,093; SCORE1L 4,858; SCORE9 6.8.

Device rate at the four campaign openings against the untuned engine:

| filter | start | now | ratio |
|---|---|---|---|
| n = 15 | 4.179e16 | 5.621e16 | **1.345x** |
| n = 16 | 3.131e17 | 3.513e17 | 1.122x |
| n = 17 | 3.740e16 | 4.259e16 | **1.139x** |
| n = 18 | 3.885e17 | 4.456e17 | 1.147x |

---

## Round 5 (2026-09-06) - two negatives and one property made explicit

### Measurement 16 - splitting the accumulator chain: **0.998x, declined**

Every window group ORs into `acc[i]`, so `acc[i]` carries a dependency chain
as long as the group count -- 31 at n = 15, six of them, one per window word.
Interleaving them into NACC independent chains and combining once at the end
shortens that critical path by NACC, at (NACC - 1) * NW more registers.

First read, without a register budget: NACC = 1/2/3/4 gives 1.000 / 0.998 /
0.980 / 0.924, and NACC = 2 costs a block per SM (79 registers to 82, which
rounds to 88 and loses the 6th block). That looked like "the ILP gained ~8%
and the block lost ~8%", so the experiment was repeated **at equal
occupancy** with `__launch_bounds__(TPB, 6)`, which fits NACC = 2 in 80
registers with no spills and 6 blocks per SM:

| NACC | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| at 6 blocks/SM | **1.000** | 0.998 | 0.990 | 0.976 |

So the accumulator chain is **not** the critical path, the first reading was
a coincidence, and there is nothing here. Reverted, including the
`__launch_bounds__` knob it needed -- a dead knob in the tree is worse than
a line in this file.

It also prices the 6th block honestly: NACC = 2 measured the same at 5
blocks and at 6. The padding ablation's ~8% per block is the slope at 4-5,
not at 5-6, and Measurement 13 (0.998x to 1.043x for the block) is the
truth at the top.

### Measurement 17 - the period against the search, now asserted

The wheel plan maximises candidate density, and a denser wheel is a LONGER
period. But a period's candidates come out in (t, s, u, j) order, so a find
is only known to be the LEAST once its period closes (CONVENTIONS.md "Two
cursors"): a find costs up to one period of over-sweep. A plan whose period
approached the search would spend more on that than the density bought --
which is the trade square-ladders rejected a wheel for, and re-priced two
terms later when the same period had become 0.13% of the hunt.

Measured at every filter both families can run:

| filter | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|
| period (x) | 1.31e16 | 6.15e17 | 1.31e16 | 6.15e17 | 6.15e17 | 6.15e17 |
| periods to the modelled median | **9.0** | 34.6 | 7,093 | 46,939 | 141,938 | 2.4e7 |

The tightest is n = 15 at 9.0 (11.1 for A074200), so the plan is safe
everywhere -- but it was safe by luck, not by design, and nothing checked
it. `_families_stay_apart` now asserts a **4x margin** at every filter of
both families and names the tightest one in its message. Checked and not
enforced on purpose: a plan that failed it is a decision for a human, not
something for the planner to route around silently.

This is also the honest reason wheel-47 is wrong at n = 15 -- one such
period is 6.15e17 against a median of 1.18e17, so the over-sweep would
exceed the search -- independent of the two numeric bounds that also
forbid it (Measurement 14).

### Round 5 result

44/44 green in 185 s. No engine change, so the fingerprints and the SCORE
row are round 4's.

---

## Round 6 (2026-09-06) - THE WHEEL IS A SUBSET, NOT A PREFIX

### Measurement 18 - the biggest win of the project: **1.49x at n = 17**

Every prime in the wheel multiplies the PERIOD by q and the candidate
density by keep(q) = (q - w(q,n))/q. In every other ladder in this
repository those two move together, because w(q,n) = min(n, q-1) makes the
small primes maximal killers. **Here they are wildly out of step**, because
w(q,n) = floor(n/q^e) makes them nearly blind. At n = 17:

| q | 11 | 13 | 17 | 19 | 47 | 53 |
|---|---|---|---|---|---|---|
| keep(q) | 0.909 | 0.923 | 0.941 | **0.105** | 0.638 | 0.679 |

11, 13 and 17 kill under a tenth of the line between them and cost a factor
of **2,431** in period; 47 and 53 kill a third each for a factor of 2,491.
A PREFIX wheel cannot make that trade -- to reach 19 it must take 11, 13 and
17, and the period bound then stops it before 47. So the planner now chooses
a **SUBSET** by value density, -log(keep(q)) / log(q), taken greedily while
the period fits every bound; the sieve primes are the COMPLEMENT rather than
a tail, which is the one place this could have silently thinned the line and
is why `self.primes` is now a set difference.

Candidates per unit of line, planned subset against the prefix it replaced:

| filter | 15 | 16 | 17 | 18 |
|---|---|---|---|---|
| prefix | 4.212e-5 | 7.023e-6 | 7.385e-5 | 7.073e-6 |
| subset | 3.417e-5 | 5.843e-6 | **4.054e-5** | **4.110e-6** |
| fewer candidates | 1.23x | 1.20x | **1.82x** | **1.72x** |

and end to end, measured paired at the campaign's own configuration:

| filter | before | after | ratio |
|---|---|---|---|
| n = 15 | 5.621e16 | 5.771e16 | 1.027x |
| n = 16 | 3.513e17 | 3.730e17 | 1.062x |
| n = 17 | 4.259e16 | **6.348e16** | **1.490x** |
| n = 18 | 4.456e17 | **6.449e17** | **1.447x** |

The candidate rate falls (2.57e12 against 3.15e12 at n = 17, 0.82x: bigger
wheel tables, more first-level residues) and the density gain more than
pays for it. n = 15 gains least because its period cap binds: the modelled
median there is only nine periods into the old wheel, so the planner is not
allowed to take the long one (Measurement 17), and `search_period_cap`
enforces exactly that -- the model's median for the term, divided by the
4x margin, passed into the plan.

This is rule 5c in one measurement: **the biggest lever was never the
kernel.** Six rounds of kernel tuning bought 1.35x at n = 15 and 1.14x at
n = 17 between them; one change to which primes the sieve asks for bought
1.49x at n = 17 by itself.

### The benchmark shapes were re-frozen, deliberately

The four CAMPAIGN shapes named prefix wheels the campaign no longer runs, so
a score against them had stopped measuring the hunt (OPTIMIZATION.md 2.13:
the benchmark shape becoming the blocker). They were re-frozen at the
planned subset wheels, and `score.py` says so. **SCORE2L, SCORE1L and
SCORE9 were NOT touched** -- they are x-space shapes over whole wheel
periods, the same candidates whatever sweeps them, and they are the anchor
across this change. They read 21,152 / 4,865 / 6.8 before and after.

SCORE 54,288 -> **55,995**; SCORE16 336,674 -> **364,682**; SCORE17
40,688 -> **62,510**.

### Round 6 result: the project against the engine it started from

| filter | untuned | now | ratio |
|---|---|---|---|
| n = 15 | 4.179e16 | 5.771e16 | **1.381x** |
| n = 16 | 3.131e17 | 3.730e17 | 1.191x |
| n = 17 | 3.740e16 | 6.348e16 | **1.697x** |
| n = 18 | 3.885e17 | 6.449e17 | **1.660x** |

plus the 34 ms per launch that round 2 took off the segment loop, which is
worth more than all of it at the openings and appears in no benchmark.

44/44 green in 195 s.

---

## Round 7 (2026-09-06) - the constants, re-swept after the wheel changed

Rule 1's corollary, applied on purpose: **round 6's subset wheel is a
structural change, so every constant tuned before it is stale after it.**
Re-swept at the campaign's own new configuration.

| knob | n = 15 | n = 16 | n = 17 | verdict |
|---|---|---|---|---|
| `pb` 128 | -- | -- | 1.000 | |
| `pb` 160 | -- | -- | 1.061 | |
| `pb` 192 | 1.000 | 1.000 | 1.102 | the old optimum |
| **`pb` 224** | **1.008** | **1.013** | **1.125** | **moved here** |
| `pb` 256 | 0.976 | 0.881 | 1.123 | falls off at two filters |
| `BIT_SURV` .012 / .007 / .004 / .002 | -- | -- | 0.87 / **1.00** / 0.96 / 0.84 | unchanged |
| `CAND_PER_LAUNCH4` 2^35 / 2^37 / 2^38 | -- | -- | 1.000 / 1.044 / 1.051 | 2^37 kept: 2^38 is +0.7% for +500 MB |

So one constant moved, `pb` 192 -> 224, worth 1.008x / 1.013x / 1.021x. It
costs the 6th block per SM (a wider window is more shared memory), and the
measurements above are net of that -- which is the honest way to read it,
and consistent with round 5's finding that the 6th block is worth little.

**And the score shapes now pin `pb` as well as `nu`.** They already had to
pin `nu` because a shape denominated in third-level residues moves when the
launch decomposition does; `pb` sets the segment width and does exactly the
same thing, and this sweep would have taken all seven fingerprints with it.
Pinned at 192, where they were frozen; the campaign runs the planner's 224.
`score.py` says so.

### The project's final state against the engine it started from

| filter | untuned | now | ratio | median | device to the median |
|---|---|---|---|---|---|
| n = 15 | 4.179e16 | **5.934e16** | 1.420x | 1.18e17 | 2.0 s |
| n = 16 | 3.131e17 | **3.848e17** | 1.229x | 2.13e19 | 55 s |
| n = 17 | 3.740e16 | **6.561e16** | **1.754x** | 9.28e19 | 23.6 min |
| n = 18 | 3.885e17 | **6.745e17** | **1.736x** | 2.89e22 | 11.9 h |

Both families to a(17) is about 51 minutes of device at the medians and
about 2.1 hours at the 2.5x the repo's optimism factor suggests budgeting
-- against 3.6 hours for the same work on the engine as inherited, and
that is before the 34 ms per launch round 2 took off the segment loop,
which no benchmark here can see.

---

## Open, priced, unbuilt

Written down so the next pass starts from evidence (OPTIMIZATION.md Rule 6):

1. **A wider survivor record**, which is what actually caps the wheel
   (Measurement 14). The emitted offset is a u64 within the launch, so the
   launch span is bounded by 2^64 whatever the reduction does; a `uint2` or
   a per-period record would lift that, and only then does splitting the
   Barrett input buy the wheel-47 that is worth ~1.35x at n = 17 and n = 18.
   Scope: the survivor buffer, the pinned readback, PRE_COPY, `_collect`,
   and what G9 and G15 expect of the stream's units. **The biggest single
   number still on the table, and the biggest change.** n = 15 and 16 would
   not take that wheel in any case: there one wheel-47 period (6.15e17) is
   five times the modelled median (1.18e17), so the over-sweep a find costs
   would exceed the search.
2. **More ILP inside a thread.** The kernel is latency-bound (both rooflines
   at ~26%) and occupancy is now at the shared-memory limit with 6 blocks
   per SM, so the next axis is independent work per thread -- two
   first-level residues per thread, doubling the accumulator chains.
   Measurement 12 is the warning about what the register allocator does when
   asked to keep more live across the group chain.
3. **`SURV_TARGET`.** Chosen so the host need lands near one core; the
   device rate is flat either side of it. The real question is what the
   PIPELINE does rather than what the device does, and that needs a hunt --
   the first `[STATUS]` lines of a real campaign will answer it, and the
   waited-fraction field is there to be read.
4. **A 64-bit pattern word.** At pb = 192 the window is NW = 6 32-bit words:
   7 shared loads and 6 funnel shifts per prime per 192 candidates. In
   64-bit it would be 4 loads and 3 two-instruction funnel shifts. The
   engine this came from measured 32-bit better, but at NW = 2, where the
   trade is 3 loads against 2. Priced at ~1.1x best case on a phase worth
   85%; unbuilt because it is a rewrite of the dominant kernel's inner loop
   and the information-efficiency argument says the loads cannot fall much:
   217 loads carry 6,944 bits to produce 5,952 bits of kill information per
   (t, s), which is 94% efficient.
5. **The host classifier.** 12.4 us per survivor, and the campaign is
   device-bound at every filter with a pool of 3, so this is worth nothing
   today. It becomes the binding side only if the device gets ~4x faster.
