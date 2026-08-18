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
