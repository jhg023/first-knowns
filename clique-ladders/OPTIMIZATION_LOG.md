# OPTIMIZATION_LOG — clique-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

Every attempt → measurement → kept/rejected, failures included. This
project starts from factorial-ladders' engine v3, whose own log holds the
rounds that produced it (the 2^64 reduction bound, the wide survivor record,
the subset wheel, the segment capped at the median); what is here is what
was measured and decided in making that engine hunt a different object.

---

## Measurement 1 (2026-09-19) — the ceiling, because this project is rule 5h's exception

The values are x + a(i) + 1, 2x + 1 and x. V − 1 = x + a(i) is an integer
with no structure, so the repository's usual route — one factorization of k
proves the whole run — does not exist here, and CLAUDE.md 5h allows a lower
ceiling "only with a measurement that says why". So it was measured before
anything else was written: `huntlib.ceiling.subproof_rate(height, samples=12)`
— random primes near `height` through `huntlib.certificate.prove`, each proof
re-verified.

| height | proved | slowest |
|---|---|---|
| 1e25 | 12 / 12 | 0.03 s |
| 1e27 | 12 / 12 | 0.15 s |
| 1e30 | 12 / 12 | 0.14 s |
| 1e33 | 12 / 12 | 0.26 s |
| 1e36 | 12 / 12 | 0.37 s |
| 1e40 | 12 / 12 | 0.49 s |

**Decision: the ceiling is `huntlib.ceiling.K_CEIL` = 1e40, as everywhere
else.** A 40-digit V − 1 factors completely by bounded rho and ECM well
inside the certificate budget, so the structureless case costs nothing at
these sizes. G10 repeats the measurement at the ceiling on every battery (8
of 8), and the certificate drill repeats it on this project's own values:
two per family just past the proof crossing and two per family at the
ceiling, 24 of 24 proved, two of them carrying a subproof for a prime factor
past the deterministic bound, which cannot be stripped. It will rarely
matter: the proof crossing is x ≈ 1.66e24 (where 2x + 1 is a form) and
3.3e24 (elsewhere), above every term the campaigns can reach in weeks.

---

## Decision 1 — sweep the forced CLASS, not x

**The problem.** A forced prime leaves x one residue class, and here it is
generally not 0: x ≡ 2 (mod 6) for A093483, 9 (mod 30) for A103828. The
inherited engine sweeps x = unit·x′, the multiples of a unit, which is only
sound when the surviving class is 0.

**First design, rejected before it was built:** unit = 1 always, the forced
primes taken by the wheel (a prime that keeps one class in q is the best
value a wheel can buy, and the planner would take them first). It is
correct and it costs nothing in candidates — but the period bound is on the
period *in the swept variable*: W′ + q2 < 2^64 on the narrow record. With
2·3(·5) inside the wheel the same prime set has a period 6 or 30 times
longer in x than in x′, which is one to two wheel primes of room and the
whole of v2's window win (179 periods at the wheel to 47 becomes 5). Priced
from factorial-ladders' round 2: about 1.2× at the filters the narrow record
serves.

**Built instead:** the engine sweeps t with **x = r + u·t**. The killed
residues are carried through the map, t ≡ (k − r)·u⁻¹ (mod q); a prime of
the unit kills nothing; the host maps back in the one place the value is
rebuilt. Because r < u, x < j·W ⇔ t < j·W′, so the periods share their
boundaries and the coverage cursor needs no change. **Two lines of the
engine core, one new attribute (`r0`), and the kernel cache key** (which
used the sign as "the whole of the family" and must now use the family:
the kill sets are literals in the kernel source).

Proved by G3 (the t kills map back onto the x kills, both directions, 2,867
cases; r is the one class the *oracle* leaves free), G7 (the class-space
wheel == the oracle's divisibility on x = r + u·t), G9 (GPU == dense CPU
sieve, which knows nothing of r or u, on windows at unit 6 and unit 30),
G13, G15 and G17 (every survivor in the class).

---

## Decision 2 — a find restarts the sweep; nothing is carried

factorial-ladders' v2 carries the classified line across a promotion and
saved ten minutes a promotion by it. That is sound there because its forms
do not depend on the find. Here a(n) creates the condition x + a(n) + 1, the
old filter never tested it, and carrying the line would be a **coverage hole
one segment wide** with every gate green — the survivors past the find in
that segment were classified, just not against the right conditions.

So `follow_frontier` restarts on the period that holds the find, clipped
just above it; the segment loop stops narrating at the first find and drops
the rest of that segment's survivors uncounted (they are re-swept and
counted once under the new filter). The cost is at most one old segment,
which the planner capped at the old index's median when this was written
and has PRICED since round 1 (below). `_promotion_drill` asserts
the restart in every family with the old filter's sweep placed five segments
past the find, and `_rediscovery_run_drill` runs the real loop through two
finds.

---

## Measurement 2 (2026-09-19) — every opening priced (5c, 5g)

A family has one opening, so "every opening the launcher has" is six
configurations. The campaign's own `calibrate()` on a scratch checkpoint at
each (real launches swept and timed, survivors counted, a 2,000-survivor
sample classified):

| family | n | class | window | device | survivors/s | µs each | core-s/s | pool |
|---|---|---|---|---|---|---|---|---|
| A093483 | 18 | mod 6 | 128 | 6.3e16 x/s | 125,000 | 10.7 | 1.34 | 3 |
| A103828 | 19 | mod 30 | 224 | 1.7e17 | 88,000 | 11.9 | 1.05 | 3 |
| A037100 | 19 | mod 6 | 32 | 4.3e16 | 45,000 | 9.3 | 0.42 | 1 |
| A119752 | 15 | mod 6 | 192 | 1.2e16 | 62,000 | 16.5 | 1.02 | 3 |
| A119751 | 15 | mod 30 | 224 | 1.7e16 | 56,000 | 17.5 | 0.98 | 2 |
| A133761 | 17 | mod 30 | 224 | 1.2e17 | 53,000 | 11.3 | 0.60 | 2 |

The device side binds at none of them by more than the pool can absorb, and
the pool is sized at runtime from exactly this measurement. Candidate rates
(frozen shapes, `score.py`): 2.4–2.6e12 a second at five openings, the
inherited engine's figure, and 1.07e12 at A037100's (the 32-period window
its plan was left with; closed in round 1, below).

Every open term is seconds at its median. The terms that will cost hours
are at filters that do not exist yet.

---

## Battery and score (2026-09-19)

`python launch.py --selftest`: **47/47 ALL GREEN in 209 s** — 5 oracle, 5
CPU, 11 GPU, 2 model, huntlib's certificate and ceiling gates, the standard
drills, and this project's: canary (eight published terms rediscovered by
the GPU stream as first occurrences, every family, x space and class
space), protocol, ceiling, certificate, resume, promotion, classification,
stop-on-discovery, families-stay-apart, campaign wiring, **the real loop on
published ground** (`Campaign.run` finds a(13), promotes itself, finds
a(14)), and evidence names.

`python score.py`: every gate green, all nine fingerprints reproduced,
**SCORE 52,880,847,125** in 183 s.

Ten of the eleven inherited GPU gates passed unmodified in logic on the
first run after the form list and the class map went in, including parity
on 28 populated windows; the eleventh asserted factorial-ladders' specific
plan ("the wheel to 53 at n = 18") and now asserts the rule it stood for
(the planned wheel takes the wide record exactly when no u64 window admits
its period).

---

## Round 1 (2026-09-19) — the campaign, priced where its hours are; planner p2; the block shape; the sieve depth

The project was built on an inherited engine with every constant inherited
and an instruction to sweep "at the first filter that costs more than a few
minutes". Those filters do not exist yet — but the model's **stand-ins** do
(`clique_model.stand_in`: the first x past the projected median that
survives every prime under 2000, so it has the small-prime residues a real
term must have), and `clique_reference.register` accepts them *in a scratch
process*. So every measurement below that names an index past the open one
was taken on a stand-in filter, through the engine API, on windows fifty
medians above any campaign floor, with nothing classified. All ratios are
medians of 3–4 interleaved rounds of 1.0–1.5 s per configuration; the
survivor stream was checked identical wherever two configurations cover the
same candidates.

### Measurement 3 — where the hours are (the inherited plan, A093483)

| filter | plan (wheel × window) | x/s | candidates/s | segment / median | device to the median |
|---|---|---|---|---|---|
| n = 18 (open) | to 41 × 128 | 6.44e16 | 2.88e12 | 0.83 | 0.7 s |
| n = 19* | to 43 × 160 | 1.31e17 | 2.97e12 | 0.92 | 17 s |
| n = 20* | to 47 × 64 | 1.58e17 | 2.42e12 | 0.88 | 4.7 min |
| n = 21* | to 53 × **32**, wide | 1.69e17 | **1.56e12** | 0.92 | **1.9 h** |
| n = 22* | to 53 × 224, wide | 3.92e17 | 3.12e12 | 0.20 | 26 h |

(* stand-in.) Two things are wrong with the n = 21 row, and they are the two
halves of this round. The planner maximised candidate *density* under a hard
cap (segment ≤ one median), so it took the longest wheel and then the only
window the cap left — and a 32-period window runs at **half** the candidate
rate. And the cap itself was priced in factorial-ladders, where a promotion
carries the classified line; here a find **restarts** the sweep (Decision
2), so the rest of the find's segment is thrown away, and a segment of 0.9
medians is an expected 19–21% of waste that the cap treats as free.

### Measurement 4 — the block shape follows the window's width: 1.05–1.28×

Why is a narrow window slow? Per-thread and per-block fixed work (the x0
loads, the warp-wide reservation and its shuffle chain) is amortised over
`spb` second-level residues × `pb` periods, and the inherited (spb, xe) =
(8, 1) — (8, 4) at NW = 2 — was tuned at NW = 2 and NW ≥ 5 only. Swept at
n = 21* on the wheels to 47 and 53, and confirmed at three real openings
(A093483 n = 18 and n = 20*, A037100 n = 19), candidates/s against the
inherited pair:

| NW (periods) | best (spb, xe) | ratio | runners-up |
|---|---|---|---|
| 1 (32) | (32, 8) | **1.20–1.28** | (32,4) 1.18–1.26, (16,8) 1.22, (8,8) 1.09, (64,1) 1.04 |
| 2 (64) | (16, 8) | 1.05–1.07 | (16,4) 1.04, (16,2) 1.03, (32,4) 0.86 of the 192 rate |
| 3 (96) | (16, 4) | **1.13** | (16,2) 1.11, (8,4) 1.06, (8,2) 1.04 |
| 4 (128) | (16, 2) | 1.05 | (8,2) 1.02, (16,1) 1.01, (16,4) 1.01 |
| 5 (160) | (8, 1) | — | (16,2) 1.004, (16,1) 0.95 |
| 6 (179/192) | (8, 1) | — | xe 2 1.007, xe 4 0.99, spb 16 0.97 / 0.89 |
| 7 (224, wide, n = 22*) | (8, 1) | — | xe 2 0.98 (a block lost: 21.5 KB), spb 4 0.95, spb 16 **0.135** — the shared queues pass `QUEUE_BYTES_MAX` and every block takes the in-block fallback, the inherited cliff |

**Kept**, as a *preference list* per width (`BLOCK_SHAPES_BY_NW`): the
engine takes the first shape whose predicted occupancy reaches
`OCC_MIN_BLOCKS4`. The list exists because G18 caught the first version: the
table went in as a pair, and (16, 2) at n = 17 of A133761 is 20,788 bytes of
shared memory and **4** blocks per SM — a lost block is ~8%, more than the
shape buys. The stream is identical at every setting (40,528 survivors and
one xor over the same six launches at five settings). The in-block rounds
keep their survivors in ONE 32-bit mask per thread, so a queue of more than
32 × tpb entries would silently drop items; nothing shipped is near it
(17–22), and the engine now raises rather than shifting past the word.

What it buys beyond the rate: the candidate rate is now **flat from 96
periods up** (0.95 / 1.00 / 0.99 / 1.02 / 1.06 at 96 / 128 / 160 / 192 /
224 on the narrow record), so a shorter segment has stopped costing
throughput.

### Measurement 5 — planner p2: the plan is priced in expected clock to a CONFIRMED find

`clique_model.expected_sweep(fam, n, floor, start, seg)` is the model's
expected line swept until the segment holding a(n) closes: Σ over segments
of seg × P(a(n) ≥ segment start), from one cumulative table of the survival
curve per (family, index, floor). `clique_gpu.plan` minimises

    expected_sweep(pv × W) × density(wheel) / crel

over every greedy wheel subset the kernel admits × every window width, with
`crel` = (measured width curve) × (0.93 on the wide record) / (window depth
`lit`). The hard cap, `plan_pb` and `search_segment_cap` are gone.

**The first version of the rate model was wrong, and the paired check
caught it.** It had no depth term, and at n = 20* it ranked the wheel to 47
at 96 periods over the wheel to 43 at 224; measured, the second is 6%
better (710 s against 753 s of expected clock). The reason is
OPTIMIZATION.md 2.8's second price of a wheel prime: taking 47 into the
wheel takes the sieve's strongest killer, so the window needs 27 primes
where it needed 26, and the kernel is per prime. `window_depth` computes
`lit` analytically at plan time (G18 pins it to the engine's own), and with
it the plan is the measured best at every filter checked:

| filter | plan p2 | measured expected clock | the alternatives, measured |
|---|---|---|---|
| A037100 n = 19 (open) | to 41 × 224 | **29.6 s** | p1's to 43 × 32: 38.0; to 43 × 96: 30.7; to 41 × 128: 32.3 |
| A093483 n = 20* | to 43 × 224 | **710 s** | p1's to 47 × 64: 763; to 47 × 96: 753; to 47 × 128: 774 |
| A103828 n = 20* | to 47 × 128 | **885 s** | to 47 × 96: 888; to 47 × 192: 925; to 43 × 224: 988 |
| A093483 n = 21* | to 47 × 128 | **12,220 s** | to 47 × 179: 12,610; to 47 × 96: 12,820; to 43 × 224: 15,900; p1's to 53 × 32: 16,290 (20,300 at the inherited block shape) |
| A093483 n = 22* | to 53 × 224, wide | **2.50e5 s** | to 53 × 160: 2.59e5; to 47 × 128: 3.24e5; to 47 × 179: 3.28e5 |

At n = 21*, the first filter that costs hours, that is **1.66×** on the
clock to a confirmed find (1.46× in line rate, the rest in a segment of
0.07 medians instead of 0.92), and a find there is confirmed within 7
minutes of being swept instead of within 1.7 hours. `_families_stay_apart`
now asserts the priced form of the old margin (the plan's expected sweep
within 1.5× of the unavoidable one; the worst opening is 1.21×) **and that
every campaign benchmark shape names exactly what the campaign plans** — a
planner change otherwise leaves the shapes scoring a configuration nothing
runs, which is what this round would have done.

Planning is ~0.3 s per filter at the live indices (one survival table, a
dozen wheels); the sieve walk is now shared between a filter's candidate
wheels (`_rung_survival`), which took the early drill filters from 3–6 s to
under 2.

### Measurement 6 — the sieve depth: five times fewer survivors for 0.3–0.6%

The device rate is flat in q2 and the inherited target stopped at "two
workers keep up". Swept at six filters of 17–21 forms:

| filter | depth | device | survivors per candidate |
|---|---|---|---|
| A093483 n = 18 | 2^15 → 2^17 | 0.995 | 4.6e-8 → 5.4e-9 |
| A103828 n = 19 | 2^15 → 2^16 | 0.997 | 2.8e-8 → 8.9e-9 |
| A093483 n = 20* | 2^14 → 2^16 | 0.994 | 4.3e-8 → 3.4e-9 |
| A093483 n = 21* | 2^14 → 2^15 | 0.998 | 2.8e-8 → 7.0e-9 |
| A119752 n = 17* | 2^16 → 2^17 | 0.997 | 2.3e-8 → 8.0e-9 |
| A093483 n = 22* (wide) | 2^14 → 2^16 | 0.994 | 1.7e-8 → 1.1e-9 |

**Kept: `SURV_TARGET_DEEP` = 1e-8 from 17 forms up** (rule 5f: a tie on
throughput goes to the setting that asks for less machine). 130,000
survivors a second become 15–25,000; 1.3 core-seconds per second and a pool
of three become 0.2 and one worker, for the days a late filter runs. It buys
machine, not rate: the launcher's own host path (`_submit` → pool → drain →
back-pressure, driven from a scratch harness on a far window) measured
**1.000** of the device alone at 2^14 with three workers, 1.001 at 2^16 with
one, 1.000 at 2^18 inline, and 0.959 at 2^16 inline — so inline needs the
last rung. Not below 17 forms: at n = 15 of A119752 a rung costs 0.948
(the launches are 3 ms and the tail's extra rounds are a visible fraction
of each). Deeper still, priced and declined: 2^18–2^20 costs 1–3% to take
the last worker inline. A deeper sieve also narrates ~12% fewer `[NEAR]`
lines (a one-short value whose failing form has a factor under the depth is
never a survivor at any depth).

### Measurement 7 — the constants, re-swept at the new shapes (n = 21*, to 47 × 128; n = 22* wide)

| knob | values | ratios | verdict |
|---|---|---|---|
| `BIT_SURV` | .012 / **.007** / .0045 / .003 | 0.934 / 1.000 / 0.976 / 0.918 | unchanged |
| `K2_SURV4` | .001 / **.0003** / .0001 / 5e-5 / 2e-5 / 1e-5 | 0.930 / 1.000 / 1.018 / 1.018 / 0.996 / 0.956 | **a tie**: 1e-4 reads 1.018, 0.999 (wide), 0.992, 1.015, 1.013 at five filters, mean 1.007 |
| `R2_DROP` | .7 / **.5** / .35 | 0.932 / 1.000 / 1.003 | unchanged |
| `TAIL_ROUND_DROP` | .5 / **.7** / .85 | 1.000 / 1.000 / 0.962 | flat |
| `CAND_PER_LAUNCH4` | 2^36 / **2^37** / 2^38 | 0.995 / 1.000 / 1.003 | unchanged |
| `CAND_PER_LAUNCH_WIDE` | 2^37 / **2^38** / 2^39 | 0.995 / 1.000 / 1.005 | flat here (factorial-ladders read 1.109); 2^37 would save ~500 MB — re-price at a second wide filter before moving it |
| `tpb` | 64 / **128** / 256 | 0.969 / 1.000 / 0.221 | unchanged |

### Measurement 8 — the phase split, and what is inside the sieve kernel

CUDA events at the planned configuration: the sieve kernel is **93.5 / 93.3
/ 91.3%** of device at n = 21* / 22* / 18 and the 25–27 tail rounds the
rest; instrumented wall equals plain wall to 1%. Inside the kernel, by
ablation at n = 21* (OPTIMIZATION.md 3.3, differential forms):

| part | share of wall | how it was priced |
|---|---|---|
| the window sieve | **56%** | every window group emitted a SECOND time reading the same window at the pattern's other period (r ± Q — the table holds two), so the results are bit-identical (15,155 survivors, same set), the compiler cannot fold the copy (a third identical copy *was* folded: 1.554 against 1.557) and the instruction mix is the window's own: 1.557× the time |
| the in-block rounds' items | **15%** | timing-only: `nq0` forced to zero through a never-true compare (0.782 of the time, less the 6.5% tail) |
| per-block and per-thread prologue, the five round reservations | 12% | the remainder |
| extraction pushes | 8% | the same, with the q0 count forced to zero |
| the tail rounds | 6.5% | CUDA events |
| the q0 reservation (shuffle chain + atomic) | 1.7% | the same, with the reservation deleted |

### Measurement 9 — the segment loop's wall clock, off-device

The measurement neither a benchmark nor a gate can make (OPTIMIZATION.md
2.14). The campaign's own per-launch methods, timed on a scratch checkpoint
at the opening of A093483 (a `Campaign` constructed against a temporary
file; `run()` is never called), against a 23 ms launch:

| per launch | |
|---|---|
| `check_rungs` + `ladder()` + `next_rung` | 3.1 us |
| `state()` + `mark_boundary` | 3.8 us |
| `k_min`, `swept_k`, `u_progress` | 0.8 us |
| `check_proof_crossing` | 6.1 us |
| **total, excluding the save** | **13.8 us (0.06%)** |
| `status_line` (the heartbeat, every 30 s) | 14.1 us |
| `save()` (rate-limited to once per 2 s) | 0.91 ms |
| `plan_for`, cached | 0.1 us |

Nothing to find, and the new planner did not put the model in the loop: it
is reached only through `plan_for`, which is cached per (family, filter).
With Measurement 6's pipeline figure (1.000 of the device through the
launcher's host path) the campaign loop is the device.

### Termination table (OPTIMIZATION.md Part 3), as it stands

| phase | share | verdict |
|---|---|---|
| the campaign's plan | — | **optimization**: planner p2, 1.66× on the clock at n = 21*, 1.24× at A037100's opening, the plan the measured best at five of five filters checked |
| the window sieve | 56% | the block shape (1.05–1.28×); `BIT_SURV` re-swept at its peak. The load count is at 94% information efficiency (lcm-ladders round 9) and the two representation changes that would cut it are priced below and declined on the measured price of a block. **The SASS-level pass is still owed** (INNOVATION.md Part 2) |
| the in-block rounds | 15% | **unsearched as a representation**: every test is a 64-bit Barrett step on a rebuilt offset, and each round rebuilds it (a global load and a 64-bit multiply-add per item per round). Priced candidate below |
| prologue + reservations | 12% | amortisation is what the block shape bought; what is left is per block |
| extraction | 8% | one reservation per XE residues (inherited, 1.10×) |
| tail rounds | 6.5% | compaction rounds, drop point flat over 0.5–0.7 |
| host | 0.2 core-s/s | the pipeline is 1.000 of the device; one worker |
| the campaign loop, off-device | 0.06% of a launch | Measurement 9 |

### Priced and declined, or priced and unbuilt

1. **A find truncates its segment** (sweep the find's remaining launches
   with only the periods up to the find live): worth at most half of
   (expected sweep / unavoidable − 1), i.e. ≤ 0.7% at n = 21*, ≤ 2% at
   n = 22*, 5–10% at filters that cost seconds. It needs a second kernel
   (a narrower window) mid-segment and a work cursor shared across two
   engines. Declined on the price.
2. **Choosing the plan by measurement at each promotion** (build the
   model's top three, time each for a second, persist the choice in the
   checkpoint): the model's residual error against measurement is now ≤ 2%
   at the filters checked (it was 6% before the depth term). Declined; the
   remedy for a mis-rank is a term in `crel`, as it was this time.
3. **The in-block rounds in the window's representation** — a round test
   as one pattern-word load at x0[t] + ne[s] + j instead of a 64-bit
   Barrett step on a rebuilt offset, with no offset rebuilt until the
   global tail. Ceiling 1.18× (the rounds' items free), realistic
   1.05–1.08×; needs a per-residue table for the round primes (~100 MB
   global at R1 = 1.1e6), the second- and third-level terms in global
   tables (shared memory has no room: 18.9 KB of 19.4 at five blocks), and
   a G14 extension. **Unbuilt — the best-priced item on the kernel.**
4. **Word-aligned pattern copies** (4 copies shifted by 8 bits save one of
   NW + 1 loads at 120 periods per 4 words): +8 KB of shared memory is one
   to two blocks per SM (−8% each) against −20% of the window's loads on
   56% of the wall. Declined on the measured price of a block.
5. **`K2_SURV4` = 1e-4**: mean 1.007 over five filters. A tie; unchanged.
6. **Batching windows at the single-launch openings** (n = 15 of A119751 /
   A119752 sweep a 3 ms launch per segment; batched launches are 1.4× more
   efficient per line): those filters last milliseconds. Declined.
7. **Promotion overhead**: a plan (0.3 s), a build (0.5 s from the kernel
   cache, 3–5 s the first time a configuration is ever compiled) and a
   1–4 s calibration per find. Under a minute per family over the whole
   campaign; logged so nobody mistakes it for a stall.

### Round 1 result

`python launch.py --selftest`: **47/47 ALL GREEN in 184 s**. `python
score.py`: 25 gates green, all nine fingerprints reproduced, **SCORE
63,036,572,249** on the re-frozen shapes (BENCHMARKS.md says which columns
of the ledger compare and which do not; on the *unchanged* nine shapes the
block shape alone read SCORE 52,228 → 54,406 and S037100 30,965 → 39,785,
with every fingerprint reproduced). What the round is worth is a clock, per
filter, on A093483's projected ladder (expected, to a confirmed find):

| filter | inherited plan, inherited shapes | now | ratio |
|---|---|---|---|
| n = 18 (open) | 2.5 s | 2.4 s | 1.04 |
| n = 19* | 47 s | 45 s | 1.04 |
| n = 20* | 13.3 min | 11.8 min | 1.12 |
| n = 21* | 5.6 h | 3.4 h | **1.66** |
| n = 22* | 69 h | 69 h | 1.00 |

and at A037100's opening 45 s → 30 s (**1.54×**: 1.20–1.28× from the block
shape on the inherited 32-period window, then 1.24× from the wheel one prime
shorter at a full window). The host
asks for one worker instead of three at every filter from 17 forms up.
n = 22* did not move: its plan was already the measured best, its shape is
the inherited one, and every constant re-swept flat — what is left there is
the kernel (items 1 and 2 under "Open").

### What the gates caught

* **G18**: the block shape as a pair cost a block per SM at one opening
  (above). The fix is the preference list.
* **The paired check** (not a gate — the process): the rate model without
  the depth term mis-ranked two wheels by 6%.
* A harness artefact worth recording: survivors *per second* divided by
  candidates per second differed 4% between two configurations that return
  the identical stream, because `sweep` yields one launch behind. Compare
  streams, not rates of streams.

---

## What the gates did NOT catch (2026-09-19) — the first campaign died 4 s in, on its own find

The first real run of A093483 found a(18) = 20,197,821,613,482,044 inside
its first segment, verified and evidenced it, and then died with a
`KeyError` ("a(18) is not known: the filter for a(19) does not exist until
it is") — 47 of 47 gates green. Nothing was lost: the evidence file had
landed and no checkpoint existed yet. Two bugs, one blind spot:

* **`found` moved before the oracle did.** `record_discovery` set
  `found[n]`, which is what `frontier()`, `filter_n()` and `x_start()`
  read; `ref.register` ran later, inside `follow_frontier`. The loop took a
  boundary snapshot between the two, and `state()` asked for the floor of
  index n + 1, whose conditions need a(n). Fix: `Campaign._settle` — the
  find and its registration are one step.
* **The snapshot aliased `found`.** `state()` stored `self.found` by
  reference, so the boundary snapshot held across a segment acquired a find
  made after it was taken: stored filter n beside `found[n]`, which
  `__init__` refuses. An interrupt between a find and its promotion would
  have written a checkpoint the campaign would not open. Fix: `state()`
  copies `found` and `passed`; and the loop no longer snapshots inside that
  window at all (an interrupt there writes the boundary before the find:
  one segment redone, the find made again, its evidence upserted).
* **The blind spot: drills on published ground.** A drill may not fabricate
  a find, so the promotion and rediscovery drills open at index 13 and
  "find" the published a(13) — which the oracle answers from `KNOWN`
  whether or not the launcher ever registered it. Every read of the new
  frontier before registration was green there and a `KeyError` at the real
  frontier. Fix: `_unpublished(fam, n0)` hides a(n0).. from the oracle for
  the length of the drill (the terms registered are still the real ones,
  and the tables are restored), so the find reaches the oracle through the
  launcher or not at all. With it, the UNFIXED loop fails the rediscovery
  drill in 3.6 s with the production traceback; the promotion drill then
  found the aliasing bug on its first run. Both drills also assert the
  in-window state: `state()` and `status_line()` answer, and an in-window
  interrupt save reopens at the boundary before the find.

The lesson for the next sequential-prefix project: **a drill that stands in
a published term for a find must hide that term from the oracle**, or it
tests a launcher that never needs to tell the oracle anything. Battery
after: 47/47 green in 204 s (promotion drill 39 s, six families), SCORE
62.8e9, fingerprints unchanged (the launcher alone was touched).

---

## Round 2 (2026-09-20) -- an outside review, tested at the LIVE filters

An outside read-only review (no code run) handed over five optimization
hypotheses and one correctness finding. INNOVATION.md Part 4: it gets the
same treatment as our own work, in both directions -- so every item was
measured, at the filters the campaigns are actually sitting at (from the
checkpoints, found terms registered in a scratch process): n = 22 of
A093483, A103828 and A037100 (wide record, the wheel to 53 / 61 x 224),
n = 21 of A119752 (narrow, clamped to 128), n = 20 of A119751 (narrow, 224),
and A133761's opening. Method: the engine API on a window at x ~ 1e27, a
fixed count of 30-40 launches per arm after one warm launch, 3-5 interleaved
rounds, medians, a throwaway warm-up arm first and an A/A arm last (A/A read
0.999-1.001 on a quiet device, to 5% when the desktop was busy -- those runs
were repeated), and the survivor SET compared on every run wherever two arms
share a launch decomposition.

The correctness finding was real and is fixed in huntlib (the seven
Miller-Rabin bases are proved to 2^64, not to 3.317e24; huntlib/README.md,
"Erratum, 2026-09-20"). It does not touch throughput: past 2^64 a PRIME now
costs thirteen exponentiations instead of seven, composites still die at the
first, and the pool is sized from a measurement at the campaign's own filter.

### 1. Shared-queue reuse (ping-pong buffers) -- KEPT, worth ~0.5%, and it pays for item 2

Round r reads queue r - 1 and writes queue r, so queue r can live in queue
r - 2's storage: two buffers, not one per round (`QUEUE_PINGPONG`). The
review's static arithmetic was right -- 3.0-3.4 KB freed and one more block
per SM at every filter -- and its implied payoff was not:

| filter | blocks per SM | ratio |
|---|---|---|
| A119752 n = 21 | 5 -> 6 | 1.022 |
| A133761 n = 17 | 5 -> 6 | 1.012 |
| A119751 n = 20 | 5 -> 6 | 1.006, 1.009, 1.013 (three runs) |
| A103828 n = 22 | 5 -> 6 | 1.005 |
| A037100 n = 22 | 5 -> 6 | 1.004 |
| A093483 n = 22 | 6 -> 7 | 0.997 |

The rate stops tracking blocks per SM at six (at A093483: 5 / 6 / 7 blocks
read 0.991 / 1.000 / 0.997), so the padding ablation's "8% a block" is the
price BELOW five and not a slope to extrapolate. Spending the freed memory
on a bigger block instead lost: (spb, xe) = (16, 1) 0.983 / 0.996 and (16, 2)
0.893 / 1.004 at n = 20 / n = 22. Kept because it is strictly less shared
memory at no cost, and it is what lets item 2 add its rows without losing a
block. The stream is identical everywhere.

### 2. The in-block rounds in the window's coordinates -- KEPT ON THE WIDE RECORD: 1.08-1.10x

Round 1 left this "unbuilt -- the best-priced item on the kernel" at a
modelled 1.05-1.08x. Priced first, by differential ablation at n = 20 of
A119751 (timing-only kernels, never in the tree):

| variant | ratio | reading |
|---|---|---|
| the rounds' items deleted (`nq0` forced to zero) | 1.24 | rounds + tail = 19% of the wall |
| every round Barrett chain emitted TWICE (second copy on offp + c, kept live by a never-true compare) | 0.90 | the chains are ~10% of the wall |
| ... three times | 0.79 | linear: they are THROUGHPUT on the multiply pipe, not latency hidden behind a load |
| the offset rebuild emitted twice | 1.00 | the rebuild is free |

So the ceiling is ~1.10x and it is all in the multiplies. Built
(`ROUND_WINDOW`): the round primes get the window's own tables -- a pattern
indexed in periods (`window_patterns`, reused), a per-residue row x0r[t] and
a per-block row ne2[ss] -- and a test is pattern bit x0r + ne2 + bw + j, no
multiply; bw rides bit 15 of the queue index. The stream was identical on
the first build and on every run since.

| version | narrow, n = 20 | narrow, n = 21 | wide, n = 22 (A093483 / A103828 / A037100) |
|---|---|---|---|
| one u16 load per test | **0.87** | -- | -- |
| rows read 16 bytes at a time (8 slots a word, a round starts on a word) | **0.90** | 1.006 | **1.077 / 1.092 / 1.078** |
| ... with the ping-pong queues | 0.91 | 1.006 | 1.10 / 1.10 / 1.06 |

This kernel is bound by load COUNT, and the two records differ in exactly
that: the narrow test paid one load a prime (the bit table), so the rows are
loads ADDED and they cost more than the multiplies they remove; the wide
test paid two (jb2 and the bit table) and now pays one. So it dispatches on
the record -- wide takes the window coordinates, narrow keeps the Barrett
rounds -- which is also where the hours are: three of the five live
campaigns are on the wide record now (whether the other two follow is the
planner's decision at their next filters, not something measured here).
Forcing the wide record to get the new rounds at n = 21 of A119752 reads
0.976 of the narrow engine: the record's own 5% is still more than the
rounds return there.

Constants re-swept on the new rounds (n = 22 of A103828): `K2_SURV4` 1e-3 /
**3e-4** / 1e-4 / 3e-5 = 0.93 / 1.000 / 1.001 / 0.70; `R2_DROP` .35 / **.5**
/ .7 = 0.96 / 1.00 / 0.84. Unchanged.

G20 gained the drill: the non-contiguous split at q2 = 64 with the window
cut short so six primes run through three rounds and four queues, on the
narrow record (Barrett rounds), the wide record (window rounds, `rwin`
asserted) and the wide record with every queue forced to 32 entries -- each
equal to the CPU engine's 2,339 survivors. **Owed:** no frozen benchmark
shape is on the wide record, because the live filters' terms are not in
`FOUND` yet; freeze one per family at the live filter when they are
published (rule 5g), so the fingerprints pin this path and not only G20.

### 3. Two tuning traps -- both real, both fixed

`ROUND_ILP` became `#define RILP`, which nothing in the kernel read: a knob
that swept nothing. Deleted. `UNROLL` was generated into the source and was
NOT in `_MODCACHE`'s key, so a same-process sweep compared a module with
itself. It is in the key now (with both new flags), and the sweep it had
never really had: UNROLL 2 / **4** / 8 = 0.995 / 1.000 / 0.996 and 0.997 /
1.000 / 1.001 at n = 20 and n = 22. Flat; unchanged.

### 4. The planner's neighbourhood -- the WHEEL is right everywhere; the WINDOW is 4-7% off at two filters. Priced, not shipped

At n = 20 of A119751, expected clock to a confirmed find against the plan
(to 47 x 224): the greedy wheel one prime shorter 1.40, one longer (wide)
1.63; the review's alternatives -- another CRT partition of the same wheel
({7..29}|{31,37}|{41,43,47} 1.024, {7..23}|{29,31,37}|{41,43,47} 1.005) and a
swap at the cutoff (53 for 47: 1.031) -- all lose. `_split_levels`' rule
(largest first level) and the greedy order are the measured best there.

The window is another matter. Candidate rate against the planned width:

| filter (plan) | 128 | 160 | 192 | 224 | 256 |
|---|---|---|---|---|---|
| A119751 n = 20 (224, narrow) | 1.01-1.02 | 1.01-1.03 | **1.03-1.05** | 1.000 | 1.02-1.04 |
| A037100 n = 22 (224, wide) | -- | **1.06-1.07** | 1.008 | 1.000 | 1.05-1.06 |
| A093483 n = 22 (224, wide) | -- | 0.948 | 0.975 | 1.000 | 1.015 |
| A103828 n = 22 (224, wide) | -- | 0.976 | 0.968 | 1.000 | 1.001 |
| A119752 n = 21 (128, narrow) | **1.000** | 0.985 | 0.972 | -- | 0.83 |

(E[line] moves under 0.3% across these widths at the narrow filters and up
to 2% at the wide ones, in the narrower window's favour, so the clock ratio
is the rate ratio or a little better. The wide rows were measured BEFORE
item 2 changed the wide kernel; re-measure before acting on them.)
`CREL_WIDTH` is one curve, measured at n = 19-22 of A093483, and the width response is filter-specific and not even
monotone -- round 1 declined "choose the plan by measurement at each
promotion" on a residual of <= 2%, and at two of the five live filters the
residual is 4% and 7%. **Not shipped here, deliberately**: the window is
the coverage unit, so it is in the cursor key and a change to it is a cursor
adoption (CONVENTIONS.md "Reading an existing cursor") with five live
frontiers behind it -- the owner's call, and its own change. What it is
worth: 1.04x at A119751 and 1.07x at A037100 today, nothing at the other
three; the form that would capture it is the declined item (time the model's
top three windows for a second at each promotion, persist the choice in the
checkpoint), now with a measured price. Whoever builds it should also let
the search reach 256 periods (`plan` stops at 224; 256 ties or wins at all
four 224-period filters).

### 5. Reusing a find's segment under the new filter -- declined on the price, again

The review's form (keep the old filter's survivors past the find and test
the ONE new condition on them, instead of re-sieving) is sound, and it is
round 1's declined item 1 from the other side. Priced from the model at the
live filters (`expected_sweep` at the planned segment against a vanishing
one): the over-sweep is 2.8 / 2.3 / 7.2 / 0.1 / 2.0% of the expected line at
A093483 / A103828 / A037100 / A119752 / A119751 -- half a segment, as it
should be. But that is the price of CONFIRMING the find, and reuse does not
touch it: a launch covers every period of the segment for a slice of the
residues, so least-ness needs the whole segment swept whatever happens
next. What reuse saves is RE-sieving the half segment past the find under
the next filter -- the same line, against the next term's expected sweep,
which is an order of magnitude longer (round 1's ladder: 12 min / 3.4 h /
69 h) -- so 0.1-0.7% of the next term's clock, for a change that reaches
into the find, the promotion and the resume machinery. Declined on the
price. The lever on the over-sweep itself is the window (item 4): A037100's
7.2% is 5.1% at 160 periods, on top of the rate.

### Round 2 result

`python launch.py --selftest`: **47/47 ALL GREEN in 199 s** (359 s on the
first run after the kernel source changed -- every configuration compiles
cold once; that run broke rule 0's cap and is the reason the second was
taken under a hard timeout). `python score.py`: every gate green, all nine
fingerprints reproduced, **SCORE 63,231,371,469**. The frozen shapes are all
narrow, so they see the ping-pong queues and nothing of item 2; what the
round is worth is at the live filters:

| campaign (live filter) | record | before | now | ratio |
|---|---|---|---|---|
| A093483 n = 22 | wide | 4.73e17 x/s | 5.1e17 | 1.08-1.10 |
| A103828 n = 22 | wide | 5.48e17 | 6.05e17 | 1.10 |
| A037100 n = 22 | wide | 2.95e17 | 3.2e17 | 1.06-1.08 |
| A119752 n = 21 | narrow | 1.66e17 | 1.70e17 | 1.02 |
| A119751 n = 20 | narrow | 3.00e17 | 3.03e17 | 1.01 |

Kernel-only numbers, all of them (INNOVATION.md 1.3): the campaign loop was
1.000 of the device in round 1 and nothing here touched the host path, but
the campaign-loop A/B is the owner's to see in the first `[STATUS]` lines of
a resumed hunt -- no agent starts one. Every cursor is untouched: the wheel,
the window, the depth and the segment are what they were, so every
checkpoint resumes as it is.

---

## Open, priced, unbuilt

Round 1 closed the four items this section opened with: A037100's 32-period
opening (planner p2 takes the wheel to 41 at 224 periods there, 1.24x on the
clock), the inherited constants (re-swept on this project's filters, at the
stand-in indices where its hours are), the missing benchmark shapes (the
campaign shapes are re-frozen at the plan and a drill now holds them to it)
-- and it ran the pricing half of the instruction-level pass. What is left,
in the order it is worth doing:

1. **The window width, chosen by measurement at each promotion** (round 2,
   item 4): 1.05x at n = 20 of A119751 and 1.07x at n = 22 of A037100 today,
   and the search should reach 256 periods. A cursor adoption, so the
   owner's call. (The in-block rounds in the window's representation, which
   stood here, are BUILT -- round 2, item 2: 1.08-1.10x on the wide record,
   a loss on the narrow one, dispatched.)
1a. **A frozen shape per family on the WIDE record at the live filter**, once
   the finds are in `FOUND` (round 2, item 2, "Owed").
2. **The SASS-level pass on the window loop** (INNOVATION.md Part 2): the
   window is 56% of the wall and its verdict -- bound by load count at 94%
   information efficiency -- is inherited from lcm-ladders round 9 plus this
   round's ablation prices, not re-derived from the real instruction stream.
3. **A shape per new filter, and the paired check of the plan at it.** Every
   find opens a filter nobody has measured. `_families_stay_apart` will hold
   a new shape to the plan; the check of the PLAN is the ten-minute harness
   of Measurement 5 (the plan against its two neighbouring windows and the
   wheel one prime shorter and longer, paired, on a far window), and the
   remedy for a mis-rank is a term in `crel`.
4. **`CAND_PER_LAUNCH_WIDE`** 2^38 against 2^37 read 1.005 at the one wide
   filter measured; re-price at a second before giving back the 500 MB.
5. **The harness**, for whoever rewrites it (scratchpad, not kept): register
   `clique_model.stand_in(fam, i)` for i up to the index wanted; build
   `GpuEngine` with an explicit wheel from `wheel_candidates(...)[k][0]` and
   `seg_cap = pb`; sweep from a period fifty medians up; time launches
   between two stream synchronisations after one warm launch; interleave the
   configurations every round and take medians; compare survivor SETS over
   identical launches whenever two configurations share a wheel and a launch
   decomposition.
