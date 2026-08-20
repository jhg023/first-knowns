# RESULTS — dickson-ladders

Verified finds live here in discovery order, each with its exact
integers, its verification record, its factor witness for the
run-breaking composite, and — specific to this project — a primality
certificate for every value claimed prime. Evidence JSONs in
`evidence/`.

## Standing state (2026-08-20)

**Four new terms found and verified**, the first computational advance on
A247965 since October 2014:

| n | value | status |
|---|-------|--------|
| a(9) | 3,332,396,388,090 | Hiroaki Yamanouchi, Oct 2014 |
| **a(10)** | **9,328,409,578,841,430** | **found 2026-08-18** |
| **a(11)** | **433,871,469,806,557,860** | **found 2026-08-18** |
| **a(12)** | **55,119,263,286,518,170,740** | **found 2026-08-18** |
| **a(13)** | **12,094,123,415,384,869,458,600** | **found 2026-08-19** |
| a(14) | open, no bound published | campaign paused, resumable |

All four were verified four ways (below), each was re-verified from its
evidence file before publication, and the sweep that produced them is
contiguous from k = 10⁴, which is what makes them *least* values rather
than merely examples. Prior published lower bounds — a(10) > 1.54665×10¹³
and a(11) > 1.076691×10¹⁴ — are consistent: those finds sit 600× and
4,000× above them. No bound had been published for a(12) or a(13).

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

## A247965(13) = 12,094,123,415,384,869,458,600

Found 2026-08-19 at k ≈ 1.21×10²², 219× above a(12) — **58 minutes after
the v4 fold's commit landed** and the campaign resumed from
k = 1.097×10²², where the verification-leg crash (below) had stopped it:
1.12×10²¹ of k-line under the folded engine, and the fold is what made
the depth routine.

- m·k²+1 is prime for every m = 1..13 — thirteen simultaneous primes of
  45–46 digits.
- The run breaks at m = 14: 14k² + 1 =
  2,047,749,496,611,848,115,619,307,470,334,282,799,595,440,001 =
  **2,711** × 755,348,394,176,262,676,362,710,243,575,906,602,580,391
  (itself composite), so the run is exactly 13.
- k = 2³ · 3 · 5² · 7² · 11 · 13 · 17 · 294,293 · 574,992,493 — a
  multiple of W(13) = 30030, as the wheel argument forces. (17 | k is
  chance, not force: the wheel takes only the primes ≤ 14.)
- Least-claim basis: every multiple of 30030 from 10⁴ to k was classified
  and failed, each failure a proof. Contiguity is unbroken across the
  wheel changes far below it and across the one crash-and-resume, which
  redid its in-flight segment from the checkpointed boundary.
- Model quantile of the find: **0.916** (E = 2.48; median predicted
  2.14×10²¹, so it landed 5.7× past it — 10% beyond the model's P90,
  later relative to prediction than every earlier find except a(11)).
- Evidence: `evidence/ladder_hit_run13_k12094123415384869458600.json`

### What the four finds say about the model

All four landed late — quantiles 0.915, 0.923, 0.787 and 0.916, i.e.
E = 2.47, 2.57, 1.54 and 2.48 where the median wait is ln 2 ≈ 0.69. The
previous edition of this file said a(13) was the draw that would decide
whether three consecutive late draws meant anything. It has, and it came
in late again — its own adjusted guess ("nearer 4×10²¹ than 2×10²¹") was
itself too shallow by 3×. Pooling all four as Exp(1) draws gives a
maximum-likelihood optimism factor of **2.26×** with a 95% interval of
**[1.03, 8.31]** — which for the first time **excludes 1** — and the
one-sided tail P(ΣE ≥ 9.06 | four Exp(1) draws) = **0.020**.

The honest reading, with its own caveats attached: four draws is a small
sample and the interval clears 1 by very little, but the question was
posed before the draw, and it resolved against the model. The working
conclusion is that the singular-series model is **optimistic about depth
by a factor of about 2** for this family — read its medians as nearer
their Q3s. What this is *not* is evidence against Dickson/Bateman–Horn:
the terms keep existing and keep being found, just deeper than the
truncated series predicts, which is the signature of a small systematic
bias in C_n rather than of a missing obstruction. a(14) is the clean
out-of-sample test: median 1.68×10²³ as published, nearer 3.8×10²³ if
the 2.26× factor is real — both inside the folded reach.

The validation table in the README (six known terms, E scattering around
1) was computed before the run and is unchanged by these four.

## Verification

Every claim above survived the project's four-way protocol, and all four
were **re-verified from their evidence files** before publication — the
whole protocol re-run from scratch, plus an independent re-check of every
stored certificate:

| leg | a(10) | a(11) | a(12) | a(13) |
|-----|-------|-------|-------|-------|
| engine SPRP chain + sympy BPSW agree on the run length | ok | ok | ok | ok |
| alternate-alignment re-sieve (different wheel alignment, sympy square roots and plain `%`, not the GPU's Barrett path) | ok | ok | ok | ok |
| BLS75 primality certificates, re-checked from scratch | 10/10 | 11/11 | 12/12 | 13/13 |
| factor witness for the run breaker | 1,425,733 | 13 | 173 | 2,711 |
| sympy `isprime` on every value, independently | 10/10 | 11/11 | 12/12 | 13/13 |
| stored k factorization re-multiplied, factors re-proved prime | ok | ok | ok | ok |

a(13)'s alternate-alignment leg ran in the post-crash direct-table form
(Python integers, no j ceiling — see below); what is checked is unchanged.

The certificates matter here rather than being decoration: m·k²+1 passes
huntlib's deterministic Miller–Rabin bound (3.317×10²⁴) before a(9), so
probable-prime tests would be evidence and not proof. N − 1 = m·k² is our
own number, fully factored by construction, which is exactly what
Brillhart–Lehmer–Selfridge Theorem 1 needs.

## The machinery behind the claims

Rediscoveries rather than discoveries — but they are the reason the four
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
4.34×10¹⁷, and for a(12) and a(13) through 5.51×10¹⁹ and 1.21×10²² on
W(12) = W(13) = 30030. "These
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

The a(12)/a(13) campaign, sieving for the next open term on the 30030
wheel, at its pause point k = 1.57×10²² (956,235,834 survivors classified
over 25.1 h of campaign wall clock):

| run | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|-----|---|---|---|----|----|----|----|
| count | 19,446 | 4,349 | 927 | 183 | 59 | 9 | 1 |

This campaign covered orders of magnitude more k-line per count than the
first, because a census count is a count of what the sweep *examined*: on
the 30030 wheel twelve of every thirteen 2310-multiples are never
candidates at all — each is proved not to be a(12) by divisibility, not
by classification — and a shorter run is counted only when its breaker
also escapes the sieve depth. The census is a by-product of the hunt, not
a measurement of the k-line, and only counts taken at the same filter can
be compared.

Within each campaign the counts fall by roughly the factor the model
predicts per added constraint, which is a weak but free consistency check
on the sieve. The run-13 count is the a(13) find itself; of the nine
run-12s, the first is the a(12) find and the rest are census repeats,
each verified when met, none evidenced, because `evidence/` holds first
occurrences only.

## Paused (2026-08-20)

With a(13) found and verified, the owner paused the campaign to move to
other work. Where it stands, all of it in the checkpoint:

- cursor k = 1.57×10²² (next_j = 521,960,159,937,822,721 on the 30030
  wheel), filter n = 14, contiguous from the floor;
- 956,235,834 survivors classified over 25.1 h of campaign wall clock;
- census at pause: `7:19446 8:4349 9:927 10:183 11:59 12:9 13:1`;
- every a(13) rung is passed and retired; the ladder aims at a(14).

The hunt is left resumable: `python launch.py` continues from the
checkpointed boundary. **Resuming starts with `python launch.py
--selftest` and `python score.py`** — that is where any shared change
made while the project sleeps gets proved on it (repo rule,
CONVENTIONS.md).

What the remaining sweep is worth: from the pause cursor to the folded
ceiling k = 2.04×10²⁴ is E = 4.28 for a(14) — a **98.6%** model chance,
≈85% under the 2.26× pooled optimism factor — about 8.5 days of sweep to
the a(14) median and 43 days to its P90 at the paired v4 rate. The wheel
does not widen again until filter 16, so a resumed campaign rides the
same 30030 wheel and the same cursor to the end of the ladder.

Two 2026-08-19 changes bear on the claims and the reach, both gated
before the sweep that found a(13) resumed:

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

Each find moved the hunt itself: the filter followed the frontier from 12
to 13 the moment a(12) was verified, and from 13 to 14 the moment a(13)
was. The wheel is unchanged at 30030 across both — W(13) and W(14) also
take the primes ≤ 14 and ≤ 15 — so the cursor never needed
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

The fourth draw has now landed too, and it broke the softening trend of
the third: a(13) came in at quantile 0.916, the pooled optimism factor
rose from 2.19× to 2.26×, and its 95% interval — [1.03, 8.31] — no
longer contains 1. The question this file carried through three finds
("is the model optimistic about depth?") is answered "probably, by about
2×", and a(14), the next open term, is the out-of-sample test of exactly
that number.
