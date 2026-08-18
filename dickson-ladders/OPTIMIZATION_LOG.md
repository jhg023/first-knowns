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

## Priced, not built

Candidates in rough order of expected value. None has been measured on
this engine; the numbers are cost-model estimates and are therefore
**not evidence** -- they exist to rank what to measure first, and to stop
the next agent from re-deriving them.

1. **Bit-sieve stage 1a (the sibling project's 14x).** For a fixed prime
   q, whether candidate j is killed depends only on (q, j mod q), so a
   block of 64 consecutive j has a kill pattern computable once per
   (prime, block) on the host and OR-ed in one word per prime per 64
   candidates. That replaces ~n adds and 3 Barrett reductions per
   (candidate, prime) with one load and one OR per 64 candidates.
   Estimated 5-15x; this is the main event.
2. **Strip threads with incremental residues.** j -> j+1 increments
   j mod q by one, so a thread covering T consecutive candidates pays the
   Barrett reduction once instead of T times. Cheap to build, ~1.2-1.5x
   guessed, and it composes with (1) rather than competing.
3. **Two-stage compaction.** Most candidates die on the first few primes
   (kill probability ~n/q, i.e. ~0.77 at q = 13), so warps diverge
   immediately. Splitting the sieve into a shallow pass plus a compacted
   deep pass is what made the sibling project's stage 1b 2.4x cheaper.
4. **A wider wheel for the deep legs.** W(n) is forced by n, but nothing
   stops a *deeper* wheel: folding the next prime (17 at n = 13) into the
   generated line costs an offset table and buys ~1.06x of candidates.
   Small, and the sibling project's experience says the offset table is
   where the complexity lives. Priced and declined for now.
5. **Host classification in parallel.** Trigger stated above. The loop is
   embarrassingly parallel per survivor; the checkpoint's ascending
   classification order is what the least-claim depends on, so any
   parallel version must preserve the ordering of *reported* results, not
   necessarily of tests.

## Declined, with reasons

- **A device-side primality test on k^2+1 to shrink the host queue.**
  60.6% of survivors die at m = 1, but they are the cheap ones: removing
  them upstream leaves 82% of the host time (measured on the sibling
  project's identical chain shape). At a 6% host share that buys ~1% of
  wall. Revisit only if (5) is somehow blocked.
- **Deeper sieving (q2 above 65536).** Survivor density is already
  2.75e-7 at n = 10; each further decade of primes costs more per
  candidate than it removes from a host that is 6% of the wall. Re-price
  after the kernel gets faster, not before.
- **Sieving on the value line instead of the k line.** The values
  m*k^2+1 are ~10^30 and there are n of them per candidate; the k line is
  one number per candidate and every test is a residue walk. There is no
  version of this that wins, and it is written down so nobody re-derives
  it hopefully.
