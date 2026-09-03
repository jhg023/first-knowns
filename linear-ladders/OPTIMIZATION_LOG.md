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
