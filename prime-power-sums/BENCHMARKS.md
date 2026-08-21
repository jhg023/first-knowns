# Benchmarks — prime-power-sums

> **Authorship disclaimer:** None of the code or measurements in this
> project were produced by me; all of it was authored and run by
> **Claude (Anthropic's AI)** at my direction.

## The SCORE contract

`python score.py` prints a number only if **every gate is green** and the
benchmark **reproduces a frozen work fingerprint** — the exact hit count
and their xor checksum on a pinned window. An engine that skips work fails
the fingerprint; an engine that breaks correctness fails the gates. Both
score 0.

**Frozen shape.** A sweep from p = 2 to 2²⁶ (6.711×10⁷ of prime line),
all eight families live, one segment, `run = 128`, `tpb = 128`,
`subw = 1024`. The geometry is pinned in `score.py` rather than inherited
from the engine, so retuning a campaign default for a different height
cannot move the frozen shape.

**Frozen fingerprint.** `147 hits / xor 5908722711111303797` — unchanged
from v1, and unchanged through every optimization below.

Every one of those 147 hits is a real term of a real sequence, and all of
them are published values this project did not find.

Repeat runs of the whole battery land between 58,754 and 60,655 Mp/s. The
window is about a millisecond now, so a few percent of ambient GPU load is
visible in the number; the ledger records the low end.

**The median is over fifteen runs, not three.** The window now takes about a
millisecond, and at that size the rate is bimodal against ambient GPU load
(1.10 ms against 1.78 ms on the same build, same process). Three samples
put the median on the wrong mode about a third of the time. The pool is
also released and the engine warmed before the clock starts: the gates
build a dozen engines with their own cached device buffers, and that
residue is measurement noise, not engine rate.

## Ledger

| date | engine | SCORE (Mp/s) | fingerprint | note |
|------|--------|--------------|-------------|------|
| 2026-08-21 | v1 | 95 | 147/5908722711111303797 | first light: three kernels, unnormalized limb prefix, Montgomery test |
| 2026-08-21 | **v2** | **58,754** | 147/5908722711111303797 | **618×**: widths sized at codegen, cost-chosen power chain, division-free Montgomery Horner, decoupled look-back, balanced sieve |

## Where the time goes

Score window, 1.040 ms best of fifteen:

| stage | ms | share |
|-------|----|-------|
| sieve: marking | 0.201 | 19% |
| sieve: count + scan + compact (one kernel) | 0.138 | 13% |
| the sweep | 0.486 | 47% |
| host | 0.214 | 21% |

Inside the sweep, by compiling the same kernel with each stage removed and
a keep-alive on the accumulator: **powering ~50%** (both walks), the
divisibility test ~23%, the warp scan and look-back ~25%. That inverts
what v1's architecture was built around — the Montgomery test it was
designed for is the smallest of the three.

## Rates that are not the score

The score is pinned to a shape so it keeps meaning the same thing while
the configuration moves. The number the **campaign** is priced on is the
rate at production height (CLAUDE.md rule 5c), measured separately at the
campaign's own configuration: `seg = 2²⁸`, `run = 64`, `subw = 2048`.

| height | v1 | v2 | factor |
|--------|----|----|--------|
| frozen score window, from p = 2 | 9.5×10⁷ p/s | **5.88×10¹⁰ p/s** | 618× |
| p = 10¹² | 1.20×10⁸ p/s | **4.07×10¹⁰ p/s** | 338× |
| p = 10¹⁵ | — | **3.58×10¹⁰ p/s** | — |
| p = 10¹⁶ | 3.25×10⁷ p/s | **3.50×10¹⁰ p/s** | **1,077×** |
| p = 3×10¹⁶ (campaign height) | — | **3.34×10¹⁰ p/s** | — |

v1's rate *falls* with height (48 fixed limbs stop being the waste and the
base-prime pass starts being it); v2's is nearly flat from 10¹² to
3×10¹⁶, which is what makes the campaign plannable rather than a
guess. All rate probes use a synthetic state at height and do real work;
they are not fingerprinted, and they are not the score.

## What the campaign costs at this rate

The index line and the prime line are related by p ≈ k(ln k + ln ln k − 1).
At the measured 3.34×10¹⁰ p/s:

| target | index k | prime line | v1 | **v2** |
|--------|---------|------------|----|--------|
| lowest live frontier (m ≥ 8) | 5×10¹⁴ | 1.8×10¹⁶ | 18 years | **6.3 days** |
| m = 11 Q1 (25% for a(19)) | 8.9×10¹⁴ | 3.3×10¹⁶ | 8.7 years | **11.4 days** |
| m = 11 median (50%) | 2.0×10¹⁵ | 7.6×10¹⁶ | 20 years | **26 days** |
| A045345 a(17) median | 2.6×10¹⁶ | 1.05×10¹⁸ | 270 years | **364 days** |

**The campaign is startable.** Six days of walking reaches new ground on
five of the seven families at once, and the nearest quartile is a
fortnight rather than a decade. The `nice` headline (A045345) remains the
most expensive family by an order of magnitude, because its frontier is
the highest — that is a fact about the problem, not about the engine.

## The ceiling, stated plainly

An RTX 4090 issues about 2.08×10¹³ integer instructions per second
(128 SMs × 64 INT32 lanes × 2.535 GHz). Each of the frozen window's
3,957,808 primes needs, with nothing wasted, 137 word multiplies for the
shared power chain, 83 words of carry-propagating accumulation, and ~42
sixty-four-bit Montgomery limbs for the odd half of the candidates —
about **1,250 integer instructions per prime**, or ~0.24 ms for the whole
window at 100% of the device's issue rate, before the sieve and before a
single kernel launch.

So **~3,000× is the instruction-count ceiling** for this algorithm on this
hardware, and v2 sits at 618× — about half the device's issue rate, which
is what a 168-register straight-line kernel at 25% occupancy gets. Beyond
that needs a cheaper algorithm, not a better kernel.

## Wall clock of the batteries

Budgeted against CLAUDE.md rule 0 (no agent command over 5 minutes):

| command | wall clock |
|---------|-----------|
| `python launch.py --selftest` | ~35 s (15 gates + 5 drills) |
| `python score.py` | ~40 s (gates ~35 s, benchmark 15 runs + 3 warm) |

Both are cheap because the gates run at small *k* by design: the oracle is
exhaustive to k = 60 000, the parity windows are populated but short, and
the canary hunt covers k ≈ 283 000. The v2 gates add NVRTC compilations —
one per distinct limb plan — which is most of the extra time and is
cached within a process.
