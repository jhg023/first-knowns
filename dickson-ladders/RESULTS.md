# RESULTS — dickson-ladders

Verified finds live here in discovery order, each with its exact
integers, its verification record, its factor witness for the
run-breaking composite, and — specific to this project — a primality
certificate for every value claimed prime. Evidence JSONs in
`evidence/`.

## Standing state (2026-08-18)

**Two new terms found and verified**, the first computational advance on
A247965 since October 2014:

| n | value | status |
|---|-------|--------|
| a(9) | 3,332,396,388,090 | Hiroaki Yamanouchi, Oct 2014 |
| **a(10)** | **9,328,409,578,841,430** | **found 2026-08-18** |
| **a(11)** | **433,871,469,806,557,860** | **found 2026-08-18** |
| a(12), a(13) | open, no bound published | the hunt continues |

Both were found in the campaign's first minutes, both were verified four
ways (below), and the sweep that produced them is contiguous from k = 10⁴,
which is what makes them *least* values rather than merely examples.
Prior published lower bounds — a(10) > 1.54665×10¹³ and
a(11) > 1.076691×10¹⁴ — are consistent with both: the finds sit 600× and
4,000× above them.

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

### What the two finds say about the model

Both landed late — quantiles 0.915 and 0.923, E = 2.47 and 2.57 where the
median wait is ln 2 ≈ 0.69. Pooling the two as Exp(1) draws gives a
maximum-likelihood optimism factor of **2.5×** with a 95% interval of
about **[0.9, 20.8]**. That interval contains 1, so this is not evidence
that the singular series is wrong; two events cannot resolve a bias of
that size, and saying so is the result. It is worth watching at a(12):
the same model put a(12)'s median at 1.83×10¹⁹, and the sweep is already
past it.

The validation table below (six known terms, E scattering around 1) was
computed before the run and is unchanged by these two.

## Verification

Every claim above survived the project's four-way protocol, and both were
**re-verified from their evidence files** before publication:

| leg | a(10) | a(11) |
|-----|-------|-------|
| engine SPRP chain + sympy BPSW agree on the run length | ok | ok |
| alternate-alignment re-sieve (coarser wheel, numpy `%`, not the GPU's Barrett path) | ok | ok |
| BLS75 primality certificates, re-checked from scratch | 10/10 | 11/11 |
| factor witness for the run breaker | 1,425,733 | 13 |
| sympy `isprime` on every value, independently | 10/10 | 11/11 |

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
4.34×10¹⁷. "These values are prime" rests on certificates rather than
probable-prime tests, because m·k²+1 outgrows deterministic Miller–Rabin
before a(9).

Non-multiples of 2310 need no sweeping and are not a gap: the wheel is
forced by the argument in the README, and G1 checks it against every
published term rather than trusting it. The oracle owns [1, 10⁴), where
the wheel argument has an exception zone, and sweeps it exhaustively at
every campaign start.

The sweep's contiguity is a property of the machinery, not a promise: the
cursor advances only past a *fully classified* segment, so an interrupt or
a crash redoes a segment rather than skipping one — which was exercised
for real, since the machine hard-hung mid-campaign (a host-pool defect,
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)) and the resume re-covered its
segment.

## Census

Values below the frontier are counted, not narrated (CONVENTIONS.md). At
k ≈ 1.4×10¹⁹ the campaign had met:

| run | 7 | 8 | 9 | 10 | 11 |
|-----|---|---|---|----|----| 
| count | 11,447 | 2,649 | 606 | 140 | 35 |

The 35 run-11 values are all ≥ a(11); each was verified three ways when
met and none is evidenced, because `evidence/` holds first occurrences
only. The counts fall by roughly the factor the model predicts per added
constraint, which is a weak but free consistency check on the sieve.

## In progress

The campaign is **running and hunting a(12)**, which the model puts at
median 1.83×10¹⁹ — a depth the sweep has already passed, making a(12) a
late draw too if the model is right. It runs indefinitely to the enforced
ceiling of its wheel (the last rung) unless stopped; `--stop-on-discovery`
and `--to` are the deliberate stops.

The one thing that would change the reading of the model is a(12): three
consecutive late draws would be worth taking seriously, where two are not.
