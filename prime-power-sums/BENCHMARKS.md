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
all eight families live, `seg = 2²⁴`, `chunk = 2¹⁶`.

**Frozen fingerprint.** `147 hits / xor 5908722711111303797`.

Every one of those 147 hits is a real term of a real sequence, and all of
them are published values this project did not find — which is why the
from-scratch window was chosen over a synthetic seed at production height.

## Ledger

| date | engine | SCORE (Mp/s) | fingerprint | note |
|------|--------|--------------|-------------|------|
| 2026-08-21 | v1 | **95** | 147/5908722711111303797 | first light: three kernels, unnormalized limb prefix, Montgomery test |

## Rates that are not the score

The score is pinned to a shape so it keeps meaning the same thing while
the configuration moves. The number the **campaign** is priced on is the
rate at production height, and it is measured separately (CLAUDE.md rule
5c: device seconds per unit of the line the hunt is paid in).

| measurement | rate | how |
|-------------|------|-----|
| frozen score window, from p = 2 | 9.5×10⁷ p/s | `score.py`, median of 3 |
| production height, p = 10¹², span 2²⁶ | **1.23×10⁸ p/s** | synthetic state, real work; rate probe only |
| sieve kernel alone, p = 10¹² | 3.3×10⁸ p/s | device-only, no powers/test |

The sieve alone is ~2.7× the end-to-end rate, so **roughly two thirds of
the time is the power/prefix/test pipeline and its per-chunk host
round-trip** — a device→host copy per power per chunk, eight of them per
65 536 primes. That is the first suspect for the optimization pass, and it
is a suspect rather than a measurement: a micro-harness written for the
phase split returned several sub-resolution readings and is not trusted.
A CUDA-event harness is the first task of the next pass (OPTIMIZATION.md:
measure the phase split before touching code).

## What the campaign costs at this rate

The index line and the prime line are related by p ≈ k(ln k + ln ln k − 1).
Targets, and what v1 would need:

| target | index k | prime line | at 1.23×10⁸ p/s |
|--------|---------|------------|------------------|
| m = 11 Q1 (25% for a(19)) | 8.9×10¹⁴ | 3.3×10¹⁶ | 8.7 years |
| m = 11 median (50%) | 2.0×10¹⁵ | 7.6×10¹⁶ | 20 years |
| A045345 a(17) median | 2.6×10¹⁶ | 1.05×10¹⁸ | 270 years |

**So no campaign starts on v1.** The gap to a sane run is about three
orders of magnitude, and closing it is the next pass's whole job. For
scale, the throughput work on the other projects in this repository has
returned 20×, 27.9× and 913× on their engines, and in every case the
largest single factor came from the campaign's configuration rather than
from the kernel.

## Wall clock of the batteries

Budgeted against CLAUDE.md rule 0 (no agent command over 5 minutes):

| command | wall clock |
|---------|-----------|
| `python launch.py --selftest` | ~15 s (12 gates + 5 drills) |
| `python score.py` | ~20 s (gates ~10 s, benchmark 3 runs) |

Both are cheap because the gates run at small *k* by design: the oracle is
exhaustive to k = 60 000, the parity windows are populated but short, and
the canary hunt covers k ≈ 283 000. Nothing in the battery needs
production height, which is what keeps a full re-gate affordable after
every change.
