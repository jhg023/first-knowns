# Optimization log — prime-power-sums

> **Authorship disclaimer:** None of this work was done by me; all of it
> was authored and measured by **Claude (Anthropic's AI)** at my
> direction.

Every attempt: change, measurement, kept or rejected. Failures included —
they are the record that stops the next person retrying them. The process
rules are in [OPTIMIZATION.md](../OPTIMIZATION.md); the two that bind
hardest here are *measure the phase split before touching code* and
*never treat the cost model as evidence*.

## v1, 2026-08-21 — first light, and the gap it revealed

The engine was built for correctness first: three kernels, an
unnormalized limb prefix, a Montgomery divisibility test. It is green on
twelve gates and five drills and scores **95 Mp/s**.

Then it was measured at production height, which is the measurement that
matters (CLAUDE.md rule 5c), and the answer is uncomfortable:

| | rate |
|---|---|
| end-to-end at p = 10¹² | 1.23×10⁸ p/s |
| sieve kernel alone | 3.3×10⁸ p/s |
| **needed for the nearest target (m = 11 Q1)** | ~1.2×10¹¹ p/s for a ~3-day run |

**About three orders of magnitude short.** The campaign is not startable
and the project's status says so. This entry exists so the next pass
starts from a number rather than from an intuition.

What that number does establish: the sieve is only ~2.7× the end-to-end
rate, so **the sieve is not the bottleneck** — roughly two thirds of the
time is the power/prefix/test pipeline. That inverts the assumption the
project was pitched on (a sieve-bound hunt, priced against primorial-ap's
2.07×10¹¹ p/s sieve), and it inverts it *before* any effort was spent
optimizing the wrong phase. The pitch's arithmetic was not wrong about
sieving; it was wrong to assume this engine would be sieve-bound.

### Not trusted: the first phase-split harness

A micro-harness timing each kernel separately returned several
sub-resolution readings (0.0 ms for `pow_limbs` at m = 1 and for
`test_hits`, and mutually inconsistent totals against the m = 11 figure).
Python-side wall timing around asynchronous launches is not good enough at
these sizes. **Rejected as a measurement**; a CUDA-event harness is the
first task of the next pass. The end-to-end and sieve-only figures above
are trustworthy because they are wall-clock over hundreds of milliseconds.

## The named levers, unpriced

Candidates only. None has been measured, none may be quoted as a number
until it is, and the ordering below is a prediction the harness will
confirm or overturn.

1. **Never materialize the prefix.** v1 writes a (48 × 65 536) uint64
   array per power per chunk, runs `cumsum` over it, and reads its last
   column back to the host — a blocking device→host copy **per power per
   chunk**, eight per 65 536 primes. Fusing the prefix scan and the
   divisibility test into one kernel, keeping the accumulator in registers
   or shared memory and writing only hits (about one per 10¹⁵ candidates),
   removes both the traffic and the syncs. This is the largest suspect and
   the one the architecture was warned about before it was written.
2. **Shared addition chains across powers.** p², p⁴, p⁸ are recomputed
   from scratch for each of the eight families; computed once, every
   p^m falls out in a couple of multiplications. Expected to matter in
   proportion to how much of the pipeline `pow_limbs` really is — which
   is exactly what the harness has to settle first.
3. **Track the live limb length.** `pow_limbs` already grows its working
   length, but `test_hits` walks all 48 limbs regardless of how many are
   populated; at m = 1 that is 45 wasted Horner steps out of 48.
4. **The index wheel in the kernel, not after it.** The obstruction
   already skips k sharing a factor with Q(m) — but as an early `return`
   per thread, so the warp still pays for the divergence. At m = 12 four
   fifths of threads return immediately.
5. **Analytic seeding (Lucy_Hedgehog prefix recurrence).** Deliberately
   declined for v1 and priced here so it is not re-argued: the run-up
   below the lowest live frontier is ~0.1% of the campaign, and walking it
   buys the 124-term canary battery. It becomes interesting only for a
   single-family run aimed at A045345, whose frontier is 20× higher than
   the rest — there it would remove about half the sweep.

## Declined, with the price

- **A benchmark seeded at production height.** Rejected for the SCORE: a
  synthetic (k, sums) seed makes every hit in the fingerprint
  mathematically meaningless, and the whole value of the frozen window is
  that its 147 hits are real published terms. Kept as an unfingerprinted
  *rate probe* in BENCHMARKS.md, which is what it is good for.
- **Widening coverage to even k.** The engines declare ODD_ONLY because
  Montgomery needs an odd modulus. For every *e* = 0 family this is
  provably free (2 | Q(m) always, so every term is odd). Widening it would
  buy only the even terms of the census family — a sequence that is
  already data-entry class — at the cost of a second, slower reduction
  path. Not worth a line of code.
- **A host worker pool.** There is nothing for it to do: the host
  normalizes carries once per chunk and verifies only when something is
  found. The load budget (CONVENTIONS.md) is satisfied by having no pool
  at all rather than by sizing one, and the throttles that exist
  (`--gpu-yield-ms`, `--gentle`) are device-side.
