# RESULTS — primorial-ap

> **Authorship disclaimer:** None of this was written by me; it was
> authored by **Claude (Anthropic's AI)** at my direction.

Verified finds for [A053647](https://oeis.org/A053647), in discovery order:
the exact integers, the verification performed, the evidence file, and the
basis of the least-claim.

## Verified finds

**None yet.** No production sweep has been run. This section will carry one
entry per verified first occurrence, and the `evidence/` directory one JSON
each — first occurrences only, never census values (CONVENTIONS.md).

## Prior state of the sequence

| term | value | who | when |
|------|-------|-----|------|
| a(1)–a(10) | 2 … 640,943 | G. L. Honaker, Jr. | Feb 2000 |
| a(11)–a(13) | 5,378,959 … 3,708,797,237 | Jud McCranie | Feb 28, 2000 |
| a(14) | 114,649,314,209 | Donovan Johnson | Oct 20, 2009 |
| a(15) | 158,317,270,283 | Donovan Johnson | Oct 20, 2009 |

**a(16) and beyond are open, with no published upper or lower bound.** The
only bound the entry ever carried — Jud McCranie's "a(14) > 2³² and
a(15) > 2³²" — was superseded by the values themselves in 2009 and is now
stale text in the comment field. Re-verified against oeis.org on
2026-08-20, revision #35 of the entry.

## What a find will have to survive

Every claimed first occurrence is confirmed four ways before it is recorded,
and any disagreement halts the campaign with exit 2:

1. **the engine's own chain** — huntlib's deterministic Miller–Rabin base
   set over the n values;
2. **sympy's independent BPSW chain**, computed from the definition in
   Python integers by the oracle;
3. **a from-scratch re-derivation by different machinery** — the GPU
   engine's residue-walk membership test, consulted one candidate at a time
   at a sieve depth the campaign is *not* running (2¹³), plus the oracle's
   direct divisibility over the actual values;
4. **a primality proof for every one of the n values**, from
   `huntlib.certificate`.

Leg 4 is free for a(16)–a(18) and real work after that. The largest value
is about (n−1)·P(n) — 4.9×10²⁰ at a(16), 3.1×10²² at a(17), 2.0×10²⁴ at
a(18) — all below the deterministic Miller–Rabin bound of 3.317×10²⁴, so
there legs 1 and 2 are proofs and the certificate restates them. At a(19)
the values reach 1.4×10²⁶: from there each value needs a BLS75 certificate
over a bounded partial factorization of N−1, which has no structure to
exploit (N−1 = p−1+j·P(n)), so it will usually be Theorem 5's cube-root
threshold with a subproof when a large prime cofactor appears.

**The basis of the least-claim.** Each term is swept contiguously from the
floor: p = 2 up to max(10⁴, sieve depth) by the oracle in the launcher's
low pass, and everything above by the engine. Every p the sweep passes over
is rejected either by a small prime dividing one of its values — a factor
witness, checkable with one multiplication — or by a failed strong test,
which is a proof of compositeness. So "this is the least p" rests on
rigorous ground throughout, independently of the primality proofs for the
find itself.

## The census

Chains of depth 6 and above are counted per depth in the checkpoint and
shown in every 30-second `[STATUS]` line; a chain one value short of the
term being hunted gets one `[NEAR]` line and no file. Neither is evidenced.
The counts from bounded smoke runs are not results and are not recorded
here; the first production run's census will be, as counts.

For scale, measured at n = 16 and depth 4096 over 6.0×10⁹ of p-line: chains
of depth ≥ 6 occur about once per 5×10⁸ of line, ≥ 8 about once per
6×10⁹, and each further step is about 0.32 of the last. That is why the
census floor is 6 — frequent enough to be a useful health readout, far too
frequent to narrate.

## In progress

The campaign has not been started. When it is, it will hunt **a(16)** from
the floor at sieve depth 2048, and on finding it will retire a(16)'s rungs,
reset the cursor and build a fresh sieve for a(17) — logging a `[STAGE]`
line that says so. The model's predictions, fixed before the run, are in
[README.md](README.md); what each term costs at the measured rate is in
[BENCHMARKS.md](BENCHMARKS.md).
