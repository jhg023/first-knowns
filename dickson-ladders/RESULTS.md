# RESULTS — dickson-ladders

Verified finds live here in discovery order, each with its exact
integers, its verification record, its factor witness for the
run-breaking composite, and — specific to this project — a primality
certificate for every value claimed prime. Evidence JSONs in
`evidence/`.

## Standing state

**No new term has been found yet: the campaign has been built and gated,
not run.** The frontier is exactly where the literature left it:

| n | value | source |
|---|-------|--------|
| a(9) | 3,332,396,388,090 | Hiroaki Yamanouchi, Oct 2014 |
| a(10) | > 15,466,500,000,000 | Hiroaki Yamanouchi, Oct 2014 |
| a(11) | > 107,669,100,000,000 | Hiroaki Yamanouchi, Oct 2014 |
| a(12), a(13) | no bound published | — |

This section will be replaced by the first find. Until then the only
honest claim this project makes is the one below.

## What has been verified so far

Rediscoveries, not discoveries — but they are the reason the discoveries
will be believable, and they are checkable today:

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
  factorization (G11).

## The least-claim, and what it will rest on

When a find is reported, the claim "a(10) = k" will mean: every multiple
of W(10) = 2310 from 10⁴ to k was classified, every k below it failed,
and the failures are *proofs* — a small prime dividing one of the ten
values, or a failed strong Fermat test. The claim "these ten values are
prime" will rest on certificates, not probable-prime tests, because
m·k²+1 outgrows deterministic Miller–Rabin before a(9).

Non-multiples of 2310 need no sweeping and are not a gap: the wheel is
forced by the argument in the README, and G1 checks it against every
published term rather than trusting it.

## In progress

Nothing is running. The first leg, when the owner starts it, sweeps the
n = 10 filter from k = 10⁴ to 2×10¹⁷ (`--to` overrides), which covers
a(10) with ~99% model probability and a(11) past its Q3, and halts on the
first frontier-extending find.
