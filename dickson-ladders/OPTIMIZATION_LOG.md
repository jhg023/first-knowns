# OPTIMIZATION_LOG -- dickson-ladders (attempt -> measurement -> verdict)

Benchmark shapes and the fingerprint convention: see BENCHMARKS.md.
Process rules: [../OPTIMIZATION.md](../OPTIMIZATION.md). The two that
bind hardest here, because the sibling project paid for both:

- **Measure the phase split before touching anything.** A fast kernel
  moves the bottleneck; it does not remove it.
- **Never treat the cost model as evidence.** It has mispredicted by 4x
  in both directions in this repository, and it mispredicted by 2.4x in
  the first entry below.

## v1 (2026-08-18): the engine as built

One kernel, one thread per candidate j, all primes from n+2 to 65536 in
one loop with an early exit on the first kill. Barrett magic-multiply
(huntlib/gpu.py) for every reduction; no residue table on the device; no
compaction stage; no bit-sieve.

| shape | rate | candidates/s |
|-------|------|--------------|
| `SCORE` (n = 10, wheel 2310) | 6.54e12 k/s | 2.83e9 |
| `SCORE12` (n = 12, wheel 30030) | 8.78e13 k/s | 2.93e9 |

Candidate throughput is flat across filters, so the entire 13x spread in
line rate is the wheel. On this problem the wheel is the lever and the
instruction count is not -- the opposite of the ordering that held in the
sibling project, and worth knowing before optimizing the wrong thing.

### Measured: preallocate the survivor queue -- 1.06x, KEPT

The first version allocated a 32 MB device buffer per launch. Removing
that was predicted "~2.5x" from a first reading that had actually
measured a different span; the honest paired measurement is **1.06x**
(2.65e9 -> 2.83e9 candidates/s). Kept -- it is free and it is real -- but
logged at its true size, because the 2.5x was a cost-model guess dressed
up as a memory of a measurement. That is exactly the failure mode
../OPTIMIZATION.md warns about, committed on this project's first day.

### Phase split, measured before any tuning

On a 2^26-candidate window at n = 10 (23 survivors):

| phase | cost |
|-------|------|
| GPU sieve | 24 ms |
| host classification of survivors | 1.5 ms (67 us x 23) |

Host share **~6%** at v1 speed, and the survivor density is 2.75e-7 per
candidate at n = 10 -- so a 10x faster kernel would put the host at ~40%.
The sibling project discovered that curve at 52% by surprise; here it is
written down on day one, with the trigger stated: **if the kernel gains
more than ~4x, parallelize the host classification before chasing the
next kernel win.** 61% of survivors die on the first value (m = 1) and
the mean chain is 1.65 tests, so the cheap-first ordering is already in
place.

## v2 (2026-08-18): bit-sieve + geometric compaction + warp-per-candidate tail

Measured before touching anything (Rule 1), on top of the v1 split above:
mean exit depth 1.57 primes vs warp-max 8.6 -- a **5.5x divergence tax**
at n = 10 (4.9x at n = 12), from the exact w_q. The v1 kernel spends
most of its issue slots on lanes that died on the first prime.

Restructure, gated by G6/G13/G14 and a new G15 (v2 == v1 bit for bit on
populated windows at n = 10 and 12):

| step | change | measured |
|------|--------|----------|
| 1 | **stage 1a bit-sieve** (NS = 32 primes as one 64-bit kill pattern per (q, j mod q), one residue register per prime, T = 64 blocks per thread) + one-shot stage 1b over the remaining ~6500 primes | **15.5x / 15.3x** paired vs v1; split flips to 1a 1.3 ms (1%), 1b 82 ms (90%) per 2^32 window |
| 2 | fixed 32-prime compaction rounds (204 rounds) | **0.85x** vs one-shot: 3,280 launches per window; a 4096-block grid costs 0.27 ms even empty. REJECTED |
| 3 | **geometric rounds** (a round ends when survival within it halves; 11 rounds), grids sized from the analytic survival | 1b 82 -> 65 ms; but rounds 8-10 (2-8k candidates each walking 1-3k primes) took 9/19/25 ms at <1 M lane-tests/ms: **latency-bound**, one dependent 64-bit chain per lane and a near-empty GPU |
| 4 | LAUNCH 2^28 -> 2^30 (4x the population per round) | 1b 65 -> 16 ms; **1.95x / 2.34x** paired (2^29: 1.57x; 2^31: 2.15x/2.52x; 2^32: 2.40x/2.82x but that is one launch per frozen window -- Rule 4 -- and its spread is 2x) |
| 5 | **warp-per-candidate kernel for the sparse rounds** (expected population < 2^16 per launch: lanes split the primes, `__any_sync` every 4 iterations) | tail rounds 2.4/4.4/6.2 ms -> 0.29/0.15/0.21 ms; 1b 16 -> 2.5 ms per window |
| 6 | host-side sort of the final survivors instead of `cp.sort` on a ~300-element array | readback 6.0 -> 0.7 ms per window |

**Paired totals (5 rounds, one process, fingerprints re-checked on every
run): v2/v1 = 289x on `SCORE` (min 283, max 303) and 314x on `SCORE12`
(min 294, max 357).** Both fingerprints reproduce.

Phase split after step 6, per 2^32 window at n = 10 (LAUNCH 2^30):
1a 1.4 ms (23%), 1b 2.5 ms (43%), readback 0.7 ms (12%), Python launch
overhead ~1.3 ms (22%) -- 6.0 ms of GPU-side wall against **~70 ms of
host classification** for the window's 1,213 survivors at 58 us each.
The trigger written down in the v1 entry (host parallel before the next
kernel win once the kernel gains 4x) fired at 15x and is now overdue by
an order of magnitude: the host is ~92% of end-to-end wall.

## v2, second pass (2026-08-18): host pipeline, bit-probe 1b, re-sweeps, launch plumbing

The v1 trigger fired, so the host went first.

### Host classification in a process pool -- KEPT

`launch.py` classifies segment i-1 in a `ProcessPoolExecutor` while the
device sieves segment i; results are consumed in ascending order in the
parent and the cursor advances only past a fully classified segment (the
least-claim ordering is untouched). Measured on a 2e15-k segment at n = 10
(v2 step-6 kernel, 237,711 survivors): serial host 18.4x the GPU time;
pooled, host/GPU 1.34 (16 workers), 0.77 (32), 0.69 (48), 0.61 (60) on 32
physical cores; pipelined 3 segments 3.9 s against 3.0 s GPU-only. A
`pool drill` in the selftest pins pooled == serial, in order.

### The 2^32 shapes stopped resolving changes -- SCORE13 added

At v2 speed a 2^32 window is one to four launches and ~1-5 ms; identical
configurations read 0.5x-2.3x against each other on it. Per Rule 4 and
OPTIMIZATION.md 2.13 the frozen shapes were not touched: a third shape,
`SCORE13` (n = 13, wheel 30030, j in [7e16, +2^38), k ~ 2.1e21 = the
model's a(13) median, 16-64 launches wide), was frozen from v2 (2,739
survivors, xor 70000110051605722) and cross-checked bit-for-bit against
v1 (56 s at v1 speed). Every verdict below is on SCORE13 unless stated.

### The ledger (paired, interleaved, one process, fingerprint every run)

| # | change | ratio | verdict |
|---|--------|-------|---------|
| 7 | RATIO 2 -> 4 (rounds end when survival falls 4x; 14 -> 8 rounds) | **1.097x** (3: 1.089, 6: 1.093, 1.5: 0.93) | KEPT |
| 8 | warp-round vote every 4 -> every 1 prime | **1.039x** (2: 1.003, 8: 1.005, 16: 0.999) | KEPT |
| 9 | warp_pop 2^16 vs 2^14 / 2^18 / 2^20 / all-warp | 1.006 / 0.981 / 0.984 / 0.985 | flat, kept 2^16 |
| 10 | LAUNCH 2^30 -> 2^33 (SCORE13: 2^28 0.42, 2^29 0.67, 2^31 1.19, 2^32 1.40, 2^33 **1.45**) | **1.45x** | KEPT; fit gives ~0.31 ms fixed cost per launch against 5.3e-13 s per candidate |
| 11 | NS at LAUNCH 2^33, walk-1b: 24 vs 32 **1.040x** (16: 0.80, 40: 0.90, 48: 0.80, 64: 0.54) | 1.040x | KEPT NS 24 (then superseded by #15) |
| 12 | T 64 vs 16/32/128/256/512 at NS 24 | 1.02 / 1.02 / 1.00 / 1.01 / 1.03, min/max straddle 1.0 | flat at that balance |
| 13 | **stage 1b test = one Barrett + one probe of the device-built kill-bit table** instead of three Barretts + an n-step walk | **1.439x** (1b 65.6 -> 15.9 ms per window; dense rounds 58 -> 400-520 M lane-tests/ms) | KEPT; the walk survives only in the v1 parity kernel |
| 14 | bits below q < 1000/2048/4096/16384/all, walk above (deep rounds probe a 24 MB L2-resident table) | 1.004 / 0.999 / 0.997 / 1.006 | flat within 1%: bits everywhere, walk removed from 1b |
| 15 | NS re-sweep after #13: 16 vs 24 **1.115x** (min 1.086); 18: 1.094, 20: 1.067, 22: 1.053; 14: 0.92, 12: 0.79, 10: 0.65 (relative to 16) | **1.115x** | KEPT: the optimum moved 24 -> 16 because 1b got 4x cheaper -- Rule 1's corollary |
| 16 | NS at n = 10 (2^38 window, parity only): 20 vs 16 1.095x, 24 1.056x | split verdict | NS is now DERIVED from a stage-1a survival target (1.2e-3 -> 16 primes at n = 13, 23 at n = 10, capped at 32) |
| 17 | RATIO re-sweep after #13: 3/6/8 vs 4 -> 1.004 / 0.994 / 0.956 | flat | 4 stays |
| 18 | T at NS 16: 128/256/512/1024 vs 64 -> 1.009 / 1.049 / 1.055 / **1.082**; kernel-only 16/64/256/1024 -> 1.70/1.61/1.54/1.50 ms | **~1.08x** | KEPT as a DERIVATION: T = largest value <= 1024 keeping 4 blocks per SM, so small windows stay full |
| 19 | CUDA-graph replay of the whole chain (stage-1a scalars moved to a device args buffer) | **1.017x** alone (0.98 min, 1.05 max) | KEPT (needed by #20: with double-buffering eager launches measured 0.889x) |
| 20 | **double-buffered launches**: two slots (stream, queues, counters, args), chain i+1 enqueued before chain i is read back | **1.085x** vs serial (min 1.065) | KEPT; the per-launch sync bubble was the "unaccounted 10 ms + readback 5 ms" of the split |
| 21 | LAUNCH 2^33 -> 2^34 with double-buffering (2^32: 0.906) | **1.076x** (min 1.059) | KEPT; ~760 MB of queues per engine at n = 13 |

**Paired totals v2-final / v1: SCORE13 913x (min 627, max 915; 3
rounds, v1 takes 56 s per pass); SCORE 464x (449-542) and SCORE12 551x
(399-640) -- those two are single-launch windows for v2 and their spread
says so.** All three fingerprints reproduce.

### Ablations and rejects (measured, with the number)

| attempt | measured | why it lost / what it taught |
|---------|----------|------------------------------|
| fixed 32-prime rounds (204 rounds) | 0.85x vs one-shot | 3,280 launches per window; an empty 4096-block round costs 0.27 ms |
| walk-per-round in stage 1b vs bit probe (#13) | 0.69x | the walk is 3 Barretts + n dependent adds per test |
| stage-1a table PADDED 2x/4x/8x/16x (same load count, same results) | 1.51x / 2.6x / 4.7x / 14x SLOWER | the footprint cliff is steep from 12 KB up -- so NS_MAX = 32 and no CRT-combined tables beyond a pair |
| stage-1a marched table (rows in block-visit order, lanes take consecutive blocks: every warp-load coalesced) | 1.10x SLOWER, correct on full and ragged launches | the gathers were never the limit; the sibling's 1.019x did not transfer |
| stage-1a no-load ablation (data-dependent shift/not/or in place of the gather) | 0.745x of the time | loads are ~25% of 1a: the kernel is ~75% issue/ALU, the opposite of the sibling |
| stage-1a register-counter ablation (no atomics, no stores) | 0.877x | the push is 12% of 1a |
| stage-1a no-extraction ablation | 0.788x | extraction + push together 21% |
| **warp-aggregated push** (ballot + shuffle scan + one atomic per warp per block) | **1.64x SLOWER** | ~2.4 survivors per warp-block; the divergent 2-3 iteration loop is cheaper than a 15-instruction uniform scan |
| `#pragma unroll 2` / `unroll 4` on the block loop | 1.07x / 3.0x SLOWER | runtime trip count -> remainder loop, register growth |
| byte-prescaled residues; min-trick conditional subtract | 1.000 / 0.996 | the compiler already emits that |
| `__launch_bounds__(256, 3)` / (256, 4) | 1.002 / 1.020 (min < 1) | flat; 62 regs = 4 blocks/SM already |
| CRT pair rows (17x19 -> 323 entries; +23x29 -> 667) replacing 2 / 4 primes | 0.92x / 1.00 kernel time, min/max 0.85-1.15 | ~5% end-to-end at best on a day the noise floor was 15%; PRICED, not taken -- worth 15+ rounds when the machine is quiet |
| hoisting K of NS primes to measure the per-prime slope | contaminated | hoisted patterns concentrate survivors in 7% of threads and the extraction loop's imbalance dominates -- Rule 3.3: the ablation changed the work distribution |
| deeper sieve (q2 262144) for the n = 10 leg, where the host binds at 2.2x GPU | ~1.9x on that leg by arithmetic; DECLINED | the a(10)/a(11) legs are under three minutes end-to-end at the current rate; at n = 13 (the campaign) the host is 18% of GPU and fully hidden |
| bigger LAUNCH than 2^34 | not measured | 1.5 GB of queues per engine; 2^33 -> 2^34 was 7.6% |

### Phase split, final (SCORE13, eager profile at LAUNCH 2^33, NS 16)

| phase | share | verdict |
|-------|-------|---------|
| stage 1a bit-sieve | 46.2 ms, 53% | issue-bound at ~28% of peak issue with no single stall named: loads 25% (no-load ablation), extraction+push 21% (12% push), the rest the 16 x ~7-SASS (prime, block) body. Coalescing (marched) 1.10x slower, unroll slower, footprint a cliff, CRT pairs ~0.92x on the kernel and unresolved. **Not exhausted**: the per-(block, prime) instruction count is the lever, and the 64-bit OR (2 SASS) and 3-op residue step are where a fresh look should start |
| stage 1b rounds | 25.4 ms, 29% | rounds 0-1 (q 83..257, 400-520 M lane-tests/ms) are 12 ms of it; primes baked as literals per round (sibling: 1.084x) and 32-bit reductions are the priced next steps, ~2-3% each end-to-end |
| readback + sync bubble | 15 ms, 17% | overlapped by double-buffering (#20: 1.085x); what remains of it is the host's own read of ~85 survivors per launch |
| host classification (n = 13) | 18% of GPU time, pipelined | end-to-end 1.22e17 k/s measured = 94% of GPU-only; at n = 10 the host binds at 2.2x GPU (2.45e15 k/s end-to-end) and the leg is minutes long |

Bugs the gates caught this session, for the record: an A/B hack that
aliased both double-buffer slots to one (2746 survivors instead of
2739 -- the harness's own parity check refused to time it), and the
`time.time()` resolution floor in `huntlib.scoring` once a 2^32 window
took under a millisecond (ZeroDivisionError; now `perf_counter`).

## Priced, not built

In rough order of expected value; **estimates are not evidence**.

1. **Baked stage-1b round kernels** (primes, magics, bit offsets as
   literals, one kernel per round; sibling 1.084x on its stage 1b) --
   ~2-3% end-to-end here, stage 1b being 29%.
2. **CRT pair rows in stage 1a** -- 0.92x kernel time on one pair,
   measured under 15% noise; needs a quiet machine and 15+ rounds.
3. **32-bit `j mod q` in stage 1b** via a j-split (sibling 1.048x on its
   equivalent) -- ~2%.
4. **Stage-1a instruction diet**: the (block, prime) body is LDG + IMAD +
   2 x LOP3 (64-bit OR) + IADD + ISETP + SEL. Ideas not yet tried:
   two independent accumulators to shorten the OR chain; a residue step
   without the compare for primes where 64 mod q is tiny.
5. **A wider wheel for the deep legs** (fold 17 into the line at n = 13):
   ~1.06x of candidates, an offset table, priced and declined for now.
6. **Deeper sieve for the n <= 11 legs** -- ~1.9x on legs that already
   take minutes; declined until a leg is long enough to care.

## Declined, with reasons

- **A device-side primality test on k^2+1 to shrink the host queue.**
  60.6% of survivors die at m = 1, but they are the cheap ones: removing
  them upstream leaves 82% of the host time (measured on the sibling
  project's identical chain shape). With the host pipelined and at 18% of
  GPU at n = 13, there is nothing to buy.
- **Deeper sieving (q2 above 65536) at n = 13.** The host is not
  binding there; more primes are pure GPU cost. Re-price if the kernel
  gains another ~4x.
- **Sieving on the value line instead of the k line.** The values
  m*k^2+1 are ~10^30 and there are n of them per candidate; the k line is
  one number per candidate and every test is a residue walk. There is no
  version of this that wins, and it is written down so nobody re-derives
  it hopefully.
- **Amending SCORE / SCORE12.** They no longer resolve engine changes
  (one launch, ~1 ms, 0.5-2.3x noise between identical configurations)
  but they still pin the v1 fingerprints; the throughput anchor is
  SCORE13. Per OPTIMIZATION.md 2.13 that is the owner's call to change.
