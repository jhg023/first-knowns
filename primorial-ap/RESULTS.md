# RESULTS — primorial-ap

> **Authorship disclaimer:** None of this was written by me; it was
> authored by **Claude (Anthropic's AI)** at my direction.

Verified finds for [A053647](https://oeis.org/A053647), in discovery order:
the exact integers, the verification performed, the evidence file, and the
basis of the least-claim.

## Standing state (2026-08-21)

**Three new terms found and verified**, the first computational advance on
A053647 since October 2009 — a 17-year-old frontier:

| n | value | status |
|---|-------|--------|
| a(15) | 158,317,270,283 | Donovan Johnson, Oct 2009 |
| **a(16)** | **116,781,362,669,989** | **found 2026-08-20** |
| **a(17)** | **2,097,209,048,106,247** | **found 2026-08-20** |
| **a(18)** | **14,042,451,608,819,603** | **found 2026-08-21** |
| a(19) | open, no bound published | campaign paused, resumable |

All three were verified four ways (below), each was re-verified from its
evidence file before publication — independently, from the definition, with
sympy alone — and each sweep is contiguous from p = 2, which is what makes
these *least* values rather than merely examples. **No upper or lower bound
had ever been published for any of them**; the sequence's only bound,
Jud McCranie's "a(14) > 2³² and a(15) > 2³²", was superseded in 2009.

Because every value here is below huntlib's deterministic Miller–Rabin
bound of 3.317×10²⁴, the primality of all 51 values is **proved**, not
asserted probabilistically (gate `g10` pins the crossing; a(19) is where it
goes away).

These are **candidates for OEIS in the repository owner's hands, not
submissions**: the pipeline records, humans decide (CLAUDE.md rule 5).

## A053647(16) = 116,781,362,669,989

Found 2026-08-20, **21 minutes** into the campaign, at p ≈ 1.168×10¹⁴.

- P(16) = 32,589,158,477,190,044,730, and p + j·P(16) is prime for every
  j = 0…15 — sixteen simultaneous primes, the largest
  488,837,493,939,213,340,939 (21 digits).
- The chain breaks at j = 16: 521,426,652,416,403,385,669 =
  **79,817** × 6,532,776,882,323,357, so the chain is exactly 16.
- Least-claim basis: every mod-30 wheel candidate from p = 10⁴ to
  1.1693×10¹⁴ was sieved and every survivor classified, each rejection a
  small prime dividing one of the values or a failed strong test;
  [2, 10⁴) was covered by the oracle's low pass.
- Model quantile of the find: **0.867** (E = 2.02; median predicted
  3.87×10¹³, so it landed 3.0× past it).
- Evidence: `evidence/ap_a16_p116781362669989.json`

## A053647(17) = 2,097,209,048,106,247

Found 2026-08-20, 3.1 hours after a(16), at p ≈ 2.097×10¹⁵.

- P(17) = 1,922,760,350,154,212,639,070, and p + j·P(17) is prime for every
  j = 0…16 — seventeen simultaneous primes, the largest
  30,764,167,699,676,450,331,367 (23 digits).
- **The chain does not stop at 17 — it runs 19 deep.** j = 17 and j = 18
  give 32,686,928,049,830,662,970,437 and 34,609,688,399,984,875,609,507,
  both prime, so this p is simultaneously a **19-term arithmetic
  progression of primes** with common difference P(17). That is admissible
  because 19 is itself among the first 17 primes, so P(17) is divisible by
  it; it is a bonus, not another term — a(18) and a(19) require the
  *different* differences P(18) and P(19), and neither is bounded by this.
- The chain breaks at j = 19: 36,532,448,750,139,088,248,577 = **71** ×
  514,541,531,692,099,834,487.
- Least-claim basis: the same contiguous sweep, from the floor to
  2.0974×10¹⁵, unbroken.
- Model quantile of the find: **0.823** (E = 1.73; median predicted
  8.15×10¹⁴, so it landed 2.6× past it).
- Evidence: `evidence/ap_a17_p2097209048106247.json`

**This find broke the verifier, and the fix is a gate now.** The classifier
walks the chain with a cap at n, so a report of "17" means *at least* 17;
the verification legs re-walked to 18, found the chain still running, and
read the disagreement as a corrupt engine. The campaign halted on a
correct find. The verifier now walks a **bounded** distance past a full
claim (`VERIFY_OVERSHOOT = 8`) so that the true depth and the real breaker
land in the evidence, and it holds the two directions apart: a chain
*longer* than a full claim is the term, while a claim that re-measures
longer than a chain which had already stopped at a composite is still the
alarm it should be. Drilled by `_drill_verification` against a(9) = 272,809,
whose chain has run 10 deep since 2000 — the case was always there to be
found in the published terms.

## A053647(18) = 14,042,451,608,819,603

Found 2026-08-21, 19.9 hours after a(17), at p ≈ 1.404×10¹⁶ — 120× above
a(17) and the deepest sweep of the campaign.

- P(18) = 117,288,381,359,406,970,983,270, and p + j·P(18) is prime for
  every j = 0…17 — eighteen simultaneous primes, the largest
  1,993,902,497,152,370,115,535,193 (25 digits).
- The chain breaks at j = 18: 2,111,190,878,511,777,086,518,463 =
  **424,267** × 4,976,090,241,550,196,189, so the chain is exactly 18.
- Least-claim basis: the same contiguous sweep, from the floor to
  1.40425×10¹⁶.
- Model quantile of the find: **0.425** (E = 0.55; median predicted
  1.77×10¹⁶, so it landed *early*, at 0.79× the median).
- Evidence: `evidence/ap_a18_p14042451608819603.json`

## How the model did

Each E below is the expected count of qualifying p up to the value that was
found, under the Bateman–Horn estimate fixed in `model_results.json` before
the first production sweep. Each should be an Exp(1) draw.

| term | predicted median | found at | ratio | E at the find | quantile |
|------|------------------|----------|-------|---------------|----------|
| a(16) | 3.87×10¹³ | 1.168×10¹⁴ | 3.02× | 2.02 | 0.867 |
| a(17) | 8.15×10¹⁴ | 2.097×10¹⁵ | 2.57× | 1.73 | 0.823 |
| a(18) | 1.77×10¹⁶ | 1.404×10¹⁶ | 0.79× | 0.55 | 0.425 |

Two late and one early, summing to **4.30 against 3 expected** — a
pooled factor of 1.43× (95% interval [0.60, 6.96], which includes 1). The
nine known terms leaned the other way, 5.64 against 9. Pooled over all
twelve: **9.94 against 12 expected, a factor of 0.83 with a 95% interval
of [0.51, 1.60]**. The interval covers 1 from both directions and after
three live finds the model is still not distinguishable from honest —
which is worth stating next to the sibling project in this repo, whose
equivalent interval **excludes** 1 at 2.26× optimistic.

The predictions were not re-fitted after any find, and `model_results.json`
is unchanged from the pre-run file.

## Prior state of the sequence

| term | value | who | when |
|------|-------|-----|------|
| a(1)–a(10) | 2 … 640,943 | G. L. Honaker, Jr. | Feb 2000 |
| a(11)–a(13) | 5,378,959 … 3,708,797,237 | Jud McCranie | Feb 28, 2000 |
| a(14) | 114,649,314,209 | Donovan Johnson | Oct 20, 2009 |
| a(15) | 158,317,270,283 | Donovan Johnson | Oct 20, 2009 |

**a(16) and beyond were open, with no published upper or lower bound.** The
only bound the entry ever carried — Jud McCranie's "a(14) > 2³² and
a(15) > 2³²" — was superseded by the values themselves in 2009 and is now
stale text in the comment field. Re-verified against oeis.org on
2026-08-21, revision #35 of the entry, which still ends at a(15).

## What each find had to survive

Every claimed first occurrence was confirmed four ways before it was
recorded, and any disagreement halts the campaign with exit 2:

1. **the engine's own chain** — huntlib's deterministic Miller–Rabin base
   set over the n values;
2. **sympy's independent BPSW chain**, computed from the definition in
   Python integers by the oracle;
3. **a from-scratch re-derivation by different machinery** — the GPU
   engine's residue-walk membership test, consulted one candidate at a time
   at a sieve depth the campaign is *not* running (2¹²), plus the oracle's
   direct divisibility over the actual values;
4. **a primality proof for every one of the n values**, from
   `huntlib.certificate`.

Leg 4 was free for all three finds and is real work after them. The largest
value is about (n−1)·P(n) — 4.9×10²⁰ at a(16), 3.1×10²² at a(17),
2.0×10²⁴ at a(18) — all below the deterministic Miller–Rabin bound of
3.317×10²⁴, so legs 1 and 2 are proofs and the certificate restates them;
all 51 values carry `deterministic-mr`. At a(19) the values reach 1.4×10²⁶:
from there each value needs a BLS75 certificate over a bounded partial
factorization of N−1, which has no structure to exploit
(N−1 = p−1+j·P(n)), so it will usually be Theorem 5's cube-root threshold
with a subproof when a large prime cofactor appears.

**The basis of the least-claim.** Each term is swept contiguously from the
floor: p = 2 up to max(10⁴, sieve depth) by the oracle in the launcher's
low pass, and everything above by the engine. Every p the sweep passes over
is rejected either by a small prime dividing one of its values — a factor
witness, checkable with one multiplication — or by a failed strong test,
which is a proof of compositeness. So "this is the least p" rests on
rigorous ground throughout, independently of the primality proofs for the
find itself. A canary rediscovery of a(13) = 3,708,797,237 from the floor
ran before the campaign was trusted.

**Re-verified before publication.** All three evidence files were re-checked
against the definition by a script that shares nothing with the engines —
sympy's `isprime` and a primorial recomputed from `primerange` — confirming
for each: the difference is P(n), all n values are prime, the recorded
`values[]` match the definition, the chain's true depth is what the file
says, and the recorded factor witness divides the breaking value.

## The census

The campaign classified **1,984,305,704 survivors** across its three
sweeps. The census — chain depths counted in the checkpoint and shown in
every 30-second `[STATUS]` line — is kept **per term**, because a chain of
depth 12 means something different under a different difference, and it is
cleared when the campaign moves to the next term. So what survives is the
**a(18) sweep's** census, over 1.404×10¹⁶ of p-line:

```
census 6:1137084 7:332357 8:97660 9:28451 10:8277 11:2391 12:701
       13:214 14:57 15:20 16:3 17:1
```

Each step is **0.29** of the last, and remarkably steady about it — the
first eight ratios run 0.289 to 0.305 before the counts get too small to
mean much. None of it is evidenced, and the top two entries are the reason
the rule exists: the three 16s and the single 17 are chains met *after*
a(16) and a(17) were settled and under a *different* difference, so they
are census repeats rather than rediscoveries — and the 17 is the
one-short `[NEAR]` of the a(18) hunt, which got one log line and no file.
Only first occurrences get files (CONVENTIONS.md).

## Where it stopped

**PAUSED 2026-08-21**, resumable. The campaign halted immediately after the
a(18) find, with the cursor at p = 1.40425×10¹⁶ under the a(18) sieve; the
checkpoint has a(18) settled but the stage advance not yet taken, so
`python launch.py` resumes by retiring a(18)'s rungs, resetting the cursor
to the floor and building a fresh sieve for **a(19)** — the launcher does
this itself and logs a `[STAGE]` line saying so.

a(19) is a genuinely bigger hunt: median 4.12×10¹⁷ on the p-line, **about
23 days** on one 4090 at the measured end-to-end rate, and the first term
whose values pass the deterministic Miller–Rabin bound, so every value will
need a BLS75 certificate. See [BENCHMARKS.md](BENCHMARKS.md) for what the
remaining terms cost.
