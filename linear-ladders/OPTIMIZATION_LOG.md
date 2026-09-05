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

**The A164325 campaign** (22:49–23:49, 1.00 h, `a(16)`–`a(18)` found,
then swept to the +1 ceiling) ran `3.9×10¹⁹` / `1.93×10²⁰` / `5.3×10²⁰` /
`1.82×10²¹` at n = 16 / 17 / 18 / 19 — the odd-family engine at each
(`3.75×10¹⁹` Measurement 7; `1.82×10²⁰` and `4.87×10²⁰` paired above;
and at n = 19, paired the next morning, **0.631× of A088250's n = 19**,
`1.76×10²¹` against `2.79×10²¹`: the odd multipliers `1..37` cover 18
residues at 23, 29, 31 and 37 where `1..19` cover 19, a first level of
`5 · 11 · 13 · 19` against `4 · 10 · 12 · 18` per those primes, 1.57× the
candidates, exactly the ratio). **A088651 at n = 17** (unit 510510) was
paired at the same time for the last campaign's expectations: **1.014×
of A088250's n = 17** — its multipliers are `1..n`, so its forcing and
its wheel are A088250's, and the unit's extra prime (17 forced from its
opening) changes nothing at the filters it will run. Six campaigns,
twenty phases, every one at the engine's rate for its wheel; the
`[STATUS]` line's rate is the benchmark's for every family at every
filter, which is what rule 5g's acceptance test asks.

**The A088651 campaign** (00:06–00:18 the next morning, 12 min, `a(16)`
found, then swept to the crossing at n = 17) ran `1.38×10²⁰` at n = 16
(Measurement 7: `1.44×10²⁰`) and `3.9×10²⁰` at n = 17 (paired above:
`3.75×10²⁰`). Seven campaigns, twenty-two phases, all at the engine's
rate. With that the v2 engine has done everything its ceilings allow:
every family's next term is above its ceiling, and the next engine
version is the one that raises them (RESULTS.md, "What is open now").

---

## v3 -- the ceiling from the certificate's cost, not the test's validity: one ceiling of 1e40 for every family, the N+1 route and the recursion in huntlib. KEPT (2026-09-04)

`SCORE`, `SCORE17`, `SCOREM`, `SCORE2L`, `SCORE1L` and `SCORE10` all
reproduce their v2 fingerprints (the wheel, the unit, the sieve depth and
the segment are v2's; nothing in the kernel moved), so this version has no
paired engine ratio to report and the SCORE row in BENCHMARKS.md is the
ambient band. 44/44 green in 120 s (three new drills, two gates extended).
Nothing here is a campaign (CLAUDE.md 0a): every number is an engine call
on a chosen window, a certificate timed on a constructed k, or a model
query.

### The design (handoff items 1-3), and why the ceiling is not two numbers

The v2 ceilings were where the PROOFS stopped: the deterministic
Miller-Rabin bound on k for the +1 families (so that every prime factor
of k stayed under the bound and Theorem 1 needed no subproof), and the
proof crossing itself for the -1 families, whose values' structure is on
`N + 1 = m*k` and for which huntlib had no test at all. Both were limits
of the CERTIFICATE, not of the engine -- candidates are `(k, off)` with a
Python-int base, the CPU engine, the model and the checkpoint are Python
ints -- so the design is three things in huntlib and none in the kernel:

1. **The N+1 route** (`huntlib.certificate`, BLS75 Theorem 15). For
   `N + 1 = F*R`, F completely factored, one discriminant D with Jacobi
   `(D/N) = -1` and, per prime `q | F`, a Lucas sequence `U(P_q, Q_q)`
   with `P_q^2 - 4Q_q = D`, `gcd(Q_q, N) = 1`, `N | U_{N+1}` and
   `gcd(U_{(N+1)/q}, N) = 1`: then every prime factor p of N is `+-1
   (mod F)`, so `(F - 1)^2 > N` proves N prime. The sequences may differ
   per q but MUST share D -- `(D/p)` is what fixes the sign, and the
   certificate's `verify` checks every pair against the one D it carries.
   A pair whose `U_{N+1}` is not divisible by N proves N composite (the
   Fermat failure's twin). Implemented with a binary Lucas ladder on
   `(U, V, Q^k)`, ~120 bits of exponent, milliseconds per value; the
   verifier re-derives all of it and refuses a neighbouring N, a tampered
   `(P, Q)`, a truncated factorization and a mislabelled theorem (gated
   in huntlib on fixed samples: `F = 2^2 3^24 5^7 7^9`, `N = F - 1` prime
   past the bound; `N = 2P - 1` with P a prime past the bound, for the
   recursion; and `(F' - 1)(F' + 1)` for the composite side). The
   cube-root N+1 theorem (BLS75 Theorem 17) is NOT implemented, priced
   at nothing: a value `m*k - 1` has `N + 1` fully factored once k is, so
   `F = N + 1` and the square-root condition holds trivially; a subproof
   of a structureless prime has Theorem 5 (cube root) on its `p - 1` side
   already, and the measured subproof rate below says that suffices.
2. **The recursion on both sides.** `prove(N, fac=...)` and `prove(N,
   fac_plus=...)` admit a claimed prime factor above the bound only with
   a subproof of it, found by `prove` one level down on whichever of
   `p - 1`, `p + 1` factors (`_admit`); a factor that gets no subproof
   inside the depth moves to R and the theorem's size test decides. A
   prime cofactor gets the same treatment. `factor_full` is the bounded
   chain then `factorint` -- the one unbounded call, which is exactly
   what the ceiling bounds.
3. **The ceiling from the measurement** (`huntlib.ceiling`). The worst
   case for the factoring chain is a k whose hard part is a balanced
   semiprime; here every k is a multiple of its unit (30030, 510510, or
   9699690 from n = 18), so the hard part is `k / unit`. Measured 2026-09-04,
   `factor_full` (200 ECM curves, then factorint), two seeds per height,
   k = unit x two primes within 1% of `sqrt(k / unit)`:

   | height | unit 1 (huntlib's default case) | unit 9699690 (this project from n = 18) |
   |---|---|---|
   | 1e26 | -- | 0.0 s |
   | 1e28 | 0.3, 0.5 s (14-digit factors) | 0.1 s |
   | 1e30 | 0.4, 0.5 s | 0.1, 0.2 s |
   | 1e32 | 0.7, 0.2 s | 0.2 s |
   | 1e34 | 1.1, 0.2 s (17-digit) | 0.2, 0.1 s |
   | 1e36 | 0.5, 2.2 s (18-digit) | 0.3, 0.2 s |
   | 1e38 | 1.6, 2.7 s | 0.9, 0.2 s |
   | 1e40 | 0.9, 3.4 s (20-digit) | 0.9, 1.4 s (17-digit) |
   | 1e42 | not measured | 1.6, 0.3 s |

   `factorint` was never reached: the 200 curves found every factor.
   The other expensive shape, `k = unit * P` with P a prime above the
   bound (a subproof of P): `factor_partial` leaves P in 0.1 s and the
   subproof is the question. A random prime near each height, eight (six
   from 1e35) samples each, `prove(P)` with both sides available: **8/8
   at 1e25, 1e27, 1e29, 1e31, 1e33 (worst 0.5 s), 6/6 at 1e35, 1e37,
   1e39 (worst 0.4 s)**, routes Theorem 1 with a subproof of the cofactor
   in a third of the cases from 1e33. So the certificate a discovery
   costs at 1e40 is one or two seconds of factoring plus tens of
   milliseconds per value, on either sign; the huntlib gate at K_CEIL
   times four proofs on a worst-case k at 0.9 s and four with a subproof
   of a 35-digit factor at 1.2 s, against a 60 s budget. **K_CEIL =
   1e40**, one number for every family and both signs (`lladder_search
   .k_ceil`, G10); what would raise it is the same table one decade up
   (ECM's curve count is the knob for 22-digit factors) and the subproof
   rate at 1e41-1e43. The proof crossing stays what it was and is logged
   once per filter as a `[MILESTONE]`.

**Where the cost actually goes in the campaign.** A discovery's
`certify_run` is one `factor_full(k)` and then, per value, a witness
search: measured on a worst-case k at 1e40 with this project's units and
signs, `ceiling.certificate_cost` (three values per family, Measurement
1): factoring 1.3-3.8 s, three proofs 0.01 s. `verify()`'s stopper witness is now
BOUNDED too (`stopper_witness`: trial division, rho, 200 ECM curves; the
full `factor_witness` only under 1e30) -- a 40-digit stopper that is a
semiprime of two 20-digit primes would otherwise hold the campaign for
whatever `factorint` needed, and the evidence then records the stopper
as composite by the strong test (a failed Miller-Rabin is a proof of
compositeness) with no witness rather than with an hour's stall.

### Measurement 1 -- the resumed filters, priced (5g), and the c = 20 sweep

Every family resumes at the filter after its frontier (`Campaign.calibrate`
on a scratch copy of the real v2 checkpoint, one second of the campaign's
own next launches; nothing recorded):

| family | resumes at | k (v2 cursor) | device | survivors / s | host need | pool | regs / blocks |
|---|---|---|---|---|---|---|---|
| A088250 | n = 18 | `3.317e24` (period 1725) | `1.39e21 k/s` | 3,350 | 0.047 core-s/s | 1 | 56 / 9 |
| A173750 | n = 20 | `3.317e24` (1725) | `2.86e21` | 1,320 | 0.017 | 1 | 56 / 9 |
| A125838 | n = 19 | `1.730e23` (90) | `7.05e20` | 3,500 | 0.043 | 1 | 56 / 9 |
| A125839 | n = 19 | `1.730e23` (90) | `2.51e20` | 9,000 | 0.108 | 1 | 56 / 9 |
| A164325 | n = 19 | `3.317e24` (1725) | `1.78e21` | 1,270 | 0.016 | 1 | 56 / 9 |
| A164326 | n = 17 | `9.998e22` (52) | `1.85e20` | 9,000 | 0.122 | 1 | 56 / 9 |
| A088651 | n = 17 | `1.942e23` (101) | `3.77e20` | 9,020 | 0.113 | 1 | 56 / 9 |

(one-second windows, the fingerprint of each family's first launches
implicit in the survivor counts; the campaign rates in RESULTS.md, taken
over minutes, agree to 5% -- `1.45e21`, `3.0e21`, `7.2e20`, `2.4e20`,
`1.8e21`, `1.8e20`, `3.75e20` -- and are the numbers to check the first
`[STATUS]` lines against.) The host need is 0.02-0.12 core-seconds per
second everywhere, so every resumed campaign sizes a pool of 1, and the
loop is device-bound by 8x or more. The certificate at k = 9.83e39 with
each family's own unit, sign and multipliers (`ceiling.certificate_cost`,
three prime values each): factoring 1.3 s (3.8 s for A088651's unit
510510, whose hard part is a 19-digit square) and 0.00-0.01 s for the
three proofs -- Theorem 1 for the +1 families, Theorem 15 for the -1,
all re-verified, none unproved.

**`LIT_SURV` at c = 20**, the table's last entry, which v2 had measured
only to c = 19 and which A173750 (n = 21) and A164325 (n = 20) promote
into on their next find. Paired and interleaved, three rounds, whole
periods from period 1, the fingerprint identical across the variants of
each configuration (ratio to the shipped 0.19):

| configuration (forms) | 0.12 | 0.19 | 0.28 |
|---|---|---|---|
| A173750 n = 21 (c = 20) | 0.977 | **1.000** (`6.28e21 k/s`) | 0.928 |
| A164325 n = 20 (c = 20, odd) | 0.977 | **1.000** (`3.72e21`) | 0.933 |
| A088250 n = 20 (c = 20) | 0.979 | **1.000** (`6.28e21`) | 0.934 |
| A088250 n = 19 (c = 19, the control) | 0.967 | **1.000** (`2.81e21`) | 0.964 |

The last entry stands, c = 21 takes it, and the n = 19 control reproduces
v2's Measurement 7 row. All twelve configurations compiled to 50-58
registers and 8-9 blocks per SM on the full body. **G18** now compiles
every family's resumed filter and the two after it as well as the
openings: 34 configurations, all at 8-9 blocks, no spills.

### Measurement 2 -- nothing in the segment loop scales with the campaign's age

The host side of one launch (`_submit`, `_drain`, `_backpressure`, the
rate-limited save check) on 200 fake launches of 320 real wheel k at
n = 18 through a real 2-worker pool, and the period close (`handle` on the
pending census, `check_rungs`, `status_line`, one save), at three ages:

| campaign age | host per launch | period close | checkpoint | census | survivors |
|---|---|---|---|---|---|
| fresh | 1.25 ms | 471 ms (the ladder's one build) | 621 B | 0 | 6.4e4 |
| 3 days | 1.26 ms | 2.1 ms | 750 B | 5.7e9 | 3.0e9 |
| 30 days | 1.27 ms | 2.4 ms | 780 B | 5.7e10 | 3.0e10 |

Constant: the census is a dict keyed by run length, `pending` empties at
every period close, `passed` is bounded by the ladder, the checkpoint is
under a kilobyte, and the heartbeat's one integral is once per 30 s.
Against 4-13 ms of device per launch at these filters the host is 10-25%
of a launch's wall clock *when the pool is bypassed* and overlapped when
it is not (v2's phase split: host gap under 0.5%). The lock drill, the
durability drill and the interrupt snapshot are unchanged and green.

### What was not done, priced

- **The kernel: untouched.** v2's termination table stands; the priced
  levers (per-lane `ffs` compaction ~8% at c = 15 and ~0 at c >= 17,
  `LDS.128` residue loads ~4%, y-chunked launches at c <= 14) are all
  at filters no resumed campaign runs, or single digits. Not taken.
- **Theorem 17 (N+1, cube root).** Unneeded here (F = N + 1) and not
  needed for subproofs at the measured rate; priced at a day of
  transcription risk against no measured gain.
- **A per-family ceiling.** The certificate cost is symmetric in the
  sign and the unit only helps, so one number; the +1 families lose
  nothing by it and the -1 families gain 17 decades.

### What the gates caught

- **The first per-family harness timed the fallback, not the route.** It
  called `certify_run` on a worst-case k whose values are not prime, so
  every value fell through to `certificate.prove(N)`'s own bounded search
  on both sides -- about a second each, 17-20 s per family. A real
  discovery's values are prime and take the structured route (0.03 s for
  three); the number is real, though, and it is what a value that fails
  its structured proof costs. Rewritten to time prime values.
- **The huntlib ceiling gate's first draft chose multipliers by hand** and
  found one prime value in twelve at 1e41 (a random value there is prime
  one time in 94); it now searches for the first two prime values per
  sign, so it drills both routes every run.
- **CLAUDE.md rule 8, again**: one heredoc with quotes, one dead shell.

### What the A164326 v3 campaign measured (2026-09-04: the resumed acceptance test, run for real)

`--family A164326`, no flags, from the v2 cursor at period 52 (its old
ceiling, `9.998e22`) at 01:29; stopped by hand at 09:02 at period 8,346,
`n = 19`. Two finds, both past the bound and both certified by the N+1
route, and a(19) > 1.6049e25 (RESULTS.md). Per filter, from the evidence
timestamps and the checkpoint:

| filter | line swept | wall clock | campaign rate | the harness / paired figure |
|---|---|---|---|---|
| n = 17 | `1.97e24` | 2.73 h | `2.0e20 k/s` | `1.85e20` (Measurement 1 above), `1.95e20` (v2 campaign) |
| n = 18 | `7.54e24` | 3.88 h | `5.4e20` | `4.9-5.3e20` (A164325 n = 18, paired) |
| n = 19 | `6.44e24` | 56 min | `1.9e21` | `1.8e21` (A164325 n = 19, paired) |

The pool was 1 throughout, no `HOST-BOUND` fragment, and the wall clock
per unit of line matched the device's at every filter, which is the
measurement OPTIMIZATION.md 2.14 says only a campaign can take. The two
certificates cost nothing visible: `k` of a(17) is `30030 * 113 * 3.59e16`
and a(18)'s `unit * 3.3e4 * 4.9e10`, seconds of factoring at most, and
the 34 Theorem 15 proofs re-verified from disk in under a second. Eight
campaigns, twenty-five phases, all at the engine's rate.

---

## v4 -- the WINDOW sieve: the small sieve primes tested 64-128 periods at a time per residue, the survivors through in-block rounds; one reservation per warp. KEPT: 10.5-13x on the frozen windows, 8.8x at the live filters (2026-09-05)

`SCORE 187,807,812,253,300` / `SCORE17 3,341,618,357,877,466` / `SCOREM 47,453,753,517,089`, the three
unit-wheel shapes RE-DENOMINATED (a v4 launch is a different thing; the
new windows were swept by both engines and the fingerprints are their
agreement, below); `SCORE2L`, `SCORE1L` and `SCORE10` reproduce their v1
fingerprints unchanged. 44/44 green. Every number below is a **paired,
interleaved ratio** on the same launches with the survivor fingerprint
checked on every run (the harness rebuilt one engine per variant with the
module cache cleared and warmed the clocks for 1.5 s before each round --
a desktop GPU idles at 285 MHz and a 50 ms measurement taken cold is a
clock measurement); the v3 engine was kept in the tree until the last
pin and then retired (OPTIMIZATION.md rule 0). Nothing here is a campaign
(CLAUDE.md 0a).

### Where v3 stood, and why a constant could not get 10x

Baseline on 2026-09-05, the frozen shapes with the fingerprint checked:
`SCORE` `1.81e11` candidates/s (`2.83e19 k/s`), `SCORE17` `2.22e11`
(`3.73e20`), `SCOREM` `1.45e11` (`7.75e18`); tail rounds 10.7-11.2% of
every launch, entered by 0.78% of candidates. v2's termination table had
the sieve kernel issue-bound at ~12 instructions per candidate per prefix
group -- five groups at c = 15 -- and ~170 issue slots per candidate in
all. The tail alone was 0.5 ns per candidate, which is the WHOLE budget
at 10x. So this pass did not tune the kernel; it replaced its front half.

### The design (OPTIMIZATION.md 2.1: invert the loop)

A candidate is `(t, s, u)` in period j, `k' = Wp*j + off(t, s, u)`. For a
FIXED residue the candidates of consecutive periods form an arithmetic
progression modulo every sieve prime q with an invertible step (`Wp mod
q`; q is above the wheel and not in the unit). So "which of the next P
periods does q kill" depends on `off mod q` alone and is a P-bit WINDOW
into a periodic pattern: with `Dinv = (Wp mod q)^-1`, `r'' = off * Dinv
mod q`, q kills period j0 + j iff `(r'' + j) mod q` is in `C_q = { kr *
Dinv }`. The pattern "bit p set iff p mod q in C_q" is stored once per
prime (2q + 96 bits, ~40-140 bytes), and a window is NW + 1 aligned
32-bit words funnel-shifted by `r'' & 31`. `r''` is linear in the
decomposition `off = (r1_t + W1*A_t) - W1*D_s + Wp*bw`: it is `x0[t] +
ne[s] + bw`, with `x0[t] = (r1 + W1*A_t)*Dinv mod q` a table per
first-level residue (launch-independent, u16, 27 MB at n = 15) and
`ne[s] = (j0 - (W1*D_s)*Dinv) mod q` computed once per block -- the
launch base folds in as `j0 mod q`, because `Wp*Dinv == 1`. Per group per
residue per 64 candidates: one IADD3, three shared loads, two funnel
shifts, two ORs. The survivors (0.7%) are extracted from the live words
and take the per-candidate route -- in-block compaction rounds over
single-prime Barrett tests (round 2's generated tests, now five rounds
deep at a 50% drop), then the unchanged global tail rounds. `G14` checks
the whole chain (x0, ne, bw, pattern word) against `killed_residues` on
sampled candidates at two launch bases, one above 2^64; `G9` pins the
stream to the CPU engine as before; the last act of the v3 engine was to
sweep the new benchmark windows and every family's resumed filter and
return the identical survivors.

### Measurement 1 -- the first build, and the split it hid (rule 1)

The first build returned the IDENTICAL stream to v3 on all three
production configurations and ran 8.9-9.1x faster in the same harness
(`1.37e12` / `8.4e11` / `7.2e11` candidates/s at n = 17 / 15 / c = 14
against v3 driven period by period) -- 4.6-6.2x against the properly
pipelined baseline. Un-pipelined: sieve kernel `1.19e12` at n = 17, tail
rounds 10.6%. The design count said ~6 issue slots per candidate for the
window sieve; the kernel was at ~65 per group per warp-step. Ablations,
each a differential variant of the same source (3.3):

| variant (n = 17) | ratio | what it says |
|---|---|---|
| extraction removed (a data-dependent test that is never true) | **2.87** | two thirds of the kernel was the survivor path, at 0.7% survivors |
| per-lane shared atomics in the extraction replaced by ONE reservation per warp (`warp_reserve`: a shuffle prefix and one atomic) | **1.50** | a same-address shared atomic from k lanes is k-deep |
| round loop unrolled 4 (`ROUND_ILP`) vs 1 | 0.95 | no ILP gain, 4x the round code (477 vs 180 `mul.hi.u64` in the PTX) -- back to 1 |
| the `while (alive)` bit loop replaced by one `if` (wrong answer) | **4.3** | a data-dependent loop INSIDE the residue loop stopped the compiler overlapping one residue's loads with the next's |
| live words written to shared, extraction after the sieve loop | 1.10 | the loop out of the hot body; registers 87 -> 66 |
| the queue-full fallback out of the hot extraction loop (`hotloop`) | 1.10 | the inlined `tail_survives` at the loop's `else` |
| one reservation per EXTRACTION BLOCK of residues and per ROUND, instead of per (residue, word) and per iteration | **1.15** | a reservation is ~300 clocks of dependent latency (five shuffles, a shared atomic, a shuffle); it was made 16 times per warp-step |

### Measurement 2 -- what the window sieve is bound by (2.12, 3.3)

With the survivor path fixed, differential variants of the group body
(same instruction count, wrong answer where noted):

| variant (n = 17) | ratio | verdict |
|---|---|---|
| the pattern loads replaced by a multiply of the same operand | **1.80** (1.56 after the 32-bit words) | the loads are the cost |
| the `ne` shared load replaced by a register expression | 1.05 | not the ne load |
| ONE EXTRA pattern load per word (99 more loads per warp-step, results ORed in) | 0.936 | ... but not their THROUGHPUT: adding as many loads again costs 6%, removing them saves 36%. The kernel is bound by the LATENCY of the load -> funnel-shift chain, with a handful of groups in flight per warp |
| 32-bit pattern words (3 one-cycle loads) instead of overlapping 64-bit entries (2 two-cycle loads) | 1.00 | data-path width is not it either; kept for the smaller tables |
| L1/shared carveout 25 / 75 / 100 (v3's pin was 50) | 1.005 / 1.007 / 1.043 at P = 64; 0.99 / 1.00 at P = 128 | L1 residency is not it: with the whole cache given to shared memory the kernel is no slower. Pinned at 100 (see "What the gates caught") |
| pattern tables in shared memory vs L1 | 1.02 | kept in shared (`PAT_SHARED`) |
| x0 in shared memory (frees 33 registers; +1 load per group) | 0.87 | registers are not the limiter either |
| `__launch_bounds__(128, 8)` / `(128, 6)` | 0.91-0.93 / 0.94 | 72 bytes spilled; 8 blocks buy nothing -- more warps did not hide the latency, so the limit is inside the warp |
| block prologue (the per-residue ne Barretts) replaced by a constant | 0.99 | free |
| window 128 periods (`pb=128`, extraction buffer for one residue) | **1.10** at n = 17, 1.06 at c = 20, 1.00 at c = 15, 1.05 at c = 14 | amortises the per-residue arithmetic and the loads over twice the candidates; 96 periods 1.04; 256 is not admissible on the unit wheel ((PB + 1) W' passes 2^63) |
| extraction buffer every 2 / 4 / 8 residues (P = 64) | 0.99 / 1.00 / 0.86 | shared memory per block: 8 KB of buffer cost a block per SM |

So the window sieve runs at ~30% issue and ~30% load-pipe utilisation
with 20-24 warps per SM and is bound by the dependent chain `ne -> IADD3
-> address -> LDS -> SHF -> LOP` with the compiler keeping a handful of
groups in flight; neither more warps nor fewer registers moved it. What
did move it was fewer chains per candidate (the 128-period window).
**Priced and not done:** software-pipelining two residues by hand
(interleave the loads of residue s + 1 with the shifts of s; the
compiler would not across the loop), and register-resident windows for
primes q <= 64 (a 128-bit doubled pattern in uniform registers, 8 ALU
instructions instead of 3 loads -- only 61 qualifies here).

### Measurement 3 -- the constants, swept on the new engine (3.4)

Interleaved, the fingerprint identical across every variant, ratio to
the shipped value:

| constant | shipped | variants | n = 17 | c = 20 | verdict |
|---|---|---|---|---|---|
| `BIT_SURV` (window depth) | 0.007 | 0.004 / 0.009 / 0.012 / 0.02 | 0.99 / 0.99 / 0.94 / 0.79 | -- | the crossover between a window group (~10 instructions per prime per 64 candidates whatever it kills) and a per-candidate test (~15 per entrant) is at ~1% survival; 0.7% |
| `K2_SURV4` (in-block rounds end, global tail start) | 0.0003 | 0.0005 / 0.001 / none (0.007) | 1.00 / 0.99 / **0.72** | 1.00 / 1.00 / 0.79 | the in-block rounds are 3-4x cheaper per item than the global tail's first round; flat between 3e-4 and 1e-3 |
| CRT pairs in the rounds (`K2_GROUP_MAX4` 2^19) | 1 (singles) | pairs | **0.54** | -- | 10-90 KB tables gathered from L2 |
| `TAIL_ROUND_DROP` | 0.5 | 0.3 / 0.7 | 0.99 / 1.02 | 0.99 / -- | flat |
| `UNROLL` (tail chains) | 4 | 2 / 8 | -- / 1.035 | -- / 1.007 | inside the band |
| `TAIL_FILL` | 2^19 | 2^21 | 1.01 | -- | flat |
| `SPB` | 8 | 4 / 16 | 0.99 / 0.88 | -- / 0.89 | 16 costs shared memory |
| `TPB` | 128 | 256 | 0.89-0.96 | 0.96 | 3 blocks per SM |
| `EXTRACT_EVERY` at NW = 4 | 1 | 2 | 0.98 (of the 1.10) | -- | the buffer again |

### The tail (unchanged code), measured round by round

One n = 17 launch of `3.4e10` candidates (P = 64): sieve kernel 17.3 ms,
13 tail rounds 1.68 ms (8.8%): rounds 0-4 (primes 691-3187, `1.0e7` down
to `6e5` items) 1.09 ms of real work at ~40 ns per item in round 0, rounds
5-12 (lanes per item 2-32, `3e5` down to `2.4e3` items) 0.59 ms of
latency at 45-130 us each. At the openings the tail is 14-17% of the
kernel (n = 15, c = 14), not because it costs more per candidate -- it is
~0.1 ns per candidate at both n = 15 and n = 17, the same 0.03% of
entrants -- but because the rest of the kernel costs more there: 43-51
window groups against 24-33 and 123 round primes against 74, so the
sieve's share of the launch grows and the tail's with it. **Priced and
not done:** merging the
last rounds (a 0.3 drop measured flat), a second stream for the rounds
(v2 measured 0.98-1.00 with a saturating sieve; the window sieve is
latency-bound at 30% issue, so it may hide now -- not built), bigger
launches (`CAND_PER_LAUNCH4` 2^35: 2^36 doubles the global queues to
0.5 GB per launch).

### Where the time goes now (the termination table, OPTIMIZATION.md Part 3)

| phase (n = 17 / c = 20) | share | verdict |
|---|---|---|
| window sieve | ~65% / ~70% | latency-bound on the load -> shift chain (Measurement 2: loads removed 1.56-1.8x, loads doubled 0.94x, carveout and registers flat, more warps flat); the 128-period window is the lever that paid. Two priced levers left: hand-pipelined residues, register windows for q <= 64 |
| in-block rounds | ~18% / ~15% | five rounds of ~15 single-prime Barrett tests each, all lanes alive; one reservation per round. The ceil-waste (rounds with fewer items than threads run one iteration at 21-86% lane use) is ~30% of the phase: lanes-per-item for the small rounds, priced at ~3% of the total, not built. Storing `off` in the later queues saves the `off_of` per round (~2%, +4 KB shared) |
| extraction | ~5% | one reservation per block of residues; the bit loop after the sieve loop |
| tail rounds | 7-9% (14-17% at c <= 15) | see above |
| host + prologue | < 2% | the prologue is free (Measurement 2); the pipelined loop's gap under 0.5% |

### Measurement 4 -- the pin against v3, and the rates that stand

The v3 engine was kept in the tree until it had swept the same windows as
v4 (whole periods, so no launch decomposition of either engine is in the
comparison) and returned the identical survivors, family by family at the
filter each campaign resumes at:

| configuration | window | survivors | v4 candidates/s | v4 k/s | v3 candidates/s | ratio |
|---|---|---|---|---|---|---|
| A088250 n = 18 (c = 18) | the 128-period segment at period 1 | 596,704 | `2.18e12` | `1.29e22` | `2.35e11` | **9.3x** |
| A088250 n = 19 (c = 19) | the 128-period segment at period 1 | 112,795 | `2.35e12` | `2.60e22` | `2.52e11` | **9.3x** |
| A088250 n = 20 (c = 20) | the 128-period segment at period 1 | 19,312 | `2.52e12` | `5.71e22` | `2.73e11` | **9.2x** |
| A173750 n = 21 (c = 20) | the 128-period segment at period 1 | 19,324 | `2.53e12` | `5.73e22` | `2.74e11` | **9.2x** |
| A164325 n = 20 (c = 20) | the 128-period segment at period 1 | 33,071 | `2.54e12` | `3.37e22` | `2.77e11` | **9.2x** |
| A125838 n = 20 (c = 19) | the 128-period segment at period 1 | 112,028 | `2.38e12` | `2.64e22` | `2.51e11` | **9.5x** |
| A125839 n = 20 (c = 18) | the 128-period segment at period 1 | 1,194,610 | `2.20e12` | `6.50e21` | `2.35e11` | **9.4x** |
| A164326 n = 19 (c = 19) | the 128-period segment at period 1 | 176,296 | `2.36e12` | `1.66e22` | `2.50e11` | **9.4x** |
| A088651 n = 18 (c = 18) | the 128-period segment at period 1 | 598,191 | `2.18e12` | `1.29e22` | `(not run; A088250's n = 18 wheel, 2.35e11)` | **~9.3x** |

and on the three re-frozen benchmark windows: `SCORE` (one third-level
residue of the 64-period segment at period 1, `7.36e19` of line) 150,985
survivors, xor 144395210679418703534414 from both, `1.23e12` against
`9.4e10` candidates/s (13.1x); `SCORE17` (eight residues of the 128-period
segment, `1.30e21`) 31,431 / 118193132530909840366348, `1.85e12` against
`1.77e11` (10.5x); `SCOREM` (one residue of the 64-period segment,
`7.01e19`) 1,166,647 / 240031737716965866902, `9.07e11` against `8.0e10`
(11.3x). (The v3 side of those three is v3 driven one period at a time
without its pipeline; against v3's own pipelined benchmark rates --
`1.81e11`, `2.22e11`, `1.45e11` -- v4's score.py rates are 6.6× / 9.0× / 6.1×.)
Then `GpuEngineV3` and its template were deleted; the CPU parity gate
(G9, 25 windows) and the three k-space fingerprints are the permanent
other half.

### Measurement 5 -- the resumed campaigns, calibrated on their real checkpoints (5g)

Each family's REAL checkpoint copied to a scratch path, loaded through
the v4 policy into a `Campaign` (every one `inherited`; A088651's u = 945
floored to 0 with its line), and `Campaign.calibrate()` on the launches
the loop would run next -- about a second of device, nothing recorded:

| family | filter (c) | launches in 1 s | k/s | survivors/s | us each | core-s/s | pool |
|---|---|---|---|---|---|---|---|
| A088250 | n = 18 (18) | 81 | `1.385e22` | 33,866 | 12.0 | 0.41 | 1 |
| A173750 | n = 20 (19) | 80 | `2.861e22` | 13,149 | 11.9 | 0.16 | 1 |
| A125838 | n = 19 (18) | 82 | `6.965e21` | 33,498 | 11.7 | 0.39 | 1 |
| A125839 | n = 19 (17) | 71 | `2.286e21` | 83,083 | 13.4 | 1.12 | 3 |
| A164325 | n = 19 (19) | 101 | `1.818e22` | 12,864 | 12.4 | 0.16 | 1 |
| A164326 | n = 19 (19) | 101 | `1.811e22` | 13,115 | 14.1 | 0.19 | 1 |
| A088651 | n = 18 (18) | 82 | `1.391e22` | 33,370 | 12.7 | 0.42 | 1 |

and the fresh openings (a scratch checkpoint at period 0): A088250
n = 15 `1.967e20 k/s`, 404,145 survivors/s, 4.63 core-s/s, pool 10;
A125838 n = 15 `5.004e19`, 850,726/s, 9.94 core-s/s, pool 20 (of the 31
a 32-core host offers); A164325 n = 16 `3.372e20`, 200,642/s, 2.31,
pool 5. Segment 0 takes 626 s, 2,459 s and 730 s of device at those
openings. So the load picture inverted (CLAUDE.md 5f): the openings are
now host-heavy and the resumed filters trivially light, and the pool
sized from the measurement is what makes both defaults right. Every
`swept to` equalled the file's k; every next segment sat under the
ceiling.


### What the gates caught during the build

- **A `ROUND(off, kl)` macro invoked on a variable named `off`**: its
  first line `const unsigned long long off = (OFF);` initialised the new
  `off` from itself. Three parity cases lost or gained survivors; the
  argument is now `oz`. A macro that declares what it is passed is a
  trap, and the parity test was the only thing that could see it.
- **A runtime-indexed `keep[]` array in the rounds went to local memory**
  (40 bytes): 20x slower, same stream. Replaced by a survivor bitmask.
- **Two ablations that priced the wrong thing** (OPTIMIZATION.md 3.3):
  removing the queue STORE left the reservation's count in place, so the
  rounds ran on uninitialised queue entries (0.43x, meaningless); and
  the first "no extraction" variant removed the loop and with it the
  compiler's constraint, so its 2.9x was two effects, separated later
  into 1.5x (atomics) and 1.10x (the loop's placement).
- **The gate windows of 16 and 32 periods measured the engine at a
  quarter and a half of its rate**: a segment is 64-128 periods and the
  live-period mask idles the rest of the window. The engine's coverage
  unit is the segment; the launcher never sweeps less (except at the
  ceiling), and the benchmark windows are whole segments.
- **The k-space wheel to 47 (W' = 6.2e17) cannot hold 32 periods under
  the 2^63 reduction bound** ((PB + 1) W' + q2 < 2^63 caps it at 14) and
  the first build raised at construction, failing G14 and G17. The
  window's bit width (PB, a multiple of 32) is now decoupled from the
  periods a segment holds (PV <= PB, chosen under the bound; the bits past
  PV are masked): that wheel runs 14 live periods in a 32-bit window, the
  unit wheel 128 in 128, and G17's three-wheel leg returned its 799
  survivors identically from all three.
- **G18 read the same configuration at 3 blocks per SM in the battery and
  5 in a harness.** The occupancy API's answer depends on the carveout
  attribute, and CuPy hands every engine with identical source the same
  compiled function, so a query made before the pin can read another
  engine's pin. Probed directly: at the 50% pin (64 KB, 1 KB reserved per
  block) the 128-period kernels of 14-15 KB fit 3-4 times; at 75 and 100
  the register file sets the occupancy (5-7). Timing is flat across the
  three (0.99-1.00 at n = 16 and 17): the kernel is bound inside the warp,
  not by warps. The sieve kernel is now pinned at 100% shared (its tables
  are in shared memory; v3's pin at 50 protected L1 tables that no longer
  exist), the occupancy is measured AFTER the pin, and G18's floor is 4.
- **Shallow gate configurations (two sieve primes above the wheel) sized
  a 65,536-entry shared queue**: `QUEUE_BYTES_MAX` halves the analytic
  capacities until the block's queues fit 12 KB; overflow is the harmless
  fallback, exercised by G14's forced-overflow drill as before.
- **CLAUDE.md rule 8, twice**: two heredocs with escapes inside quotes,
  two dead edits.

### What changed for the launcher (CONVENTIONS.md "Two cursors")

The coverage unit is the SEGMENT: `eng.seg_periods` periods (64 at
c <= 15, 128 from c = 16), swept in `eng.launches_per_segment` launches of
a first-level chunk x a few third-level residues x every second-level
residue x every period of the segment. The work cursor `u` is the launch
index inside the segment; a v2/v3 cursor (`u` a third-level residue index
of one period) is inherited at its period with `u` floored to 0, which
re-sweeps at most one period. The over-sweep at a find is one segment:
`1.23e23`-`2.46e23` of k -- 20 minutes at A088250's n = 15, 1.7 hours at
A125838's c = 14 opening at P = 64 (the reason the width is 64 there),
and 5-20 s at the resumed filters where the campaigns run. The
heartbeat's `periods [j, j+seg) ..%` is progress through the segment.

