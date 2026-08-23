# OPTIMIZATION_LOG — shift-ladders

Every attempt: the change, the measurement, kept or rejected. Failures
included — they are the record that stops the next person retrying them.
Read [OPTIMIZATION.md](../OPTIMIZATION.md) first; its rules are binding
here, and two of them shaped this engine before a line of it was written.

## v1 — the first engine (2026-08-23)

**What it is.** A flat residue table for the primes up to `p1`, built by
CRT lifting; one thread per candidate; a Barrett magic-multiply reduction
and one bitmap lookup per remaining prime, bailing out at the first kill.
Candidates carried as `(m, off)` with the base folded per prime on the
host. Correctness first: five gates and drills of its own, a bit-for-bit
parity gate against the CPU engine on six populated windows, and five
frozen benchmark fingerprints.

**Two OPTIMIZATION.md rules were applied at design time, not after:**

- **2.7, carry `(m, off)`.** No machine word bounds this search from the
  first commit. square-ladders retrofitted this and its second ceiling
  raise cost a campaign stretch; here the enforced ceiling has never been
  anything but the primality-proof bound.
- **Choose the wheel that fits at every parameter the battery runs.** `p1`
  is per base (23 at b = 4, 37 at b = 2) because the two wheels differ in
  density by 3,000×, and the flat table's size limit is enforced
  (`RES_MAX`) rather than discovered: the b = 2 wheel reaches 1.29×10⁹
  residues at p1 = 47, and asking for it must refuse rather than fail 183
  GiB into a numpy allocation. It did exactly that once, during this
  build, which is why the check is now computed from the products before
  anything is allocated.

### Measured during the v1 build

**1. The per-launch base fold: 6,533 big-int divisions → one numpy step.
KEPT.** `base mod q` for every sieve prime was recomputed from the Python
big int on every launch. Measured directly: **0.357 ms per launch**
against **0.034 ms** for the numpy step form — 10.5×. The base advances by
a fixed stride between launches, so it is computed in full once per sweep
and stepped after that (a short final launch falls back, at most once).

What that was worth depends entirely on the shape, which is the point:
0.357 ms is 13% of a production launch (2.7 ms) and **99.5%** of a
coarse-wheel one (~2 µs of device work). The coarse-wheel benchmark shapes
went from 0.77 s to 0.003 s for the same work.

**2. Launch size: fixed 64 periods → sized from the wheel. KEPT, and
re-swept.** A launch covers whole periods, so 64 of them is 10⁸ candidates
at `p1 = 23` and 65,000 at `p1 = 13` — three orders of magnitude of device
work for the same fixed host cost. The default is now a constant number of
CANDIDATES per launch. Interleaved, paired, fingerprint checked on every
run:

    base 4, n = 19, p1 = 23           base 2, n = 17, p1 = 37
      16 periods   0.762x               12 periods   1.000x (old default)
      42           0.934x               32           1.241x
      64           1.000x (old default) 49           1.366x
     128           1.079x               96           1.427x
     256           1.076x              192           1.421x
     341           1.147x
     512           1.114x

Both plateau at about **2²⁹ candidates per launch**, which is what the
constant now targets (341 periods at base 4, 99 at base 2). Worth 1.15×
at base 4 and 1.43× at base 2 against the fixed 64.

**A rule was broken and then repaired, and it is logged because the repair
is the interesting part.** Changes 1 and 2 were first made in a single
edit and measured together — exactly the "an A/B that varies two things
credits the interesting one" failure OPTIMIZATION.md names. They were then
separated: change 1 by direct measurement of both fold forms, change 2 by
the interleaved sweep above with change 1 already in place. The combined
figure would have credited the launch size with the fold's win at the
coarse shapes and the fold with the launch size's win at the production
one.

**3. Absolute rates swing 30-50% run to run; ratios do not.** The same
production shape measured 3.5, 4.1, 4.5, 5.2 and 6.4 ×10¹² m/s across the
session on an otherwise idle machine, while the interleaved ratios above
repeated to a few percent. The cause is at least partly structural: the
production shape's residue table is 12.6 MB and is streamed once per
launch, so it is bandwidth-sensitive where the 8 KB coarse-wheel shapes
are not (11-13% spread against 51%). **No A/B on this project may be read
off two separate `score.py` runs.**

## Priced and not done

The v1 engine is deliberately unoptimized and the two levers that matter
are both known, both priced from another project's measured results, and
both large.

**A. The factored multi-level wheel — worth ~14× at base 4.** The wheel
stops at `p1 = 23` only because a flat table cannot hold more; the same
CRT lift applied twice more gives the wheel to 47 as three small tables
instead of one impossible one (square-ladders: 1,088,640 × 4,560 × 16,675
entries, 8.8 MB, for a wheel of 8.3×10¹³ residues). Priced from the
densities this project's own `wheel()` already computes:

| base, filter | wheel ≤ 23/37 (v1) | wheel ≤ 47 | candidates saved |
|---|---|---|---|
| b = 4, n = 19 | 7.05×10⁻³ | 5.08×10⁻⁴ | **13.9×** |
| b = 2, n = 17 | 7.27×10⁻⁷ | 2.36×10⁻⁷ | **3.1×** |

This is the same lever that paid 4.3× end-to-end in square-ladders, and it
is larger here because v1 starts further from the wall. It also replaces
the 12.6 MB table that makes `SCORE` unresolvable (finding 3), so its
measured value should exceed its predicted one — which is precisely the
kind of claim that must be checked rather than assumed.

**B. The kernel's work per candidate — worth ~5×.** v1 sustains
3.2×10¹⁰ candidates/s. square-ladders' v5 kernel, on the same card,
sustains 1.62×10¹¹ on the same shape of inner loop. The gap is four
techniques, all catalogued there with measured numbers: two rounds of
shared-memory block compaction (the warp pays the deepest early exit, so
compact before the tail), per-prime constants packed into one 128-bit
load, CRT-combining the hottest primes so "killed by 41 or 43" is one
reduction and one lookup, and moving the tail to its own kernel. None of
them is speculative here — they are a port, not a research project.

**Together: about 70×**, which is what turns the table in
[BENCHMARKS.md](BENCHMARKS.md) from "a(19) in 3.5 h, a(20) in 87 h" into
"a(19) in 3 minutes, a(20) in an hour" — and is the difference between a
project that reaches two terms and one that reaches five.

**Order of work, when it is picked up.** A first, because it is a pure
win on both families and it removes the benchmark's own noise floor; B
second, and re-sweep A's constants afterwards, because an optimum tuned
against the old kernel is now wrong (OPTIMIZATION.md rule 4). Measure the
phase split before either — this engine has never been profiled, and the
one time this repo skipped that step it aimed a week of work at the wrong
80%.

## Declined

Nothing yet. When something is declined it belongs here with the price
that made it not worth doing, not in a commit message.
