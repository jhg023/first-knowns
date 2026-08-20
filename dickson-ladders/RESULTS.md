# RESULTS — dickson-ladders

Verified finds live here in discovery order, each with its exact
integers, its verification record, its factor witness for the
run-breaking composite, and — specific to this project — a primality
certificate for every value claimed prime. Evidence JSONs in
`evidence/`.

## Standing state (2026-08-18)

**Three new terms found and verified**, the first computational advance on
A247965 since October 2014:

| n | value | status |
|---|-------|--------|
| a(9) | 3,332,396,388,090 | Hiroaki Yamanouchi, Oct 2014 |
| **a(10)** | **9,328,409,578,841,430** | **found 2026-08-18** |
| **a(11)** | **433,871,469,806,557,860** | **found 2026-08-18** |
| **a(12)** | **55,119,263,286,518,170,740** | **found 2026-08-18** |
| a(13) | open, no bound published | the hunt continues |

All three were found in the first minutes of a campaign, all three were
verified four ways (below), and the sweep that produced them is contiguous
from k = 10⁴, which is what makes them *least* values rather than merely
examples. Prior published lower bounds — a(10) > 1.54665×10¹³ and
a(11) > 1.076691×10¹⁴ — are consistent: the finds sit 600× and 4,000×
above them. No bound had been published for a(12).

These are **candidates for OEIS in the repository owner's hands, not
submissions**: the pipeline records, humans decide (CLAUDE.md rule 5).

## A247965(10) = 9,328,409,578,841,430

Found 2026-08-18, in the campaign's first minutes, at k ≈ 9.33×10¹⁵.

- m·k²+1 is prime for every m = 1..10 — ten simultaneous primes of 32–33
  digits.
- The run breaks at m = 11: 11k² + 1 =
  957,211,477,976,825,999,698,551,928,893,901 = **1,425,733** ×
  671,382,003,486,505,537,641,726,697, so the run is exactly 10.
- k = 2 · 3 · 5 · 7 · 11 · 1,282,297 · 3,149,249 — a multiple of
  W(10) = 2310, as the wheel argument forces.
- Least-claim basis: every multiple of 2310 from 10⁴ to k was classified
  and failed, each failure a proof (a small prime dividing one of the ten
  values, or a failed strong Fermat test).
- Model quantile of the find: **0.915** (E = 2.47; median predicted
  1.68×10¹⁵, so it landed 5.5× past it).
- Evidence: `evidence/ladder_hit_run10_k9328409578841430.json`

## A247965(11) = 433,871,469,806,557,860

Found 2026-08-18 at k ≈ 4.34×10¹⁷, minutes later in the same campaign.

- m·k²+1 is prime for every m = 1..11 — eleven simultaneous primes of
  36–37 digits.
- The run breaks at m = 12: 12k² + 1 =
  2,258,933,427,745,234,185,047,139,138,333,355,201 = **13** ×
  173,764,109,826,556,475,772,856,856,794,873,477.
- k = 2² · 3³ · 5 · 7 · 11 · 37 · 643 · 438,595,237 — also a multiple of
  W(11) = 2310, the wheel being unchanged from n = 10 (both take the
  primes ≤ 12).
- Least-claim basis: the same contiguous ascending sweep, unbroken from
  10⁴ through this k, with every survivor classified.
- Model quantile of the find: **0.923** (E = 2.57; median predicted
  7.18×10¹⁶, so it landed 6.0× past it).
- Evidence: `evidence/ladder_hit_run11_k433871469806557860.json`

## A247965(12) = 55,119,263,286,518,170,740

Found 2026-08-18 at k ≈ 5.51×10¹⁹, **9 minutes 45 seconds** into the
re-configured campaign — the first find of the 30030-wheel sweep, and 127×
above a(11).

- m·k²+1 is prime for every m = 1..12 — twelve simultaneous primes of
  40–41 digits.
- The run breaks at m = 13: 13k² + 1 =
  39,495,731,408,230,628,656,925,688,254,545,297,918,801 = **173** ×
  228,299,025,481,101,899,751,015,539,043,614,438,837 (itself composite),
  so the run is exactly 12.
- k = 2² · 3² · 5 · 7 · 11 · 13 · 1,171 · 261,240,151,283 — a multiple of
  W(12) = 30030 = 2·3·5·7·11·13, which is what the wheel argument forces
  once 13 is in play, and the reason the coarser sweep could reach here at
  all.
- Least-claim basis: every multiple of 30030 from 10⁴ to k was classified
  and failed. The sweep changed wheels twice on the way (2310 → 30030 as
  the filter followed the frontier), and each widening was re-denominated
  by floor — an overlap of under one period, never a gap — so contiguity
  is unbroken across the changes; every k the coarser wheel skips is
  *proved* not to be a(12) by the same divisibility argument.
- Model quantile of the find: **0.787** (E = 1.54; median predicted
  1.83×10¹⁹, so it landed 3.0× past it — between the model's Q3 and its
  P90).
- Evidence: `evidence/ladder_hit_run12_k55119263286518170740.json`

### What the three finds say about the model

All three landed late — quantiles 0.915, 0.923 and 0.787, i.e. E = 2.47,
2.57 and 1.54 where the median wait is ln 2 ≈ 0.69. The third was the
mildest of them, which *lowers* the estimated bias: pooling all three as
Exp(1) draws gives a maximum-likelihood optimism factor of **2.2×** (down
from 2.5× on two) with a 95% interval of about **[0.9, 10.6]** (from
[0.9, 20.8]). The interval still contains 1, so this is still not evidence
that the singular series is wrong — but the one-sided tail is now
P(ΣE ≥ 6.58 | three Exp(1) draws) = **0.04**, which is where a third
consecutive late draw does start to be worth watching rather than merely
noting. The honest reading: the model is not yet falsified, it has been
pessimistic-about-depth three times running, and a(13) is the draw that
decides it.

Stated as predictions rather than post-hoc: the same model puts a(13)'s
median at 2.14×10²¹ and its P90 at 1.10×10²². If the 2.2× factor is real
rather than luck, a(13) lands nearer 4×10²¹ than 2×10²¹.

The validation table below (six known terms, E scattering around 1) was
computed before the run and is unchanged by these three.

## Verification

Every claim above survived the project's four-way protocol, and all three
were **re-verified from their evidence files** before publication — the
whole protocol re-run from scratch, plus an independent re-check of every
stored certificate:

| leg | a(10) | a(11) | a(12) |
|-----|-------|-------|-------|
| engine SPRP chain + sympy BPSW agree on the run length | ok | ok | ok |
| alternate-alignment re-sieve (coarser wheel, numpy `%`, not the GPU's Barrett path) | ok | ok | ok |
| BLS75 primality certificates, re-checked from scratch | 10/10 | 11/11 | 12/12 |
| factor witness for the run breaker | 1,425,733 | 13 | 173 |
| sympy `isprime` on every value, independently | 10/10 | 11/11 | 12/12 |
| stored k factorization re-multiplied, factors re-proved prime | ok | ok | ok |

The certificates matter here rather than being decoration: m·k²+1 passes
huntlib's deterministic Miller–Rabin bound (3.317×10²⁴) before a(9), so
probable-prime tests would be evidence and not proof. N − 1 = m·k² is our
own number, fully factored by construction, which is exactly what
Brillhart–Lehmer–Selfridge Theorem 1 needs.

## The machinery behind the claims

Rediscoveries rather than discoveries — but they are the reason the two
finds above are believable, they run before every campaign, and anyone
can check them today:

- **The oracle re-derives a(1)–a(6) exhaustively from the definition**
  (G2), sweeping k one integer at a time below the wheel argument's
  exception zone and on the wheel above it. a(6) = 30,473,520 comes back
  in under two seconds.
- **The CPU engine re-derives a(7) and a(8) end-to-end as first
  occurrences** (G5) — not "finds them", *finds them first*, sweeping
  from k = 10⁴.
- **The GPU engine re-derives a(7)** the same way (G8), and the
  launcher's canary prelude re-derives **a(7), a(8) and a(9)** through
  whichever engine production is about to use. a(9) = 3,332,396,388,090
  is the deepest: 1.6×10¹⁰ wheel candidates swept to reach it.
- **The two engines agree bit-for-bit** on populated windows from
  j = 10⁶ to the enforced ceiling 4×10¹⁸ (G6), and the GPU stream is
  independent of how the work is sliced (G13).
- **The kernel's decisions equal big-integer divisibility** of the
  actual values m·k²+1, checked with no engine on the other side of the
  comparison (G14).
- **The certificate machinery works on real values past the
  deterministic-MR bound**: a(9)'s nine values (up to 10²⁶) each carry a
  Brillhart–Lehmer–Selfridge witness set that re-verifies from scratch,
  and the verifier rejects both a forged witness and a falsified
  factorization (G11). The witness search is open-ended over the primes,
  because the wheel primes can never witness p = 2 here (README, item 5);
  G12 replays a genuine run-10 value whose m = 2 certificate needs base 41.

## The least-claim, and what it rests on

"a(10) = 9,328,409,578,841,430" means: every multiple of W(10) = 2310
from 10⁴ to that k was classified, every one below it failed, and the
failures are *proofs* — a small prime dividing one of the ten values, or
a failed strong Fermat test. The same holds for a(11) through
4.34×10¹⁷, and for a(12) through 5.51×10¹⁹ on W(12) = 30030. "These
values are prime" rests on certificates rather than probable-prime tests,
because m·k²+1 outgrows deterministic Miller–Rabin before a(9).

Non-multiples of 2310 need no sweeping and are not a gap: the wheel is
forced by the argument in the README, and G1 checks it against every
published term rather than trusting it. The oracle owns [1, 10⁴), where
the wheel argument has an exception zone, and sweeps it exhaustively at
every campaign start.

The sweep's contiguity is a property of the machinery, not a promise: the
cursor advances only past a *fully classified* segment, so an interrupt or
a crash redoes a segment rather than skipping one — which was exercised
for real: a campaign stopped abruptly mid-segment and the resume
re-covered it.

## Census

Values below the frontier are counted, not narrated (CONVENTIONS.md).
Two campaigns have reported counts, and **they are not comparable to each
other** — which is worth stating rather than quietly tabulating, because
the second set looks like a regression and is not.

The a(10)/a(11) campaign, sieving one step behind the frontier on the
2310 wheel, at k ≈ 1.4×10¹⁹:

| run | 7 | 8 | 9 | 10 | 11 |
|-----|---|---|---|----|----| 
| count | 11,447 | 2,649 | 606 | 140 | 35 |

The a(12) campaign, sieving for the next open term on the 30030 wheel, at
k ≈ 8.73×10¹⁹ (33,199,184 survivors classified in 13.5 minutes):

| run | 7 | 8 | 9 | 10 | 11 | 12 |
|-----|---|---|---|----|----|----| 
| count | 1,368 | 352 | 78 | 27 | 2 | 1 |

The second campaign covered 6× more k-line and counted 8× fewer run-7s,
because a census count is a count of what the sweep *examined*: on the
30030 wheel twelve of every thirteen 2310-multiples are never candidates
at all — each is proved not to be a(12) by divisibility, not by
classification. The census is a by-product of the hunt, not a measurement
of the k-line, and only counts taken at the same filter can be compared.

Within each campaign the counts fall by roughly the factor the model
predicts per added constraint, which is a weak but free consistency check
on the sieve. Each run-11 and run-12 value was verified when met; none is
evidenced, because `evidence/` holds first occurrences only.

## In progress

The campaign is **hunting a(13)**, which the model puts at median
2.14×10²¹ — the sweep is past the P90, standing at k = 1.10×10²² with the
census at `7:17161 8:3876 9:822 10:168 11:51 12:8`. It runs indefinitely
to the enforced ceiling of its wheel (the last rung) unless stopped;
`--stop-on-discovery` and `--to` are the deliberate stops, and Ctrl+C
checkpoints at the last completed segment and exits cleanly.

Two 2026-08-19 changes bear on the claims and the reach, both gated
before resuming:

- **A verification-path crash was found by the campaign itself and
  fixed.** At k = 1.097×10²² a run-12 `[NEAR]` verification converted k
  to j on the *coarser* alternate-alignment wheel (2310), crossed the
  enforced j ceiling — which the coarse wheel reaches at k = 9.24×10²¹,
  13× before the campaign's own wheel — and halted the run with the
  checkpoint intact at a segment boundary. The leg now consults the
  alternate table directly in Python integers (same table, same
  mathematics, no ceiling), and the selftest drills it at the exact j
  that raised. **No recorded value is affected**: the leg only ever
  checked membership of k, and every earlier verification ran below the
  coarse wheel's reach.
- **The engine folded its first sieve prime into candidate generation**
  (v4): j = 17u + r over the five surviving offsets, an identical
  survivor stream (G17 pins folded == unfolded bit for bit, and the
  frozen fingerprints reproduce), measured **2.39× end-to-end** at the
  campaign configuration — and the enforced reach moved from
  k = 1.20×10²³ to **k = 2.04×10²⁴**, which is what makes **a(14)**
  (median 1.68×10²³, past the old ceiling) a realistic continuation of
  the same sweep: E = 4.41 (98.8%) inside the new reach, against
  E = 0.54 (42%) inside the old one.

The find moved the hunt itself: the filter followed the frontier from 12
to 13 the moment a(12) was verified. The wheel is unchanged at 30030 —
W(13) also takes the primes ≤ 14 — so the cursor did not need
re-denominating, and the sweep continued from where it stood.

**The campaign was re-configured on 2026-08-18** for a measured 27.9×
end-to-end — 2.4×10¹⁵ → 6.8×10¹⁶ k/s — and a(12) is what that bought:
found 9 minutes 45 seconds after the re-configured campaign started, where
the old configuration would have needed about six and a half hours to
reach the same depth. Almost none of it was the kernel. The hunt had been
sieving one step behind the frontier, on a 2310 wheel when
a(12) is necessarily a multiple of 30030, and classifying every survivor
with all seven Miller–Rabin bases when a single base-2 test *proves* most
of them short. Details and measurements in
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3.

Two things about that re-configuration belong in a results file rather
than an optimization log, because they bear on what the claims rest on:

- **A latent correctness bug was found and fixed.** The kill-bit table's
  residue walk squares a value below q, so it needs q² to be exact; it was
  32-bit, valid only for q < 2¹⁶, and every gate in the engine ran at the
  default sieve depth of 65536, so nothing had ever evaluated a prime past
  that. It is u64 now, and `g16_deep_sieve_arithmetic` gates it above 2¹⁶.
  **No published result is affected**: a(10) and a(11) were found, verified
  and re-verified at q2 = 65536, entirely inside the range the old
  arithmetic was exact for, and the frozen benchmark fingerprints (also at
  65536) are unchanged. The bug could only ever have been reached by
  asking for a deeper sieve, which nothing did until now.
- **The claim that this is a contiguous least-first sweep is unchanged**
  by the move to the 30030 wheel. run(k) ≥ 12 forces 13 | k — m runs over
  a complete residue system mod 13, so some m has m·k² ≡ −1 (mod 13), and
  that value exceeds 13 above the floor — so every k the coarser wheel
  skips is proved not to be a(12). The cursor was re-denominated by floor,
  which overlaps by under one period and never gaps.

That third draw has now landed, and it came in milder than the first two:
the pooled optimism factor fell from 2.5× to 2.2× and its interval still
contains 1, while the one-sided tail tightened to 0.04. So the question
the last edition of this file posed is answered "not yet, and now watch
a(13)" — which is the honest place for it to be after three events.
