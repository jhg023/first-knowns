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

## Open, priced, unbuilt

Written down so the next pass starts from evidence (OPTIMIZATION.md Rule 6):

1. **The wheel to 47 at unit 2**, with the window narrowed to 29 periods.
   The candidate saving is exact (1.47×); the window cost is not measured.
   §2.8's second limit says fit `a + b/T` first.
2. **n = 16's occupancy.** G18 reports 4 blocks/SM at n = 16 against 5 at
   the other filters, and 19 KB of shared memory — the queue budget rise
   cost it a block. Worth a paired sweep of `QUEUE_BYTES_MAX` *at that
   filter*, since the optimum need not be shared.
3. **`SURV_TARGET`.** Chosen to land near one core; the device rate is flat
   either side of it, so the real question is what the pipeline does, not
   what the device does. Measure the campaign loop's wall clock per unit of
   line against its device time (OPTIMIZATION.md Rule 1's third paragraph).
4. **The segment-loop wall clock, which nobody has timed.** The benchmark
   measures the engine and the gates measure correctness; neither runs a
   segment. `shift-ladders` lost four fifths of a campaign to exactly that
   blind spot.
