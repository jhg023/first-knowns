# euler-prime-runs

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A164926](https://oeis.org/A164926): the
least prime p such that Euler's polynomial form **x² + x + p** is prime
for exactly n consecutive values x = 0, 1, ..., n−1.

**Results so far: a(17) = 348,284,517,256,411,907,
a(18) = 8,461,068,614,861,832,371, and
a(21) = 234,505,015,943,235,329,417.** a(17) and a(18) were found and
verified 2026-08-05/06, the first new terms of the sequence since
2009; a(21) was settled 2026-08-12 when the exhaustive sweep passed
the known Waldvogel–Leikauf upper bound at 2.35×10²⁰ without finding
a smaller run ≥ 19. Details in [RESULTS.md](RESULTS.md).

**Status: ACTIVE** — hunting a(19). The sweep is contiguous from
0 to **1.056×10²¹**, so a(19) and a(20) both exceed that. Conditional
on the empty sweep so far, the model puts a(19) at median 1.82×10²¹
(quartiles 1.36×10²¹ / 2.74×10²¹); the current leg runs to 5×10²¹, ~94%
of the conditional distribution. The engine was rebuilt 2026-08-15
(bit-sieve stage 1a, then a 31# wheel) for ~19x and sharpened three times on
2026-08-16, by 1.294x, 1.055x and 1.329x — cumulatively **~32x**, measured
against a realized 5.5×10¹⁴ p/s on the engine that swept leg 1 — with a
bit-identical survivor stream throughout, proven by paired A/B against the
engine each version replaced and still pinned by G6/G13/G14/G15 and the
unchanged fingerprints. That puts the a(19) median ~12 hours out.

## The problem

Euler noticed in 1772 that x² + x + 41 is prime for x = 0..39 — forty
primes in a row before 40² + 40 + 41 = 41² breaks the run. Rabinowitsch's
theorem explains the miracle: x² + x + p is prime for all x = 0..p−2
exactly when the field of discriminant 1−4p has class number 1, and by
the Heegner–Baker–Stark theorem there are only nine such discriminants.
So Euler's "lucky numbers" {2, 3, 5, 11, 17, 41} are provably the last
of their kind, and any prime with a long run beyond them is a *generic*
statistical object, findable only by search.

Define run(p) = the number of consecutive x from 0 with x² + x + p prime.
A164926(n) is the least prime with run exactly n. Before this project:
a(1)–a(16) known (a(15) = 291,598,227,841,757, Andersen 2009), then a
17-year gap — **a(17) through a(20) unknown**, with a run-21 example
234,505,015,943,235,329,417 known as an upper bound for a(21) (from a
construction-style search, so not a confirmed least).

There is no known upper bound for a(17)–a(20): every new segment of the
sweep could contain the find. That is what makes it a hunt.

## The mathematics of the engine

A prime p has run ≥ 17 only if none of the 17 values x² + x + p
(x = 0..16) has a small prime factor. For each prime q, the forbidden
residues of p are −(x²+x) mod q — about min(17, (q+1)/2) classes. One
engine covers the whole range:

**0. Representation.** p is never held in a machine word. Every candidate
is the pair (k, off) with p = k·31# + off, so every sieve test reduces to
`((k mod q)·(31# mod q) + off mod q) mod q`, which stays 64-bit-safe to
the enforced ceiling 10²⁴ — a factor >3 under the Miller–Rabin validity
bound. There is no 2⁶⁴ boundary in the search: the same code sweeps 10⁵
and 10²³, and exact integers exist only on the host as Python ints.

**1. Wheel.** p is generated only in residues mod 31# = 200,560,490,130
that survive all wheel primes 2..31 — 1.5×10⁻⁴ of the line. The wheel is
chosen per n as the largest whose offset table fits a memory budget
(2.99×10⁷ offsets at n = 17; the same table would be 5.4×10⁸ at n = 5, so
the small-n gate cases fall back to 29#). Folding a prime into the wheel
generates ~2x fewer candidates for a *mathematically identical* survivor
set — the wheel only decides which primes are tested by generation rather
than by sieving — which is why both frozen fingerprints still reproduce.

**2. Stage 1a, the bit-sieve.** For prime q, if a block of 64 consecutive
wheel periods starts at residue r, then period offset u is killed by q
exactly when `(r + u·(31# mod q)) mod q` is forbidden — a function of
(q, r) alone. So the host precomputes `pat[q][r]`, a 64-bit kill pattern,
and the kernel ORs **one word per prime per 64 periods** for the first 26
stage-1 primes, then reads survivors straight out of the complement with
`__ffsll`. Those words are stored in *visit order* — the index sequence for
prime q is `(r₀ + s·dmw) mod q`, and dmw is invertible mod q, so storing
`G[m] = pat[m·dmw mod q]` makes the walk stride-1 and shared by every prime,
which collapses the per-prime residue step into one pointer bump. Nothing is
tested per candidate, so there is no per-candidate
state to step and no early-exit branch to diverge on — which is the point:
the obvious "test each candidate, exit early" loop spends most of its
instructions maintaining state for primes the average candidate never
reaches, and a warp runs until its *last* lane dies.

Seeding those residues is not free — each thread reduces k and its offset
against all 26 primes before the loop starts. So the grid is shaped to pay it
as few times as possible: the periods-per-thread T is *derived* from the
launch size rather than fixed, chosen so the grid's y-slices come out even
and, at the production launch size, so there is only one of them. Measured by
sweeping the window and fitting, the sieve costs
`~36 + ~21·words` ms per 10⁹ threads, so seeding is now ~2.5% of it.

A survivor is pushed as the pair (offset, period). The queue stores the
offset's **value**, not its index, because every downstream consumer would
otherwise have to gather it back out of a 240 MB table — a scattered read per
entry per round for a number the sieve already had in a register. The two
fields share 64 bits under a split derived from the wheel period and refused
if a launch could ever overflow it.

**3. Stage 1b, compaction rounds.** The remaining stage-1 primes (to
1024) are tested 16 at a time, with survivors forwarded to a second queue
between rounds and counts kept on the device. Its exit depth averages
13.9 but maxes at 80.4 across a 32-lane warp, so restarting each round
with every lane alive recovers most of that 5.8x. Each round is its own
**generated kernel** with its primes unrolled and their moduli, magics and
mask offsets as literals: the indexed loop read six warp-uniform values per
prime out of global arrays, and five of them are properties of the prime.
Only one of the modular reductions per candidate-prime needs 64 bits — *k*
itself is never formed, because the host knows k mod q and the candidate
carries its period offset in the low half of its queue entry — and even
`off mod q` does not, since `off = a·2ˢ + b` with s chosen so that
`a·(2ˢ mod q) + b` clears 2³² for every prime in the stage. **G15** checks
that bound at its worst case rather than trusting it.

**4. Stage 2.** Primes 1024..65536, one thread per surviving candidate.
The kill test is not a scan over the 17 values of x²+x but a single bit
probe: q divides one of p + x² + x exactly when p mod q is 0 or
q − (p mod q) is itself of the form x² + x, which is a valid restatement
precisely because every stage-2 prime exceeds max(x²+x) = 272. Gate
**G15** pins that equivalence against big-integer divisibility, including
its precondition — and the same restatement is used for the stage-1 primes
above 272, where it replaces a gather into the ~10 KB forbidden-residue mask
with a probe of the same 36-byte table. Its residue reduction uses the same
splits as stage 1b, with its **own** split point: these primes reach 65521,
so the product has 64x less room, and the engine derives s per stage rather
than sharing one.

**5. Host classification.** The ~3.6×10⁻¹³ of the line that survives goes
to the host, where a deterministic 7-base Miller–Rabin (valid to
3.3×10²⁴) computes each survivor's exact run. The GPU only ever
*proposes*.

Arithmetic is Barrett magic-multiply throughout (no hardware 64-bit
division; see `../huntlib/gpu.py`), and its exactness is never assumed:
gate **G6** pins the whole GPU stream bit-for-bit against an independent
numpy-`%` engine on populated windows at seven heights up to the ceiling.
That engine is itself pinned against direct big-integer trial division on
mini-windows (G10) and against the sympy oracle on small windows (G4);
**G13** proves the stream does not depend on how work is sliced — into
pattern words, threads, launches, *or offset chunks*, since a launch is also
cut along the offset axis so the queue is bounded by how many offsets are in
flight rather than by how many periods a launch spans; **G14** pins the
sieve's pattern tables directly against big-integer divisibility of the
actual values, in both layouts; **G15** does the same for the bit probe and
the 32-bit reductions, checking the *preconditions* that make them valid
rather than only their output; and the pipeline rediscovers a(13), a(18) and
the Waldvogel–Leikauf run-21 value end-to-end (G8, G12, and the launcher's
canary prelude).

This shape was reached by measurement, not design intuition, and the
constants interact: the sieve depth went 28 → 24 once compaction rounds
made stage 1b cheaper, back to 28 once the wider wheel shifted the sieve's
prime range upward, then **28 → 26** once baked round kernels cut stage 1b
by 2.4x and made handing a prime *back* to it the better trade; the round
size went 8 → 16 → 24 and then **24 → 16** for the same reason. Every one of
those moves was a re-sweep after a structural change, and two of them
reversed direction.

What the sieve is bound by has been established by attacking it from both
sides, and both answers are negative. It is **not instruction-bound**:
removing two of about six instructions per prime per pattern word (the
visit-order table) is worth 1.007x, hoisting the edge mask 0.999x, narrowing
the prologue's arithmetic 1.006x. It is **not sector-bound** either:
collapsing a warp's 26 gathers from 17.3 distinct 32-byte sectors down to 1
buys only 1.53x, and not monotonically. It counts *load instructions* — which
is why a wider 128-bit pattern word loses 5x, folding the table 24x smaller
loses 1.5x by turning one load into two, and CRT-pairing primes dies on the
footprint cliff (0.62x at 86 KB, 0.14x at 172 KB). The only lever that
removes loads is generating fewer candidates, i.e. a wider wheel — measured
at **1.85x** on production-shaped launches. It was blocked on the benchmark
rather than the engine: the frozen 5×10¹⁴ window holds 2,494 periods of the
31# wheel but only 68 of the 37# one, so it reports that change as a *loss*.
A third frozen shape, [6.11×10²⁰, +2×10¹⁶), was added to resolve it — see
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

The sieve's *other* term is per-thread setup. It was 17.4% of the kernel;
halving the thread count (one grid slice instead of two) beat making each
thread's arithmetic cheaper, 1.022x against 1.015x, which says that term is
mostly thread overhead rather than instructions — and with T now derived from
a larger launch it is down to 2.1%. That measurement is also what prices the
next wheel: 37# generates 1.85x fewer candidates, and once the queue stopped
capping the launch's period count it measures **1.85x** on production-shaped
launches. It measures 0.58x on the frozen 5×10¹⁴ window, which holds only 68
of its periods — a blocker in the benchmark's shape, not the engine's.
Amending the anchor that makes scores comparable across engine generations is
a human's call, not an optimizer's, so the anchor was not amended: a third
frozen shape was **added** beside it, wide enough to hold 2,696 periods of
the wider wheel, and the two originals still reproduce bit-for-bit. Net
**~32x** over the engine that swept leg 1,
with both frozen fingerprints reproducing bit-for-bit — the engine got
faster without the work changing. See
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) for every attempt including
the rejects, and [../OPTIMIZATION.md](../OPTIMIZATION.md) for the process.

Throughput on an RTX 4090 (see BENCHMARKS.md). The engine scores **SCORE
16,307,051,103**, **SCORE128 16,325,330,842** and **SCORE_WIDE
16,662,037,996** on its three frozen windows — but absolute scores on this
machine swing by ~2x between captures of identical code (the same engine, the
same session, has read 13,198,517,241 and 20,917,761,353 on the first of
those), so BENCHMARKS.md quotes paired ratios and so should you.
Its immediate predecessor realized **1.232×10¹⁶ p/s in production** over a
10-hour leg; applying the paired 1.329x ratio projects **1.64×10¹⁶ p/s**,
i.e. **~30x** the 5.5×10¹⁴ the leg-1 engine averaged. At that rate
re-sweeping everything from 0 to 5×10²¹ costs ~3.5 days, and the enforced
10²⁴ ceiling is ~1.9 years of single-GPU wall (it was ~58). For historical
reference the retired u64-only kernel scored 512,819,184 (5.1×10¹⁴ p/s) and
took ~9.5 hours to cover the 64-bit-safe range.

## The odds model

`euler_model.py` computes the Bateman–Horn prediction with numerically
evaluated singular series (primes to 2×10⁶, tail bounded). Validation:
the six known generic terms a(9)–a(15) sit at model quantiles
.99/.56/.41/.23/.83/.64 — scattered, as an honest model's knowns should
be. Out-of-sample performance so far: a(17) landed at quantile 0.69
(median predicted 2.6×10¹⁷); a(18) landed at quantile 0.63, essentially
exactly at the predicted E = 1 depth (found 8.46×10¹⁸, predicted
8.58×10¹⁸); the run-17 census closed at 8 against an expected 11.6
(within Poisson scatter). The model is two-for-two on out-of-sample
terms.

Predictions for phase 2, restated as the sweep consumes them. Stated
before leg 1 (conditional on the empty 64-bit tail, E = 0.20 spent):
a(19) median 2.6×10²⁰, quartiles 8.9×10¹⁹ / 6.8×10²⁰, and 48% odds of
landing below the Waldvogel–Leikauf run-21 value at 2.35×10²⁰. Leg 1
then came back empty to 3.2×10²⁰, which is a 36% outcome on its own
terms (E = 1.02 spent) and is also what settled a(21).

Conditional on the sweep now being empty to 3.6004×10²⁰ (E = 1.09 spent
for run ≥ 19): **a(19) median 8.34×10²⁰, quartiles 5.38×10²⁰ /
1.45×10²¹**, 98% by the current leg cap of 5×10²¹. a(20) is far deeper —
median ≈ 8×10²¹ conditionally, unconditional E = 1 at 1.1×10²² — so the
two open terms are not comparable targets, and both are already known to
exceed a(21).

## Running it

```
python launch.py --selftest    # full gate battery + drills (~15 min)
python launch.py --stop-on-discovery
                               # THE HUNT: resumes at the frontier
                               # (3.62e20), runs to 5e21 (~98% of the
                               # conditional a(19) distribution), halts
                               # after a frontier-extending find
python launch.py --status      # scoreboard
python score.py                # gates x fingerprinted benchmarks
python euler_model.py          # rebuild the odds model + its gates
```

**One engine, one cursor, no flags.** Every candidate is carried as the
pair (k, off) with p = k·29# + off, which is as valid at 10⁵ as at 10²³,
so a single sweep runs from the oracle floor to the enforced ceiling
10²⁴ with no seam at 2⁶⁴ and nothing to select. The GPU is always used.
`--engine cpu` selects the numpy reference engine, which exists for
verification and gating — it is orders of magnitude slower and would
never finish a production leg.

The superseded engines — the u64-only kernel and the pre-bit-sieve 128
path — have been **deleted**, not parked. They existed to prove the
replacement produced an identical stream; that gate ran green and was
committed, so the proof lives in the git history rather than in a module
nothing calls. The tree is the answer to "what runs if you start this
from zero", and that question has one answer.

What is permanent is the *independent* reference: `euler_search.py`'s
numpy engine, which the GPU is pinned against by G6 on populated windows
at seven heights up to the ceiling. That is not an old version, it is the
other half of the parity gate.

`--stop-on-discovery` follows the repo-wide convention (CONVENTIONS.md):
only a run beyond the campaign frontier (currently ≥ 19) halts the hunt;
run-17/18 repeats are verified, evidenced, and counted as census
(`near13-18` in the status line). The known run-21 value at 2.345×10²⁰
was treated as an in-flight canary, not a discovery — rediscovered on
schedule 2026-08-12 and thereby settled as a(21) (see RESULTS.md).

Requires Python 3.12+, numpy, sympy, CuPy + CUDA GPU (or `--engine cpu`).

The launcher preludes every fresh campaign with an exhaustive oracle
sweep of [2, 10⁵) — during which Euler's 41 (run 40) fires the complete
discovery protocol as a positive control — and with mini-hunts that must
rediscover a(14) and a(15) end-to-end before production is allowed to
proceed.

## Trust

This project follows the repository-wide [CONVENTIONS](../CONVENTIONS.md):
three independent implementations (oracle / CPU / GPU) with bit-parity
gates on populated windows up to the 64-bit ceiling, in-stream canaries,
planted-fake and resume drills, and a three-way verification protocol
with factor witnesses on every discovery. See `evidence/` for the
verifiable artifacts.
