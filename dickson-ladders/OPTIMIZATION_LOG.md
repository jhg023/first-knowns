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

### Pool size 60 -> 8 -- the sweep above optimized a number that was not free


The sweep read "more workers, better ratio" and took `cpu_count - 4` = 60
processes. It measured throughput only, and throughput was not the binding
constraint: the campaign has to leave the desktop it runs on usable, and
`cpu_count - k` is an appetite that scales with the host rather than with
the work. Everything the hunt actually consumes is modest, and was
measured: one launch is 21 ms of device time across 9 kernels (the TDR
watchdog is 2 s), every queue write is bounds-guarded, the engine holds
~0.8 GB of 24 GB of VRAM, and the pool holds ~7-9 GB of 64 GB. What is
*not* modest is 60 fresh interpreters importing numpy and sympy in the
same instant, which is peak host draw and lands exactly while the device
is flat out on the next segment. The default became `min(8, cpu_count -
2)` and then 4, sized from the requirement (CONVENTIONS.md, "Sizing a
hunt so it leaves the machine usable").

Eight was the conservative setting, and it is NOT the throughput optimum --
recorded here so the tradeoff is explicit rather than rediscovered.
Measured on the live campaign (n = 11, k ~ 9.5e18, cap 19, 40-digit
values), sampling worker CPU and device utilization over the same window:

| quantity | measured |
|---|---|
| survivors classified | 70,082 /s (253M over 3,612 s) |
| host cost per survivor | ~105 us |
| pool at 8 workers | ~92% duty, **7.4 cores** (+0.5 parent) |
| device utilization | alternates 98% / 12%, **mean 41%** |
| per 1.0e16-k segment | pool ~4.0 s vs device ~1.8 s |
| end-to-end | 2.35e15 k/s |

So at eight workers the pipeline is **host-bound by 2.3x and the device
idles 60% of the time**. The knee is ~18 workers, where the device binds
again and the rate should reach ~6e15 k/s (~2.5x). The default stays at 8
because the failure it prevents is worse than the throughput it costs, and
because the spawn burst scales with the worker count -- raising toward the
knee is a deliberate, watched change, not a default.

**A methodology note that cost real time here.** The first sizing of this
used the engine's `profile` path to time a launch: 21.2 ms across 9
kernels, which gave 5.4 s of device time per segment and the conclusion
"five cores is plenty". That is ~3x too slow, because `profile` runs the
kernels **eagerly with CUDA events between them**, i.e. it disables exactly
the graph replay production uses. The live device time is ~1.8 s per
segment. OPTIMIZATION.md Rule 1 says measure the split before optimizing;
the corollary this adds is that **an instrumented path is not the
production path** -- take phase splits from a running campaign (worker duty
+ `utilization.gpu` sampling) when one is available.

Two rules came out of this and are worth stating plainly: a tuning sweep
that only measures throughput cannot see the constraint that actually
binds (OPTIMIZATION.md Rule 7), and **a hunt that runs for days on
somebody's desktop does not get to take the whole machine**
(CONVENTIONS.md).

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


---

## v3 (2026-08-18): the campaign was configured 28x below its own engine

The engine had been optimized hard and the CAMPAIGN had not been optimized
at all. Every number below is per **1e18 of k-line** at k ~ 1e19, paired
and interleaved in one process (Rule 3), fingerprints checked every run,
on an idle machine.

The starting point, measured rather than remembered -- filter 11, wheel
2310, q2 = 65536, all-bases classification, 8 workers:

| side | cost per 1e18 k |
|------|-----------------|
| device | 142.3 s |
| host (2.98e7 survivors x 111.2 us) | 3,308 core-s, 413 s on 8 workers |
| **end-to-end** | **413 s = 2.42e15 k/s** (the live campaign logged 2.35e15) |

and after the changes below, **14.78 s = 6.77e16 k/s on 4 workers**: a
measured **27.9x**, with half the host processes.

### 0. First, a correctness bug -- found by the canary, not by a gate

Deepening the sieve is one of the changes below, and the first campaign
smoke run at the new depth reported:

```
[ALARM] CANARY ALARM: a(7) rediscovery failed (got [], expected 3776600100)
```

The walk that builds the kill-bit table (`_TABLE_SRC`) squares a residue,
so its intermediates reach `q^2`. It was written in **32-bit**, which is
exact only for `q < 2^16` -- and the engines' own `q2` default is 65536, so
in the whole life of the engine **no test had ever evaluated a prime whose
square leaves u32**. Ask for a deeper sieve and the products silently wrap.
Measured at q2 = 262144: for q = 81899 the table marked 7 residues dead
where 10 are dead, and not as a subset -- so the sieve both kept candidates
it should kill (harmless, host cost) and **killed candidates it should
keep**, which is how a term being hunted disappears. a(7) was one of them.

Fixed by doing the walk in u64 (exact for every `q < 2^32`, and it runs
once per engine so the width is free), and `Q2_MAX` now states the bound
the arithmetic holds over rather than leaving it in a comment.

The gate lesson is the general one, and it is worth stating plainly: **G14
checked the kernel's decisions against big-integer divisibility, and G6
checked the GPU stream against the CPU engine, and both were green
throughout -- because every gate in the file used the default q2.** A gate
that only ever runs at one point in a parameter's range does not test the
parameter. `g16_deep_sieve_arithmetic` now checks the table against
divisibility at q2 = 2^18 for primes sampled across the whole range, at
least three of them above 2^16, and re-checks the deep stream against the
CPU engine -- whose table comes from sympy's square roots in Python
integers and cannot share the failure.

Every measurement in this section was re-taken after the fix.

### 1. Filter lag 1 -> 0: the wheel is the whole ballgame -- 13x

`W(n)` is the product of the primes `<= n+1`, because `run(k) >= n` forces
`q | k` for every prime `q <= n+1` (m runs over a complete residue system
mod q, so some m has `m*k^2 == -1 (mod q)`, and that value exceeds q above
the floor). Hunting a(12) at filter **12** therefore rides the **30030**
wheel instead of the 2310 one: 13x fewer candidates per unit of k-line and
13x fewer survivors to classify. The least-claim is untouched -- a(12) is
a multiple of 30030 by that same argument, so the coarser wheel skips
nothing that could BE a(12).

Lag 1 existed so that run-11 values (one short of a(12)) still got their
`[NEAR]` line and the census still filled in below the frontier. That is
bookkeeping; a(12) is the hunt. `--filter-lag 1` restores it at 1/13 the
rate.

| filter | wheel | device | survivors |
|--------|-------|--------|-----------|
| 11 | 2310 | 142.3 s | 2.98e7 |
| 12 | 30030 | 14.35 s | 2.29e6 |

### 2. Two-pass classification -- 2.44x on the host, and it is still exact

`mr_is_prime` evaluates the 7-base huntlib set. Profiling the real
survivor stream showed **2.446 bases per value** -- not because composites
are expensive (a composite is rejected by the FIRST base: one modular
exponentiation, 27 us) but because **24% of survivors have m*k^2+1 prime
at m = 1**, and a prime is what makes all seven bases run.

The fix uses the asymmetry of a strong test: **a failure is a PROOF of
compositeness; only a pass is mere evidence.** So a base-2-only chain
(`huntlib.primes.sprp_base2`) yields a rigorous UPPER BOUND on the run --
it can stop too late, never too early. If that bound lands below
`SPRP_EXACT_FROM = 5` the true run is proved to be below it, and nothing
the campaign records depends on which of 0..4 it was (census counts start
at 7, `[NEAR]`/`[DISCOVERY]` are higher, and `best_run` is guarded to the
same floor). If the bound reaches 5 the chain is redone with the full base
set.

This is not a probabilistic shortcut: **every run length the campaign
writes down still comes from the full base set.**

| | modpows/survivor | us/survivor |
|---|---|---|
| all-bases chain | 3.27 | 111.2 |
| two-pass | 1.34 | **45.7** |

Drilled in the selftest against `GpuEngine.run_length` (which never takes
the shortcut) over every survivor of a real window: identical, and every
cheap-chain result an upper bound.

### 3. Sieve depth 65536 -> 262144: buys back three quarters of the host

With the device 13x cheaper and the host 2.4x cheaper, which side binds is
now a genuine choice, and q2 is the dial. Deep rounds hold tiny
populations, so **the device is nearly flat from 65536 to 262144** while
survivors fall 4.1x:

| q2 | device | survivors | host core-s | pool needed | end-to-end |
|----|--------|-----------|-------------|-------------|------------|
| 65536 | 14.35 s | 2,293,610 | 104.8 | 8 workers | 6.97e16 k/s |
| 131072 | 14.93 s | 1,106,720 | 50.6 | 4 workers | 6.70e16 k/s |
| **262144** | **14.78 s** | **560,509** | **25.6** | **2 workers** | **6.77e16 k/s** |
| 524288 | 16.07 s | 292,700 | 13.4 | 1 worker | 6.22e16 k/s |

All four are within 3% end-to-end, so this is not a throughput decision at
all -- it is a decision about **how much of the machine the hunt asks
for**, and the rule is to take the setting that asks for less. 262144
gives up 3% and asks for a quarter of the CPU. `--q2` overrides; the
frozen benchmark depth (65536) is untouched, and `score.py` now pins it
per shape rather than inheriting a default, so SCORE stays comparable.

### 4. Constants re-swept after the structural change -- 1.14x

The tuning constants were all swept at n = 13 / q2 = 65536. The campaign
now runs n = 12 / q2 = 262144 with 3.5x the stage-1b primes, and the
re-sweep rule paid:

| # | change | campaign shape | other shapes | verdict |
|---|--------|----------------|--------------|---------|
| 22 | **RATIO 4 -> 2** (a round ends when survival within it halves; 8 -> 16 rounds) | **1.119x** (min 1.012; 3: 1.092) | 1.103x at n=12/q2=65536, 1.034x on SCORE13 | KEPT -- and the earlier verdict (4 by 1.097x) does not reproduce on an idle machine |
| 23 | **T_MAX 1024 -> 2048** | **1.017x** | 1.020x on SCORE13 (min 1.014) | KEPT |
| -- | NS 24 (derived) vs 16/20/22/26/28 | 0.854 / 0.987 / 0.995 / 0.968 / 0.945 | | derivation confirmed, unchanged |
| -- | LAUNCH 2^34 vs 2^33 / 2^35 | 0.935 / 1.027 | | 2^35 is 2.7% for 2x the queue memory (1.65 GB) -- priced, not taken |
| -- | WARP_POP 2^16 vs 2^14/2^18/2^20 | 0.936 / 0.999 / 1.009 | | flat, unchanged |
| -- | T 4096 | 1.039x | 1.035x on SCORE13 | NOT REACHABLE by the derivation at LAUNCH 2^34 without halving MIN_BLOCKS_PER_SM, which is the guarantee that a small window still fills the device. Priced, not taken |

Cumulative engine gain, HEAD vs now, paired and interleaved: **1.046x on
SCORE13** (min 1.036), **1.103-1.119x at n = 12**. The 2^32 shapes
returned 1.42x and 0.83x with paired spreads of 0.57-2.04 -- they no
longer resolve anything (OPTIMIZATION.md 2.13), which is why the verdicts
above are read off the campaign shape and SCORE13.

### Rejected: unrolling the stage-1a block loop -- and what it taught

The lever named in v2's phase split was "the per-(block, prime)
instruction count". It is **not a lever**, and this is the measurement
that says so.

The idea was sound on paper. The body was

```
acc |= pat[po + s];   s += (64 % q);   if (s >= q) s -= q;
```

-- one load, one 64-bit OR (2 SASS) and a three-instruction modular add,
every block, every prime. 64 is invertible mod q, so re-indexing each row
by `v -> (64 % q) * v mod q` turns the walk into an INCREMENT: block b
wants row entry `u + b`. Consecutive blocks then read consecutive entries,
so U of them need ONE modular add instead of U, and padding each row with
U-1 copies of its head removes the wrap test. At U = 4 the body goes from
24 instructions per prime per 4 blocks to 15.

It was implemented twice (U parallel accumulators; then one accumulator
with the offset folded into the load's immediate) and both were **worse**,
monotonically, on SCORE13 with fingerprints intact:

| U | 1 | 2 | 4 | 8 |
|---|---|---|---|---|
| U accumulators | 1.007x | 0.717x | 0.592x | 0.455x |
| one accumulator | 1.000x | 0.684x | 0.591x | 0.445x |

Registers were not the cause (44 -> 42, no spills). Ablations found it:

- **The body does not care.** Loads + ORs + the modular adds, with
  extraction and atomics deleted: **2.57 / 2.56 / 2.44 / 2.69 ms** at
  U = 1/2/4/8. Cutting 44% of the body's instructions changed nothing.
  So stage 1a is **not issue-bound**, which is what v2's phase split
  recorded.
- **It is the push.** Timing the stage-1a kernel alone with the
  `atomicAdd` replaced by a fixed slot: 3.16 / 2.80 / **2.62** / 2.65 ms
  -- the unroll IS worth 1.21x once the atomic is out. With the atomic in:
  3.66 / 5.95 / 6.52 / 9.45 ms. The single-address atomic costs 0.5-1.0 ms
  un-unrolled and **6.80 ms** at U = 8. NVCC's automatic warp-aggregated
  atomic is what makes the un-unrolled push nearly free, and the unrolled
  control flow loses it. (Replacing the mid-loop `break` with a masked
  tail did not bring it back: 0.591x -> 0.598x at U = 4.)
- **What it IS bound by**: giving every lane the same residue, which
  collapses each gather from ~18 distinct 32-byte sectors to 1 and changes
  nothing else, is **1.24x**. So the body is L1-**sector**-bound, and the
  arithmetic around the gathers is free.

### Rejected: spreading the stage-1a atomic over more counters

Following the above, the obvious next move is to kill the contention on
the single counter. It is not contention. Replacing
`atomicAdd(nout, 1u)` with `atomicAdd(nout + (blockIdx.x & (P-1)), 1u)`
-- same warp-uniform address, more of them -- measured, at the campaign
configuration (grid 512, 19.1M pushes per launch):

| counters | 1 | 8 | 32 | 128 | 512 | none |
|----------|---|---|----|-----|-----|------|
| stage 1a | **4.32 ms** | 5.80 | 5.92 | 5.96 | 4.89 | 3.99 |

Spreading it is **worse at every P**. The single-address form is the one
NVCC compiles to a warp-aggregated push; anything else gives that up and
pays per-lane. Combined with the v2 finding that a hand-written
ballot+scan aggregation is 1.64x slower, **the push has no cheaper form**,
and per-block queue slices (which would have been the next attempt) are
priced at zero before being written.

Corrected verdict for stage 1a, replacing v2's: **the lever is the number
of gathers per candidate and their sector spread, not the instruction
count and not the atomic.** The ceiling available -- free gathers AND a
free push -- is about 2x on a phase worth 66% of device time. The two
known ways to spend it have both already been measured and lost (the
marched/coalesced table, 1.10x slower; CRT pair rows, 0.92x). Anyone
picking this up should attack sectors, and should not re-derive the
instruction-diet idea: it is priced at zero here.

### Phase split at the campaign configuration (n = 12, q2 = 262144)

Measured by subtraction on the production path, not through the `profile`
hook (which disables the graph replay and overstates device time ~3x):

| phase | ms/launch | share |
|-------|-----------|-------|
| stage 1a bit sieve | 5.07 | **66.4%** |
| stage 1b, 16 compaction rounds | 2.67 | 35% |
| readback + sync + host sort | ~0 | ~0 |

Round 0 (q 127-173, 10 primes, 19.1M -> 9.0M) is 0.76 ms of stage 1b; the
per-round subtraction is noisy at +-1 ms and should not be read finer than
that.

### Robustness, measured against the machine rather than the clock

- **The checkpoint did not survive an abrupt stop.** It came back as 785
  bytes of NUL -- exactly its own length, none of its content. `os.replace` is atomic for the directory ENTRY; the DATA was
  still in the page cache. `huntlib.checkpoint.save` now flushes and
  **fsyncs** before the replace and rotates the previous file to `.bak`;
  `load` falls back to the `.bak` and, failing that, raises
  `CheckpointCorrupt` instead of quietly returning None -- which for a
  live frontier would have restarted the sweep at the floor. Drilled in
  the selftest on the exact 785-NUL corruption.
- **The pool is ramped, not stamped.** `ProcessPoolExecutor` spawns on
  submit only if no worker is idle, so a segment's worth of chunks starts
  every worker in the same instant -- N fresh interpreters importing numpy
  and sympy at once, at peak host draw, while the device is flat out. They
  now start one at a time (`_prime_pool`, `--worker-ramp`) at below-normal
  priority, warm before the first segment. Drilled.
- **A run that ENDED never saved.** Every other exit persisted the cursor
  -- segment boundary every `--heartbeat`, evidence at once, Ctrl+C,
  `--stop-on-discovery` -- and ordinary completion did not, so a `--to` run
  threw away everything it had swept and the next one started again from
  the floor. Silently, because a re-sweep looks exactly like a sweep: the
  only visible symptom was `--status` still reading k = 3.0e4 after two
  completed runs, and a survivor count that happened to match because the
  same k-line was covered twice. Found by running `--to` twice and reading
  `--status`; now drilled in the selftest, which runs two bounded
  campaigns in a temp directory and requires the second to resume where the
  first stopped.
- **The device no longer square-waves.** Host-bound by 2.3x meant the GPU
  idled 60% of the time, alternating 98%/12% utilization every few seconds
  -- thousands of full-amplitude load transitions an hour on a 450 W card.
  The device now binds, so it runs at a steady load.
- **The campaign logs the machine's state at start** (GPU, SMs, VRAM held,
  driver, power limit, max clock, temperature), so the log itself answers
  "how much VRAM did it hold" and "was the card at stock limits" for any
  run, without anyone reconstructing it afterwards.

### What v3 settles from the v2 "priced" and "declined" lists

- **"Deeper sieve for the n <= 11 legs -- ~1.9x, declined until a leg is
  long enough to care."** TAKEN, and for a different reason than it was
  priced: the win is not throughput (3%) but host processes (4x).
- **"Deeper sieving (q2 above 65536) at n = 13."** Still declined there.
  `--q2` makes it a campaign choice rather than an engine constant.
- **"Stage-1a instruction diet ... two independent accumulators to shorten
  the OR chain; a residue step without the compare."** PRICED AT ZERO,
  measured. Do not re-derive this.
- **"A device-side primality test on k^2+1 to shrink the host queue."**
  Still declined, and now by a wider margin: the host is at ~43% duty on
  4 workers and the device binds.
- **CRT pair rows** and **baked stage-1b round kernels** are unchanged and
  still the two best remaining ideas -- but note that CRT pairs now have a
  *mechanism* to be judged against (sectors per gather, not table size),
  which is not how they were priced.


---

## v4 (2026-08-19): the fold -- a declined item re-priced 3x wrong, worth 2.39x

### 0. First, the crash that freed the machine to measure

The live a(13) campaign died at k = 1.097e22: a run-12 [NEAR]
verification called `full_verify`, whose alternate-alignment leg
re-sieved a window around k on the COARSER 2310 wheel, and
j = k/2310 = 4.75e18 tripped the enforced J_CEIL (4e18) guard --
ValueError, campaign down.  The coarse verification wheel crosses the j
ceiling at k = 9.24e21, **13x before the campaign's own wheel does**, and
the eight earlier run-12 values all happened to sit below that.  The
checkpoint was at a segment boundary as designed; the crash cost two
minutes of sweep.  The leg now consults the alt engine's residue table
directly (`CpuEngine.survives`, Python integers, exact at any depth) --
membership of k is all the windowed sweep ever checked -- and the
selftest's deep-verification drill pins the direct check against
big-integer divisibility at the exact j that raised.  Committed
separately (db24539) before any measurement below.

### 1. The mispriced decline (OPTIMIZATION.md Rule 5b, worked example)

The v2 "priced, not built" list carried: *"a wider wheel for the deep
legs (fold 17 into the line at n = 13): ~1.06x of candidates ...
declined."*  That price is a linear-form transplant -- one killed
residue per prime, 17/16 = 1.06 -- and this form is QUADRATIC: every
solvable m contributes two roots, so w_q ~ n.  The engine's own kill-bit
table says w_17(13) = **12**: folding 17 out of the sieve and into
candidate generation keeps 5/17 of the line -- **3.4x fewer candidates**,
not 1.06x.  A decline is only as good as its stated reason, and this one
did not survive a single popcount of a table the engine already builds.

### 2. Phase split at the live shape (n = 13, q2 = 262144), before building

Whole-graph events on the production path (graph replay intact, no
readback), interleaved full-chain vs stage-1a-only:

| phase | share |
|-------|-------|
| stage 1a | 5.90 ms/launch -> **60.7%** |
| stage 1b + tail | 2.32 ms -> 39.3% |

Device 11.4 s per 1e18 k idle; ~81 final survivors per 1e18 k at this
depth, so the host pool is essentially idle at n = 13 (~3.7 core-s per
1e18 k) and every win below is pure device win.  Predicted fold value:
1a x (5/17) x (NS'/NS) -> ~1.8x end-to-end.

### 3. The fold, built (engine v4)

Enumerate u with j = P*u + r over the offsets r that survive P = 17
(five of seventeen at n = 13: 0, 2, 6, 11, 15, from the same walk the
device runs).  The kill-bit and pattern tables are built per offset --
entry s answers for j = P*s + r -- and the KERNELS ARE UNCHANGED: they
walk u where they walked j, and a launch picks its offset's tables by
pointer (CUDA graphs captured per offset, since a graph bakes pointers).
The survivor stream is identical by construction; all three frozen
fingerprints reproduce, and the new **G17** pins folded == unfolded bit
for bit on populated windows and unaligned cuts, then checks the deep
zone (below) against big-integer divisibility with no engine on the
other side.

NS re-derives from the same S1A_TARGET on the folded line: 16 -> 24
primes (the line's survivors are 3.4x denser per candidate, so stage 1a
carries more primes at the same queue density -- and the densest
stage-1b primes moved into 1a with it, which is where the measured win
beats the 1.8x prediction).

**Paired A/B at the campaign shape (n = 13, q2 = 262144, 2^41-j window
at the live cursor, streams compared every round, both arms in one
process): fold/unfold = 2.387x (min 2.138, max 2.439, 7 rounds).**
2.31e17 k/s folded vs 9.64e16 unfolded on the idle machine -- 4.3 s of
device per 1e18 k.

### 4. Constants re-swept after the structural change (Rule 3.4)

| knob | swept | verdict |
|------|-------|---------|
| NS (derived 24) | 15: 0.751, 20: 1.003, 24: 1.000, 26: 0.972 | derivation KEPT -- the 20-24 plateau is flat; the "cheap 1a" point (15, same absolute queue as v3) loses 25% |
| LAUNCH | 2^33: 0.912, 2^34: 1.000, 2^35: 1.021 | 2^34 stays: +2.1% is not worth 2x the queue memory (0.71 -> 1.42 GiB), same verdict as v3 |
| T pinned 4096 | **0.979** (was 1.039x before the fold) | DECLINED, and the standing "T 4096 unreachable without halving MIN_BLOCKS_PER_SM" question closes: the fold moved the optimum back to the derived 2048.  Re-sweeps exist because of exactly this |
| RATIO | 1.5: 0.949, 2: 1.000, 3: 0.922, 4: 0.901 | 2 stays |

### 5. What the fold costs, and what it moves

- **Device memory 0.77 -> ~2.4 GiB** (five kill-bit tables at 344 MiB
  each, q2 = 262144, plus the queues) of 24 GiB.  Stated per the load
  budget; one offset's tables are hot per launch, so the L1 footprint --
  the measured cliff -- does not move (pattern table 13.0 KiB/offset at
  NS 24; the NS sweep shows the cliff is not biting).
- **The queue-cap clamp moved 2^26 -> 2^27**: the folded line's stage-1a
  survival is P/(P-w_P) higher at the same prime count, and a swept-low
  NS hit the old clamp.  The analytic sizing still governs allocation.
- **The reach extends 17x**: the device's u64 quantity is u, so the
  engine holds to j = P * J_CEIL = 6.8e19 -- **k = 2.04e24**.  The old
  ceiling (1.20e23) sat between a(14)'s Q1 and median (E = 0.54, a 42%
  chance of a(14)); the new reach covers a(14) to E = 4.41 (98.8%).
  Past j ~ 1.8e19 the value of j leaves u64: `survivors_j` (numpy)
  refuses that zone and `survivors_j_deep` (Python integers, the
  campaign's API) owns it, G17-checked at the top of the reach.
- The frozen 2^32 shapes degrade further (a folded pass is 5-7 ragged
  eager launches; OPTIMIZATION.md 2.13) -- their absolutes are now pure
  noise, but they still pin their v1 fingerprints, which is their job.
  SCORE13's window holds ~0.94 launches per offset (eager, no overlap)
  and still reads 2.2x the pre-fold capture; the anchor for future
  engine A/Bs should be a campaign-shaped window, as used here.
- G13's graph drill runs LAUNCH 2^18 so each offset's u-span still holds
  full launches; the drill's point (graph == eager) is unchanged.

### What v4 settles from the standing lists

- **"A wider wheel for the deep legs (fold 17): ~1.06x, declined"** --
  the price was wrong 3x, the item is BUILT, and it was the largest
  single device win since the v2 restructure.
- **"T_MAX 4096, priced 1.4%, not reachable by the derivation"** --
  re-priced at 0.979x under the fold; closed, not worth reaching.
- **CRT pair rows** and **baked stage-1b round kernels** remain the two
  best un-built ideas, unchanged -- but re-price both against the folded
  profile (stage 1a is now ~35% of a much smaller device bill, and
  round 0's primes moved into 1a).
- Folding a SECOND prime (19: 7/19 survive at n = 13, another 2.7x
  thinning of what remains of stage 1a) is PRICED, NOT TAKEN: offsets
  multiply to 35 classes, the kill-bit tables scale to ~12 GiB at the
  campaign depth, and stage 1a is no longer 60% of anything.  Revisit
  only if stage 1a dominates again at a much deeper q2.

### Postscript: what v4 bought

a(13) = 12,094,123,415,384,869,458,600 landed at k = 1.209e22 on
2026-08-19, 58 minutes after this entry's commit -- 1.12e21 of k-line
past the crash point the folded campaign resumed from (RESULTS.md).  The
campaign was paused 2026-08-20 at k = 1.57e22 with a(14) the next open
term, E = 4.28 inside the remaining folded reach.
