# OPTIMIZATION_LOG — linear-ladders

Every attempt: the change, the measurement, kept or rejected. Failures
included — they are the record that stops the next person retrying them.
Read [OPTIMIZATION.md](../OPTIMIZATION.md) first; its rules are binding
here, and this engine is a *transfer* — prime-ladders' v3.1 engine with
`killed_residues` re-keyed from the primes to the family's multipliers —
which changes what the first pass has to establish: not whether the kernel
is fast, but whether the configuration is right for a problem whose wheel
is 83× thinner than the one the kernel was last tuned on, at every opening
the launcher has (CLAUDE.md 5g).

All numbers below are from harnesses importing the engine and sweeping
launches of period 1 (or whole periods, where a period holds fewer than 64
launches) with the fingerprint checked on **every** run; configurations
were measured interleaved, and the ratio is the claim (OPTIMIZATION.md
rule 3). Absolute rates drifted about 5% between rounds on this desktop;
ratios inside a round held to 1–2%. No campaign has run (CLAUDE.md 0a):
every measurement here is an engine call on a chosen window.

## v1 — prime-ladders' engine, re-keyed to the multipliers (2026-09-03)

**What it is.** prime-ladders' v3.1 GPU engine with
`killed_residues(q, n, s) = { -s·prime(i)⁻¹ }` replaced by
`killed_residues(q, n, F, unit) = { -s·m⁻¹ mod q : m in mults(F, n), q ∤ m }`
over the family's multipliers, a family key in place of a sign, and the
unit chosen per family from the forced primes at its opening filter. The
kernel, the three-level CRT wheel in unit space, the compaction design,
the tail rounds with lanes per item, the pipelined loop and the `(k, off)`
representation are unchanged and are documented in prime-ladders' log;
nothing below re-measures what that log already measured, except where
this problem's density changes the answer — and it changes several.

**Design-time rules applied before a line was written:**

- **2.7, carry `(k, off)`.** Inherited. The enforced ceiling is the
  primality-proof bound: `3.317×10²⁴` on k for the +1 families (BLS75
  Theorem 1 on `N − 1 = m·k` past the crossing), the crossing
  `k_proof(n, F) = (3.317×10²⁴ − s − 1) / m_max` for the −1 families
  (`2.2×10²³` at n = 15), and no machine word appears in either (G10,
  tight to one k).
- **Choose the wheel that fits at every parameter the battery runs.** The
  same (31],(41],(53] wheel serves all seven families at every filter
  they can reach, because `w(q,n,F)` only grows with n and the tables only
  shrink. The k-space wheels the gates run stop at 47, as prime-ladders'
  did.
- **Measure the campaign, not just the engine (5c), at every opening
  (5g).** Seven families, four filters each: the openings are enumerated
  in `launch.py`'s docstring and every one was priced below.

### Measurement 1 — the phase split (rule 1, taken before anything else)

CUDA events around the two kernels on an un-pipelined launch, against the
production pipelined sweep's wall clock, 48 launches of period 1:

| opening | survivors / launch | sieve kernel | tail rounds | sieve + tails vs pipelined wall | pipelined wall / launch |
|---|---|---|---|---|---|
| A088250 n = 15 | 259 | 4.35 ms (87%) | 0.65 ms (13%) | 5.00 ms = **95%** of 5.25 ms | `2.37×10¹⁹ k/s` |
| A088250 n = 17 | 31 | 3.17 ms (86%) | 0.52 ms (14%) | 3.70 ms = **101%** of 3.67 ms | `3.5×10²⁰ k/s` |
| A125838 n = 15 | 719 | 4.60 ms (85%) | 0.83 ms (15%) | 5.43 ms = **98%** of 5.51 ms | `7.9×10¹⁸ k/s` |

The loop is device-bound at every opening: the host gap is 0–5% of wall,
and the tail — 25% of the device in prime-ladders v1, 11% after its
rounds — is 13–15% here. The tail rounds use 14–18 rounds with lanes per
item rising to 32 from the fifth round on. The sieve kernel is the phase
to attack, as in every ladder project before this one; nothing in it is
re-tuned here beyond the constants (item 4), because its per-candidate
cost was measured in prime-ladders and the transfer kept the candidate
rate (`1.8–2.5×10¹¹ /s` here against `1.75–2.5×10¹¹` there).

**The segment loop's host side** (the launcher's `_submit` and `_drain`
timed on 200 fake launches of 260 survivors through a real 2-worker pool,
the device stood in by a 5.5 ms sleep): `_submit` 0.082 ms, non-blocking
`_drain` 0.036 ms, final blocking drain 0 ms — the pool kept up with no
backlog. That is 0.12 ms of a 5.25 ms launch, 2.3%; the rate-limited
checkpoint save (7 ms every ≥ 2 s) and the heartbeat's one integral (every
30 s) are under 0.5% more. So the loop should run at ≥ 95% of the device
rate. **PENDING the first run (OPTIMIZATION.md 2.14):** the first `[STATUS]`
lines of the A088250 campaign should read close to `2.1×10¹⁹ k/s` at
n = 15 and `2.9×10²⁰` at n = 17; anything under 90% of those is a
per-launch cost that does not scale with the work, and the place to look
first is whatever sits between the launches.

### Measurement 2 — every opening priced (5g step 2), the production wheel

64 launches of period 1 (whole periods where a period holds fewer), 3
rounds, the constants of item 4:

| family | filter | forms c | unit | R1 × R2 × R3 | density (cand / k) | line rate | survivors / unit line | survivors / s | host need at 14.5 µs |
|---|---|---|---|---|---|---|---|---|---|
| A088250 | 15 | 15 | 30030 | 14,336 × 572 × 34,048 | `8.6×10⁻⁹` | **`2.2×10¹⁹`** | `2.1×10⁻¹⁵` | 46,000 | 0.66 core-s/s |
| A088250 | 16 | 16 | 30030 | 4,095 × 525 × 30,969 | `2.0×10⁻⁹` | **`8.3×10¹⁹`** | `1.7×10⁻¹⁶` | 13,600 | 0.20 |
| A088250 | 17 | 17 | 30030 | 2,016 × 480 × 28,080 | `8.3×10⁻¹⁰` | **`2.9×10²⁰`** | `2.5×10⁻¹⁷` | 6,900 | 0.10 |
| A088250 | 18 | 18 | 30030 | 715 × 437 × 25,375 | `2.4×10⁻¹⁰` | **`9.6×10²⁰`** | `2.3×10⁻¹⁸` | 2,200 | 0.03 |
| A173750 | 16 | 15 | 30030 | 14,336 × 572 × 34,048 | `8.6×10⁻⁹` | `2.4×10¹⁹` | `2.1×10⁻¹⁵` | 45,000 | 0.65 |
| A125838 | 15 | 14 | 30030 | 34,425 × 621 × 37,323 | `2.4×10⁻⁸` | `7.6×10¹⁸` | `1.7×10⁻¹⁴` | 117,000 | 1.7 |
| A125839 | 16 | 14 | 30030 | 34,425 × 621 × 37,323 | `2.4×10⁻⁸` | `7.8×10¹⁸` | `1.7×10⁻¹⁴` | 118,000 | 1.7 |
| A164325 | 16 | 16 | 30030 | 14,336 × 525 × 30,969 | `7.2×10⁻⁹` | `2.7×10¹⁹` | `6.0×10⁻¹⁶` | 14,500 | 0.21 |
| A164326 | 15 | 15 | 30030 | 32,400 × 572 × 34,048 | `1.9×10⁻⁸` | `1.0×10¹⁹` | `4.6×10⁻¹⁵` | 45,000 | 0.65 |
| A088651 | 16 | 16 | 510510 | 4,095 × 525 × 30,969 | `2.0×10⁻⁹` | `8.8×10¹⁹` | `1.7×10⁻¹⁶` | 13,700 | 0.20 |

Three things the table says. **The wheel is the rate**: every family and
filter runs the kernel at `1.8–2.5×10¹¹` candidates per second, and the
line rates span 130× because the density does. **The density is a
function of the form count** c and nothing else: A088250 at n = 15,
A173750 at n = 16 and A164326 at n = 15 (c = 15 each) share R1, R2, R3 to
the digit where their forcing thresholds agree, and every constant below
is therefore keyed by c. **The host need runs from 1.7 core-seconds per
second at the −1 openings to 0.03 at n = 18**, so no pool constant serves
all of them (5g): `size_pool` measures at the campaign's own filter (in
the selftest it measured `2.18×10¹⁹ k/s`, 44,059 survivors/s × 14.5 µs =
0.64 core-s/s and ramped 2 workers, matching the row above) and again at
every promotion.

### Measurement 3 — the wheel to 59, priced and DECLINED

Every candidate at these filters is a multiple of 30030, so the u32 and
2⁶³ bounds admit 59 in unit space: (..37], (37, 47], (47, 59], W1 =
`2.5×10⁸`, W2 = `2.6×10⁸`, a period of `1.92×10²¹` (59× the production
wheel's). It kills 15 of 59 residues at c = 15 — 1.34× fewer candidates
per unit of line — and prime-ladders' rule is that a wheel prime is the
cheapest lever there is. Measured paired and interleaved, two rounds:

| opening | (31],(41],(53], unit 30030 | (37],(47],(59], unit 30030 | ratio |
|---|---|---|---|
| A088250 n = 15 | `2.21×10¹⁹`, `2.18×10¹⁹` | `2.70×10¹⁹`, `2.69×10¹⁹` | **1.23×** |
| A088250 n = 16 | `7.92×10¹⁹`, `7.95×10¹⁹` | `1.32×10²⁰`, `1.32×10²⁰` | **1.66×** |
| A088250 n = 17 | `2.77×10²⁰`, `2.81×10²⁰` | `2.78×10²⁰`, `2.81×10²⁰` | **1.00×** |
| A125838 n = 15 | `7.08×10¹⁸`, `7.11×10¹⁸` | `5.86×10¹⁸`, `5.90×10¹⁸` | **0.83×** |
| A088651 n = 16 | `7.97×10¹⁹`, `8.01×10¹⁹` | `1.32×10²⁰`, `1.33×10²⁰` | **1.66×** |

(The survivor counts per unit of line were identical on both wheels at
every opening, as they must be: the sieve depth did not move.)

**Declined.** The 59-wheel wins where a campaign spends minutes and ties
or loses where it spends hours. A088250's a(15) and a(16) are expected
inside the first minute and the first five minutes (BENCHMARKS.md); the
campaign then sits at n = 17 for hours, where the two wheels tie to 1% —
the 59-wheel's candidate rate falls to `1.65×10¹¹ /s` there (its
first-level table has 40,320 residues to the 53-wheel's 2,016, and every
launch is one third-level residue of `7.5×10⁸` candidates). At A125838's
opening it **loses** 17%: with R1 × R2 = `2.0×10¹⁰` a launch is one
third-level residue of twenty billion candidates, the tail queue hits its
`Q3_MAX` cap and 75% of the tail items take the in-block overflow fallback.
Removing that cap needs an offset-chunk axis in the kernel (OPTIMIZATION.md
2.11), which is an engine change and not a constant. Against those the
53-wheel's period is 59× shorter: a find costs at most `3.3×10¹⁹` of
over-sweep (1.5 s at the opening, 0.1 s at n = 17) instead of `1.9×10²¹`
(70 s), and period 0 — where every family's first term is expected —
closes and is narrated in seconds instead of a minute. **Where it would
pay:** A088651, whose whole campaign is one filter (a(16) 96% under the
ceiling, 39 min at `8.8×10¹⁹`), would finish in 25; A164325 and A173750
would gain 1.2–1.7× for the few minutes of their first term. A per-family
wheel is 14 minutes once, against a second set of fingerprints, gates and
a second period denomination. Not taken.

### Measurement 4 — the constants, re-swept on this density (rule 3a)

Interleaved, 64 launches (or whole periods) per run, the fingerprint
identical across every variant of every filter. Ratios are to the shipped
value at the same filter.

**`LIT_SURV` (the prefix compaction point), by form count.** Two rounds at
every opening and at A088250's next three filters, then one confirming
round on the other w-classes:

| family | n | c | 0.12 | 0.19 | 0.28 | 0.40 | kept |
|---|---|---|---|---|---|---|---|
| A125838 | 15 | 14 | **1.000** (`7.5×10¹⁸`) | 0.79 | 0.77 | 0.75 | 0.12 |
| A125839 | 16 | 14 | **1.000** (`7.8×10¹⁸`) | — | 0.76 | — | 0.12 |
| A088250 | 15 | 15 | **1.000** (`2.2×10¹⁹`) | 0.84 | 0.89 | 0.80 | 0.12 |
| A173750 | 16 | 15 | **1.000** (`2.4×10¹⁹`) | — | 0.82 | — | 0.12 |
| A164326 | 15 | 15 | **1.000** (`1.0×10¹⁹`) | 0.83 | 0.86 | 0.78 | 0.12 |
| A125839 | 17 | 15 | **1.000** (`1.6×10¹⁹`) | — | 0.89 | — | 0.12 |
| A088250 | 16 | 16 | 0.88 | 0.90 | **1.000** (`9.1×10¹⁹`) | 0.90 | 0.28 |
| A088651 | 16 | 16 | 0.90 | 0.90 | **1.000** (`9.3×10¹⁹`) | 0.90 | 0.28 |
| A173750 | 17 | 16 | 0.86 | — | **1.000** (`4.9×10¹⁹`) | — | 0.28 |
| A164325 | 16 | 16 | 1.01 | — | **1.000** (`2.6×10¹⁹`) | — | 0.28 (a tie) |
| A088250 | 17 | 17 | 0.95 | 0.95 | **1.000** (`3.0×10²⁰`) | **0.16** | 0.28 |
| A088250 | 18 | 18 | 0.93 | **1.000** (`1.06×10²¹`) | 0.98 | **0.22** | 0.19 |

The optimum moves with the form count and not with the family: 0.12 at
c ≤ 15 by 1.12–1.31× over 0.28, 0.28 at c = 16 and 17 by 1.05–1.17× over
0.12, a tie between 0.19 and 0.28 at c = 18, and **0.40 is a 5–6× cliff
from c = 17 on** — the shared-memory cliff prime-ladders mapped one
filter past where it had swept, here found before the first campaign
because every filter the campaigns promote through was swept (5g). The
table is `LIT_SURV_UNIT_BY_C` in `lladder_gpu.py`, keyed by c, so a
family whose rungs start at 2 or 3 reads the row its survival curve
actually has (A125839 at n = 17 is the c = 15 row); a form count past its
end takes the last entry.

**The rest, at A088250 n = 15 (LIT 0.12) and n = 17 (LIT 0.28), one
interleaved round with the baseline repeated:**

| constant | shipped | variant | n = 15 | n = 17 | verdict |
|---|---|---|---|---|---|
| `K2_SURV` | 0.008 | 0.004 | 0.99 | 1.02 | flat; keep |
| `K2_SURV` | 0.008 | 0.015 | 0.99 | 1.00 | flat; keep |
| `CPT` | 64 | 32 | **0.755** | **0.84** | keep 64 |
| `SPB` | 16 | 8 | 0.995 | 0.95 | keep 16 |
| `SPB` | 16 | 32 | 0.99 | 0.98 | keep 16 |

(Baselines: `2.306×10¹⁹` and `2.305×10¹⁹` at n = 15, `3.23×10²⁰` and
`3.36×10²⁰` at n = 17 — the 4% between the two n = 17 baselines is the
ambient band, and the K2/SPB variants sit inside it.) prime-ladders'
unit-wheel values survive this density unchanged except `LIT_SURV`, which
is the constant that project also found filter-sensitive.

### Termination table (OPTIMIZATION.md Part 3), v1

| phase | share (A088250 n = 15 / n = 17) | verdict |
|---|---|---|
| sieve kernel | 87% / 86% | the phase prime-ladders v2/v3 attacked (prefix hoist, in-block rounds, per-filter LIT); its constants re-swept here at every opening: LIT moved (by form count), CPT/SPB/K2 held. Not re-profiled inside: the candidate rate matches prime-ladders' to 10% at the same kernel, so its roofline arguments transfer |
| tail rounds | 13% / 14% | prime-ladders' lanes-per-item rounds; 14–18 rounds here, LPI to 32 from the fifth. Bounded by its share |
| host gap | 5% / 0% | the pipelined loop; `_submit` + `_drain` 0.12 ms per launch measured |

**Not done, priced:** the 59-wheel (item 3, 1.0–1.66× by filter, declined
on where the hours are spent); an offset-chunk axis in the kernel
(OPTIMIZATION.md 2.11), which would lift the `Q3_MAX` cap that costs the
59-wheel at the −1 openings and might make it a win everywhere — an engine
change; a per-family wheel choice (A088651's campaign in 25 min instead of
39). **Do not rebuild:** everything in square-ladders' and prime-ladders'
rejected lists applies to this kernel unchanged, since it is this kernel.

### Ceilings found

- **A launch may not hold more than one period's third level at a
  filter where R3 < nu.** At n = 18 a period is 8 launches, so a
  "64-launch" benchmark shape there sweeps 8 and stops; the harness that
  first measured n = 17 and n = 18 over-counted their line by 2.5× and 8×
  (a rate of `7.6×10²¹` that was really `9.6×10²⁰`). `score.py` refuses a
  launch count over a period's, and the deep shapes are denominated in
  periods.
- **The −1 families' ceilings are the crossing**, `2.2×10²³` at n = 15
  down to `1.0×10²³` for A164326 at n = 17 (m_max = 33). An N+1
  certificate (BLS75 on the factorization of `m·k = N + 1`) would lift
  every one of them to `3.317×10²⁴`; huntlib does not have it, and adding
  it is a new engine version with a certificate drill at that height.

### What the gates caught during the build

- **Two vacuous parity windows and one ceiling overshoot in G9.** At
  n = 15 a sieve to 128 leaves 0.2 survivors in `4×10⁸` of line — the
  wheel is that strong — and a dense CPU sieve wide enough to populate it
  costs a minute per window; the n ≥ 15 windows run a sieve to 32 instead,
  where 30 survivors fit in `4×10⁸`. A window whose span I had doubled
  without moving its base overshot the +1 ceiling by one wheel period
  (`3.2×10¹⁰`) and the engine refused it, as designed.
- **A canary below the floor.** A164326's a(7) = 2100 is under the
  engine floor (4097 at sieve 4096); G5 refused the vacuous rediscovery
  and the term was replaced.
- **A unit-admissibility test case that was wrong about the lemma**, not
  the code: 30030 at A088250's n = 14 was listed as "not forced", but 13
  is forced from n = 12 in the 1..n family (G2c), so the engine rightly
  accepted it. The refusal cases now sit one filter below each threshold.
- **G12's first version asserted the series was larger than the prime
  ladders'.** It is smaller (`2.3×10⁴` against `6.6×10⁵` at n = 14):
  consecutive multipliers kill more residues per prime than the first n
  primes do. The gate now asserts the correct direction, and the model's
  validation (46 draws, mean E 0.86) is what says the series is right.
- **A pool harness without a spawn guard** re-executed itself in every
  worker on Windows (`BrokenProcessPool`). Scaffolding gets the same
  discipline as the arithmetic (OPTIMIZATION.md rule 6).

---

## v2 — the wheel to 59, the L1 carveout pinned, the register allocation guarded. KEPT: 1.20× at n = 17, 1.27× at n = 15, 1.50× at n = 16 (2026-09-03)

`SCORE 30,826,035,115,578` / `SCORE17 404,629,246,197,708` /
`SCOREM 8,416,469,598,948`, the three shapes re-frozen on the new wheel
(the wheel is a deliberate coverage change; the three k-space shapes keep
v1's fingerprints and reproduce them). 42/42 green in 88 s (G18 is new;
G17 gained a three-wheel leg). Every number below is a **paired,
interleaved ratio** from a harness that builds two engines from the same
module — different constants, source patches or wheels — and sweeps the
frozen windows back to back with the fingerprint checked on every run;
absolute rates drifted 10% across the afternoon and are quoted only as
context. Nothing here is a campaign (CLAUDE.md 0a).

The pass followed OPTIMIZATION.md Part 1 in order, and its shape is worth
stating first because it is the finding: **every large number in it was
a configuration mistaken for a constant.** v1's tuning table was measured
correctly and read wrongly three times — a "shared-memory cliff" that was
the driver's L1 carveout, a "LIT optimum" that was the compiler's register
allocation, and a "wheel that ties at n = 17" that was a group budget one
bit too small and a queue cap four times too small. None of the three is
visible to a fingerprint, a gate or a rate; each needed a measurement of
the thing itself.

### Measurement 1 — the phase split, re-taken (rule 1)

CUDA events around the sieve kernel and the tail rounds of every launch
against the pipelined wall clock, three rounds each:

| shape | wall / launch | sieve | tail rounds | host gap |
|---|---|---|---|---|
| `SCORE` (n = 15) | 5.2–5.6 ms | **86.5%** | 13.3% | 0.3% |
| `SCORE17` | 3.8–4.0 ms | **84.4%** | 15.2% | 0.5% |
| `SCOREM` (c = 14) | 5.6–6.1 ms | **84.3%** | 15.5% | 0.3% |

The same split v1 recorded; the loop is device-bound and the sieve kernel
is the phase. What v1 did not do was look inside it ("not re-profiled
inside: the candidate rate matches prime-ladders'"), which Part 3.1 says
is an inherited verdict. So:

### Measurement 2 — what the sieve is bound by, priced by ADDING work (3.3)

Each variant appends one statement to every hoisted prefix group's line
whose result is ANDed with a kernel parameter that is 0 at runtime: the
compiler cannot know that, so the work is done and the survivor stream —
and the fingerprint — is untouched. The marginal cost of one such
statement per group per candidate, on a launch of `1.07×10⁹` candidates
at `SCORE` (5 groups), as the time it adds to the launch:

| added per group per candidate | ratio | cost / launch | per instruction-equivalent |
|---|---|---|---|
| a 5-instruction dependent ALU chain | 0.894 | 0.12 ms | **0.025 ms per instruction** = 128 SMs × 4 issue/clk × 2.5 GHz: the SM's peak issue rate, at the margin |
| a gather from one 32-byte sector (data-dependent index) | 0.812 | 0.24 ms | ≈ 10 instr-eq (8 of them its own address arithmetic) |
| a gather spread over 1 KB | 0.786 | 0.28 ms | 11 |
| over 8 KB | 0.698 | 0.45 ms | 18 |
| over the 30 KB triple table | 0.657 | **0.54 ms** | 22 |
| a conflict-free shared-memory gather (16 words) | 0.877 | 0.15 ms | 6 |
| a shared gather over 256 words | 0.814 | 0.24 ms | 10 |

(At `SCORE17`, two groups: 0.998 / 0.933 / 0.930 / 0.845 / 0.839 / 0.930
for ALU / sector / 1 KB / 8 KB / 30 KB / shared, the same picture.) Read
together: **the kernel is issue-bound, with one expensive load.** A prefix
group is ~12 instructions plus its gather; a gather into a small table
costs its instructions and little else, and only the 30 KB triple's
gather carries an L1 penalty worth ~12 instructions — one group in five.
The PTX confirms the count (6 for the candidate step, 12 per group, then
the compiler turns the five `kill |= bit` accumulations into
`and / setp / or.pred` triples) and shows where the rest of the kernel's
17,000 PTX instructions are: the cold overflow fallback `tail_survives`
inlined at all 128 candidate sites. The prefix is about three quarters of
the sieve at c = 15.

### Measurement 3 — the "shared-memory cliff" is the driver's L1 carveout

A sink variant that adds an 8 KB shared array per block (and a gather
into it) measured **0.257× / 0.203×** at `SCORE` / `SCORE17`; at
`SCORE17` even 1 KB more was 0.186×. The gather is not the cost (a
256-word shared gather is 0.24 ms above). The mechanism: the SM's 128 KB
of unified cache is split by the driver to MAXIMISE OCCUPANCY, so a
kernel whose resident blocks want a few KB more shared memory gets a
100 KB shared carveout and 28 KB of L1 — and the 40–50 KB of group tables
that were L1-resident are not any more. Setting the carveout explicitly
(`cuFuncSetAttribute(PREFERRED_SHARED_MEMORY_CARVEOUT)`), each variant
its own module (CuPy memoizes `RawModule` by source text, so two engines
built from identical source share one function and its attributes — the
first sweep measured one kernel six times):

| carveout (% shared) | blocks/SM | `SCORE` | `SCORE17` | `SCOREM` |
|---|---|---|---|---|
| driver's choice | 9 | 1.000 | 1.000 | 1.000 |
| 50 (64 KB shared, 64 KB L1) | 9 | 1.007 | 1.001 | 1.005 |
| 25 (32 KB / 96 KB) | 6 / 5 / 6 | 0.986 | 0.885 | 0.990 |
| 0 (max L1) | 1 | 0.374 | 0.283 | 0.385 |
| 75 | 9 | 0.257 | 0.176 | 0.259 |
| 100 | 9 | 0.295 | 0.155 | 0.269 |
| the +8 KB variant at 50 | 5 / 4 / 5 | 0.797 | 0.716 | 0.812 |

So the tables need between 32 and 64 KB of L1; the driver's default was
already 50 for every v1 configuration (and is now **pinned**, so a change
in shared footprint cannot move it); and occupancy is soft on the low
side (6 blocks instead of 9 costs 1% at n = 15, 12% at n = 17). This is
the cliff prime-ladders v3 mapped at CPT ≥ 96, SPB 32 and LIT 0.40 and
called shared memory: the queues grew, the driver moved the split, and
the tables fell out of L1. With the carveout pinned those constants were
re-swept below.

### Measurement 4 — things that did not pay, measured

| attempt | `SCORE` | `SCORE17` | `SCOREM` | why it was tempting / why not |
|---|---|---|---|---|
| the pair-group tables (≤ 2 KB each) copied into shared memory per block, gathered there | 1.010 | 0.999 | 1.013 | a shared gather is cheaper than a 32-sector L1 gather — but a 1 KB-footprint L1 gather already costs 0.28 ms against shared's 0.24 (Measurement 2). A wash; not shipped |
| `#pragma unroll 1` on jj / `unroll 4` on ss / `unroll 1` on ss / both | 0.996 / 0.987 / 0.970 / 0.992 | 0.999 / 0.997 / 0.978 / 1.001 | — | code size (the 64-candidate body is ~5,000 instructions): not instruction-cache-bound, and the unrolling buys almost nothing. Kept in reserve: the (4, 1) body is the occupancy guard's fallback below |
| accumulate the raw shifted word, test bit 0 once (`kacc`) | 1.002 | 1.002 | 1.004 | the `and / setp / or.pred` triples in the PTX; nvcc had already fused them in SASS. Noise |
| form the 64-bit offset only in the cold branch (`lazyoff`) | 1.004 | 1.006 | 1.003 | two instructions per candidate; noise |
| **fold the table's word offset into the load's immediate (`nooff`)** | **1.025** | **1.016** | **1.019** | one `add` per group per candidate. KEPT |
| `__noinline__` on the fallback | 0.787 | 0.774 | 0.796 | 156 registers, 3 blocks/SM: a real call inside the unrolled body |
| a plain-loop cold fallback (no unrolled chains) at every site | 0.649 | 0.721 | 0.695 | 140 registers |
| an overflow MASK per thread, flushed after the ss loop (8 cold sites instead of 128) | 0.839 | 0.850 | 0.843 | 138 / 105 registers — see Measurement 6 |
| the same with `__ldcs` on the residue loads | 0.975 | 1.029 | 0.989 | 43 / 48 registers, 10 blocks/SM: the same source with one load hint compiles 3× smaller, and 40 warps buy nothing over 36 |
| `__launch_bounds__(128, 9 / 10 / 12)` | 1.009 / 0.971 / 0.625 | 0.728 / 0.781 / 0.142 | 0.990 / 0.969 / 0.575 | the bound changes the scheduler's choices, not just the cap: n = 17 went from 50 registers and no spills to 56 with 40 bytes of local. Not a control |

### Measurement 5 — the wheel to 59, re-priced (2.8, 2.11)

v1 measured (..37],(37,47],(47,59] at 1.00× at n = 17 and 0.83× at
A125838's opening and declined it. Paired against v1's wheel with the
launch-denominated windows, as v1 measured it and then with the two
configuration faults removed:

| opening | as v1 measured (group budget 2¹⁸, Q3 2²⁶) | with 2¹⁹ | + Q3 2²⁸ |
|---|---|---|---|
| A088250 n = 17 | 1.080 | **1.127** | — |
| A088250 n = 16 | 1.138 | **1.237** | — |
| A088250 n = 15 | 1.179 | 1.174 | — |
| A125838 n = 15 (c = 14) | 0.673 | 0.659 | **1.000** |

Two faults. **The group budget.** On this wheel the first sieve prime is
61, and 61·67·71 = 290,177 exceeds `LIT_GROUP_MAX = 2¹⁸`, so the prefix
ran (61,67),(71,73),(79) — three lookups per candidate where v1's wheel
ran (59,61,67),(71,73) — two. The 1.31× of density paid 1.5× of prefix.
At 2¹⁹ the triple forms (a 35 KB table) and the wheel is 1.13× at n = 17.
**The tail-queue cap.** At c = 14 a launch is one third-level residue of
`2.05×10¹⁰` candidates (`R1 × R2 = 791,775 × 25,839`), its round-2
survivors are `1.6×10⁸`, and `Q3_MAX = 2²⁶` sent 60% of them through the
in-block fallback — a 6,500-prime tail serialised inside the sieve block.
The phase split there read sieve 94% at `1.28×10¹¹` candidates/s against
`2.3×10¹¹` elsewhere and tails 3.5%. At 2²⁸ the analytic size wins
(`2 × 1.3 GB` of queue at that opening, a tenth of it from c = 15) and
the opening ties.

### Measurement 6 — the "LIT optimum" is the register allocation

With the group budget at 2¹⁹, `LIT_SURV` 0.19 on the 59-wheel dropped to
**0.19× / 0.27×** at n = 17 / 16 with the carveout pinned. The
configuration it compiled to: groups (61,67,71),(73,79,83),(89) — a SECOND
triple, 73·79·83 = 478,661, a 58 KB table, 94 KB of prefix tables. So the
modulus budget alone is the wrong knob: `lit_groups` now also carries a
running BYTE cap (`PREFIX_BYTES_MAX = 40 KB`) and closes a group early
rather than let a table grow past it; with it, 0.19 at n = 17 is
(61,67,71),(73,79),(83,89), 37 KB.

And with THAT fixed the register count moved instead. The same hot path
compiled to 50, 54, 56, 64, 94 and 117 registers across near-identical
configurations (the 128 inlined copies of the cold fallback steer the
allocator; `nres` 16 versus 32 flips it), and at 94 registers a block
count of 5 instead of 9 is 0.8×. **v1 had shipped every c = 16 opening —
A088250 n = 16, A164325 n = 16, A088651 n = 16 — at 93 registers and 5
blocks per SM**, every fingerprint green. Every source-level attempt to
steer it made it worse (Measurement 4). What works is measurement: the
engine now reads the registers and blocks per SM its kernel compiled to
and, under `OCC_MIN_BLOCKS = 8`, compiles the (ss 4, jj 1) body and keeps
whichever reaches more blocks — that body costs 0–2% where the full body
compiles well (Measurement 4) and was 1.11× at the 94-register n = 16
case. `config()` reports the choice; **G18** builds every family's
opening filter and the next and refuses one under 8 blocks, with spills,
without the carveout, or with the prefix over its cap. Today all 14
compile to 53–64 registers and 8–9 blocks on the full body.

### Measurement 7 — `LIT_SURV` and the rest, re-swept on the 59-wheel (3.4)

Paired against **v1's wheel with `nooff` on both**, each opening its own
group, 4–5 rounds, all with the 2¹⁹ budget, the byte cap, Q3 2²⁸ and the
carveout pinned. Registers / blocks per SM in brackets where they moved:

| opening (forms) | 0.12 | 0.19 | 0.28 | 0.40 | kept |
|---|---|---|---|---|---|
| A125838 n = 15 (c = 14) | **0.936** [64/8] | 0.819 [128/4] | 0.717 [117/4] | — | 0.12 (0.96 on the (4,1) body at 0.19; a 5% loss at this one opening, the only one) |
| A088250 n = 15 (15) | **1.271** | 0.978 [128/4] | 0.957 [117/4] | — | 0.12 |
| A088250 n = 16 (16) | **1.503** | 1.226 [117/4] | 1.223 [94/5] | 1.109 | 0.12 (1.52 on the (4,1) body at 0.19 — the guard's fallback, not taken while the full body reaches 9) |
| A088651 n = 16 (16, unit 510510) | **1.503** | 1.223 | 1.222 | — | 0.12 |
| A164325 n = 16 (16, odd) | **1.418** | — | — | — | 0.12 |
| A164326 n = 15 (15, odd) | **1.243** | — | — | — | 0.12 |
| A088250 n = 17 (17) | 1.170 | **1.203** | 1.145 | 1.023 | 0.19 |
| A088250 n = 18 (18) | 1.303 | 1.319 | **1.321** | 1.104 | 0.19 (a tie) |
| A088250 n = 19 (19; vs 0.12 on the 59-wheel) | 1.000 | **1.063** | 1.001 | — | 0.19 |

The three c = 16 references (v1's wheel at A088250, A088651 and A164325
n = 16) are the 93-register, 5-block kernels of Measurement 6, so part of
that 1.5× is v1's own occupancy loss; the honest cross-wheel number at
c = 16 is nearer 1.25×. `LIT_SURV_UNIT_BY_C` is now 0.12 to c = 16 and
0.19 from c = 17. The other constants, on the 59-wheel at n = 17 / 15
(ratio to the shipped v2 value): `CPT` 128 0.971 / 1.030 (a wash; 32 is
**0.248 / 0.240**, and `tpb` 64 — the same 4,096-candidate tile — 0.210 /
0.224, so the tile stays 8,192); `SPB` 32 1.010 / 1.034 (a wash inside a
±10% band), 8 0.946 / 0.953; `K2_SURV` 0.004 0.975 / 0.996, 0.015
0.950 / 0.969; `K2_GROUP_MAX` 2¹⁵ 0.815 / 0.830, 2¹⁶ 0.844 / 0.821 (the
round-2 tables leaving L1); `tpb` 256 0.980 / 0.960; `CAND_PER_LAUNCH`
2³¹ **1.027 / 1.032** at n = 17 / 18 (two third-level residues per
launch; below c = 17 one residue exceeds either budget) — KEPT; and the
prefix byte cap itself on the k-space gate shapes (`SCORE10`, `SCORE2L`)
1.003–1.007 against no cap. `PRE_COPY` was raised to 2¹⁵ because a c = 14
launch returns ~15,000 survivors and the synchronous read past 2¹³ was
the 2.2% host gap in that phase split.

### What shipped, and the paired ratio it stands on

Wheel (..37],(37,47],(47,59]; `LIT_GROUP_MAX` 2¹⁹ with `PREFIX_BYTES_MAX`
40 KB; `LIT_SURV_UNIT_BY_C` 0.12 / 0.19; the offset fold; `Q3_MAX` 2²⁸;
`CAND_PER_LAUNCH` 2³¹; `PRE_COPY` 2¹⁵; `CARVEOUT_PCT` 50 pinned;
`OCC_MIN_BLOCKS` 8 with the (4, 1) body as the fallback; G18; G17's
three-wheel leg (the v2 wheel, v1's and the k-space wheel over
`[10⁶, 3.26×10¹⁹)` at n = 17: 799 identical survivors); `CKPT_LAUNCHES`
32 (a launch is 8–40× the work it was). Against v1 at the same filter,
paired: **1.27× (c = 15), 1.50× (16), 1.20× (17), 1.32× (18), 0.94–1.00×
(14)**; the ledger's cross-run numbers are 1.38× / 1.29× / 1.18× on the
three re-frozen shapes.

### Termination table (OPTIMIZATION.md Part 3), v2

| phase | share (n = 15 / 17) | verdict |
|---|---|---|
| sieve: prefix | ~65% / ~37% of wall | issue-bound at the margin (Measurement 2: an added instruction costs exactly the SM's peak issue), ~12 instructions and one gather per group; the gather is free for the pair tables and worth ~12 instructions for the triple. Levers left, priced: per-lane `ffs` compaction after the first group (56% of candidates are dead after it at c = 15; ~8% there, ~0 at n = 17); `LDS.128` for the per-group residue loads (~4%). The wheel is at its u32 / 2⁶³ limit again: (..37] is the last first level under 2³² and (37,59] the last second under 2³², so the next prime needs the k-windowed sweep square-ladders priced |
| sieve: queue-0 push + round 2 + global push | ~20% / ~45% | round 2 is the larger part at n = 17 (27% of candidates enter it, 18 non-hoisted Barrett groups); its constants (`K2_SURV`, `K2_GROUP_MAX`, one split) re-swept and unmoved. Not attacked inside |
| tail rounds | 13% / 15% | prime-ladders' lanes-per-item rounds; 14–18 rounds, LPI to 32. **The second-stream overlap was built and measured: 0.979 / 0.994 / 0.998** on `SCORE` / `SCORE17` / `SCOREM`, paired, intervals straddling 1 — the sieve saturates the SMs, so the rounds interleave rather than hide, and the second set of tail queues is 2.6 GB at c = 14. Reverted; what it left behind is the round-0 capacity fix below. Bounded by the share, and now shown not to hide behind the sieve |
| host gap | < 0.5% | the pipelined loop; nothing to take |

**Priced and not done:** y-chunked launches, so
that c ≤ 14 runs `10⁹`-candidate launches instead of `2×10¹⁰` (it would
remove the 2.6 GB of tail queue at those openings and probably turn the
c = 14 tie into the 1.2× the density predicts — an engine change: a
second-level offset in the kernel and a chunk loop in `_sweep`); the
`ffs` compaction and the vectorised residue loads; an N+1 BLS75 route for
the −1 families' ceilings (unchanged from v1). **Do not rebuild:** shared
pair tables, unroll-depth changes, `kacc`, `lazyoff`, any variant of the
fallback (Measurement 4), and every k-space reject in square-ladders' and
prime-ladders' logs.

### What the gates caught

- **The resume drill's two-level window fell inside period 0.** Its
  `k = 10¹⁵` sat in the first period of the wider two-level wheel
  (`6.2×10¹⁷`), and the engine refused the unclipped window as designed;
  the drill moved to `10¹⁹`, six periods, cut at two.
- **The harness measured one kernel six times.** CuPy memoizes
  `RawModule` by source text; six "variants" that differed only in a
  function attribute shared one CUfunction, and the last attribute set
  applied to all of them (Measurement 3, first attempt: every carveout
  read 0.27×). Tagging each variant's source fixed it. Scaffolding gets
  the same discipline as the arithmetic (OPTIMIZATION.md rule 6), again.
- **The ovf-mask patch anchored on a pragma the unroll variants had
  changed** and asserted rather than silently building the wrong kernel.
- **G16 caught the second-stream overlap reading unwritten queue slots.**
  Tail round 0 took `min(count, round_cap)` items, and the count includes
  pushes that overflowed `q3cap`; production has `q3cap == round_cap[0]`
  so nothing was ever read past what was written, but G16's forced-zero
  cap exposed the gap the moment a second queue set stopped the stale
  slots being the previous launch's. Round 0 now reads at most `q3cap`
  slots, in the serial engine too.

### What the A088250 campaign measured (2026-09-03: the acceptance test, run for real)

Started with no flags at 17:59 and stopped at the family's ceiling at
19:15 with `a(15)`, `a(16)` and `a(17)` found ([RESULTS.md](RESULTS.md)).
Per filter, from the evidence timestamps and the checkpoint, against the
v2 benchmarks:

| filter | line swept | wall clock | campaign rate | benchmark |
|---|---|---|---|---|
| n = 15 (period 0) | `1.92×10²¹` | 65 s, pool sizing and ramp included | `3.0×10¹⁹ k/s` | `SCORE` `3.07×10¹⁹` |
| n = 16 | `8.5×10²²` | 10.1 min | `1.4×10²⁰` | `1.38×10²⁰` (Measurement 7) |
| n = 17 | `9.6×10²³` | 39.2 min | `4.1×10²⁰` | `SCORE17` `3.99×10²⁰` |
| n = 18 | `2.27×10²⁴` | 25.4 min | `1.49×10²¹` | `1.45×10²¹` (Measurement 7) |

Every phase ran at its benchmark's rate, the pool was sized to 2 at the
opening and 1 after, and `a(15)` was narrated at the close of period 0 as
the README's first-lines paragraph said it would be. The loop's wall
clock per unit of line matched the device's at every filter, which is the
measurement OPTIMIZATION.md 2.14 says only a campaign can take.

**The A125838 campaign** (19:28–19:46 the same day, 17.2 min to its
ceiling, `a(15)`–`a(18)` found) and **the A125839 campaign** (19:55–20:10,
15 min, `a(16)`–`a(18)`) read, from their timestamps: period 0 at
`9.2×10¹⁸` / `9.4×10¹⁸` against the `SCOREM` `8.4×10¹⁸`, and then, at
their later filters, `7.2×10¹⁹` / `7.0×10¹⁹` at c = 16 and `7.2×10²⁰` /
`2.7×10²⁰` at c = 18 / 17 — half to two thirds of A088250's rates at the
same form counts, which had run at their benchmarks an hour earlier.

That was first written up here as an open question about the launcher.
It is not one. **Paired, in one process, 4 rounds:** A125839 at n = 18
against A088250 at n = 16 (both c = 16, both 54 registers and 9 blocks
per SM, the same generated source) is **0.503×**, and A125839 at n = 19
against A088250 at n = 17 (c = 17, 56 registers, 9 blocks) is **0.655×**.
The kernels are the same; **the wheels are not.** A family whose rungs
start at 2 or 3 forces each small prime one or two filters later than
the `1..n` family (README.md's thresholds: `2..n` forces `q` from
`n = q + 1`, `3..n` from `q + 2`), so at A125839's n = 18 the prime 17
keeps `17 − 15 = 2` residues in the first wheel level where A088250's
n = 16 keeps one, and at its n = 19 the prime 19 keeps three where
A088250's n = 17 keeps two: twice and 1.5× the candidates per unit of
line at the same candidate rate — exactly the campaign ratios. v1's
"the density is a function of the form count c and nothing else"
(Measurement 2 above) holds only between filters in the same forcing
state, and the sibling table in BENCHMARKS.md now carries the −1
families' own rates at their later filters. The campaigns ran at the
engine's rate at every filter, and there is nothing to fix.

**The A173750 campaign** (20:23–21:00, 37 min, `a(16)`, `a(17)` and
`a(18) = a(19)` found, then swept to the +1 ceiling) confirmed the
reading on a +1 family with the same rung start: n = 16 (period 0)
`3.0×10¹⁹` (`SCORE` `3.07×10¹⁹`); n = 17 `7.3×10¹⁹` (the lagged wheel,
`6.5×10¹⁹` paired); n = 18 `4.1×10²⁰` (`SCORE17` `3.99×10²⁰`, every
prime forced there); n = 20 `3.0×10²¹` (A088250's n = 19 wheel,
`2.8×10²¹`, Measurement 7). Four campaigns, fourteen phases, every one at
the engine's rate for its wheel.

**The A164326 campaign** (22:27–22:41, 14 min, `a(15)`, `a(16)` found,
then swept to its `n = 17` ceiling of `1.005×10²³`) ran `1.3×10¹⁹` /
`4.1×10¹⁹` / `1.95×10²⁰` at n = 15 / 16 / 17. The first two are
Measurement 7's odd-family rates; the third had no benchmark, and paired
in one process **A164326 at n = 17 is 0.491× of A088250 at n = 17, and
A164325 at n = 18 is 0.478× of A088250 at n = 18**, the same generated
source, 56 registers and 9 blocks per SM on both sides. The wheel again:
the odd multipliers `1, 3, …, 33` cover only 16 nonzero residues modulo
19, 23, 29 and 31 (the seventeenth, an even one such as 16 mod 19, is
never reached) where the consecutive `1..17` cover all 17, so the odd
family's first wheel level is `3 · 7 · 13 · 15 · 20 = 81,900` residues to
A088250's `2 · 6 · 12 · 14 · 20 = 40,320` — 2.03× the candidates per unit
of line at the same kernel rate. The campaign's `1.95×10²⁰` is that
engine's `1.82×10²⁰`. So the odd families have their own rates from
n = 17 on, as the `2..n` and `3..n` families do from n = 17 and 18, and
BENCHMARKS.md's sibling table carries them.
