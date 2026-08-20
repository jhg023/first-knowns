# primorial-ap

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A053647](https://oeis.org/A053647): the
first term of the first arithmetic progression of **n primes whose common
difference is the n-th primorial** — the smallest difference an n-term
progression of primes can possibly have. The sequence is
`nonn,nice,hard,more`; its last computational advance was **October 2009**,
and no open term has ever had an upper bound published for it.

**Results so far: none.** The engine is built, the gate battery is green
and the odds model is validated and stated below, but **no production sweep
has been run** — only bounded smoke runs to 8×10¹¹, far below where any
open term is expected. Hunts in this repository are started deliberately by
the repository owner, never by an agent. The first target is **a(16)**,
which the model puts at a median of 3.87×10¹³ — about 1.8 hours of sweep at
the measured end-to-end rate.

**Status: ACTIVE** — this is the project currently being advanced. Prior
frontier: **a(15) = 158,317,270,283**, Donovan Johnson, October 20, 2009.

## The problem

G. L. Honaker, Jr. proposed the sequence in February 2000; Jud McCranie
filled in a(11)–a(13) within ten days, and Donovan Johnson computed
a(14) and a(15) in October 2009. Nothing computational has happened to it
since — the edits in the seventeen years after are link and format changes.

A053647(n) is the least prime *p* such that

&nbsp;&nbsp;&nbsp;&nbsp;*p*, *p* + P(n), *p* + 2·P(n), …, *p* + (n−1)·P(n)

are **all prime**, where P(n) = [A002110](https://oeis.org/A002110)(n) is
the product of the first n primes. The difference is not a free parameter:
any arithmetic progression of n primes must have a common difference
divisible by every prime up to n, so P(n) is the **minimum admissible
difference**, and this sequence asks for the first progression that
achieves it.

| n | a(n) | | n | a(n) |
|---|------|---|---|------|
| 1 | 2 | | 9 | 272,809 |
| 2 | 5 | | 10 | 640,943 |
| 3 | 7 | | 11 | 5,378,959 |
| 4 | 13 | | 12 | 116,137,159 |
| 5 | 37 | | 13 | 3,708,797,237 |
| 6 | 73 | | 14 | 114,649,314,209 |
| 7 | 7,937 | | 15 | 158,317,270,283 |
| 8 | 7,703 | | | |

**The sequence is not monotone** — a(7) = 7937 is larger than a(8) = 7703 —
and that is not a curiosity, it is the shape of the whole problem. The
difference P(n) changes with n, so a candidate for one term says nothing
about any other: no term bounds any other, there is no ladder to climb, and
the campaign re-sieves from the floor for every term it hunts.

**Why it is open, and why a find confirms rather than refutes.** The tuple
{0, P(n), …, (n−1)P(n)} is *admissible*: for a prime q ≤ prime(n) every
member is congruent to p mod q, excluding one residue class and no more;
for q > prime(n) the n members are distinct mod q and q > n leaves a class
free. Nothing obstructs the progression at any prime, so Dickson's
conjecture — and the Hardy–Littlewood k-tuple conjecture with it —
predicts **infinitely many** p for every n. A new term is a confirmation.
The only bound ever published on this sequence, Jud McCranie's
"a(14) > 2³² and a(15) > 2³²", was superseded by the values themselves in
2009; **every open term is open from the floor up.**

## The mathematics of the engine

**The sieve.** For any prime q the killed residues of p are exactly

&nbsp;&nbsp;&nbsp;&nbsp;F(q, n) = { (−j·P(n)) mod q : j = 0 … n−1 }

and that single formula covers both cases without a branch: when q divides
P(n) — that is, q ≤ prime(n) — every j gives 0, so F = {0} and the
condition is just that q does not divide p; when q does not divide P(n) the
n values are distinct and q kills n of its q residue classes. At n = 16
that is 16 residues killed by every prime from 59 up, which is a ferocious
sieve: after depth 2048 only about 4.5 candidates in a million survive, and
after depth 65536 about one in ninety million.

**The wheel.** a(n) is itself prime and larger than prime(n) for every
n ≥ 5, so it is coprime to P(n) and in particular to 2, 3 and 5. Both
engines therefore walk a mod-30 wheel of eight residues. Below
max(10⁴, sieve depth) the argument has an exception zone — a value can *be*
the small prime that would otherwise kill it — so the engines refuse to run
there and the launcher's low pass covers [2, floor) with the oracle
instead, which keeps the least-claim contiguous from 2.

**Representation.** Candidates are the pair `(base, offset)` with
p = base + offset, base a Python integer and offset a u64. One engine spans
the whole range with no seam at 2⁶⁴ — which matters here, because p passes
it around a(21) and the *values* p + j·P(n) pass it at a(16).

**Three implementations, sharing nothing but the answer.** The oracle
(`ap_reference.py`, sympy only) computes killed residues by direct
divisibility over every residue class. The CPU engine (`ap_search.py`,
numpy) computes them as `(-j * P(n)) % q` in Python integers and sieves a
flat array with one entry per integer, masking the wheel afterwards. The
GPU engine (`ap_gpu.py`, CuPy) never multiplies by P(n) at all: it *walks*
the residues, starting at 0 and subtracting P(n) mod q with a conditional
add-back, in u32 registers, with Barrett magic-multiply throughout — and it
sieves a bitmap indexed by (wheel period, lane), in which an integer
divisible by 2, 3 or 5 has no representation at all. The parity gates
compare streams that were produced by three different constructions.

**Why the marking work is chunked.** The kill count for a prime is
proportional to 1/q, so the smallest sieve prime does thousands of times
the work of the largest; one thread per (prime, residue, lane) would leave
the whole segment waiting on the q = 7 thread. A prime is therefore split
into contiguous ranges of the wheel-period axis, sized so every task marks
about the same number of bits. The split changes *which thread marks a
bit*, never *which bits are marked*, and gate G13 drills exactly that by
re-sieving one window with a 64× different task count and requiring an
identical stream.

## The odds model

A Bateman–Horn estimate with a numerically computed singular series
(`ap_model.py`). Two features of this problem drive it: the singular series
is **enormous** — every prime q ≤ prime(n) contributes (1−1/q)^(1−n), so at
n = 16 the primes up to 53 alone multiply the density by about 5×10⁹, which
is why these terms are findable at all — and the log factors are **not all
log p**, because P(n) dwarfs every p this hunt will reach, so for j ≥ 1 the
value is essentially j·P(n) and its log barely moves as p sweeps.

**Validation, on the nine known terms the model did not help find.**
E(n, a(n)) should be an Exp(1) draw for each, so the values must *scatter*:

| n | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|----|----|----|----|----|----|
| E at a(n) | 2.53 | 0.35 | 1.03 | 0.22 | 0.14 | 0.20 | 0.39 | 0.70 | 0.06 |

They range 0.06 to 2.53 and sum to **5.64 against 9 expected** — honest
scatter with a mild *early* lean (p ≈ 0.12 under Gamma(9), so not
significant). Recorded rather than smoothed away, and noted here because it
is the opposite skew from the sibling project in this repo, whose model ran
about 2× optimistic.

**Predictions, stated before the run.** Depths on the p-line; each term is
its own sweep from the floor.

| term | Q1 | median | Q3 | P90 | median at the measured rate |
|------|----|--------|----|-----|------------------------------|
| a(16) | 1.56×10¹³ | **3.87×10¹³** | 7.93×10¹³ | 1.34×10¹⁴ | 1.8 h |
| a(17) | 3.29×10¹⁴ | **8.15×10¹⁴** | 1.67×10¹⁵ | 2.81×10¹⁵ | 1.6 d |
| a(18) | 7.16×10¹⁵ | **1.77×10¹⁶** | 3.61×10¹⁶ | 6.08×10¹⁶ | 34 d |
| a(19) | 1.67×10¹⁷ | **4.12×10¹⁷** | 8.40×10¹⁷ | 1.41×10¹⁸ | 2.2 y |
| a(20) | 4.10×10¹⁸ | **1.01×10¹⁹** | 2.05×10¹⁹ | 3.45×10¹⁹ | 54 y |

**What that means for what this project can expect to find.** The measured
v1 rates are **8.46×10⁹ p/s** of device sieve and **5.97×10⁹ p/s**
end-to-end (the campaign currently sieves a segment and then classifies it,
rather than overlapping the two — a measured 30% left on the table, and the
first entry on the optimization list). The table above uses the end-to-end
number. So a(16) is an afternoon, a(17) is a weekend, and a(18) is about
five weeks at the median — eleven weeks at P90. **a(19) is out of reach
without a faster engine.**

The engine is a v1 and there is real headroom: the marking kernel draws
210 W of a 450 W budget and reaches about 2.4×10¹⁰ marks per second, which
is far short of what the memory system can do, and the overlap above is a
separate 30%. But headroom is not a result. The honest statement is that
**this project is built to find three new terms**, and that a fourth
depends on optimization work that has not been done —
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) says what the candidates are and
what each is expected to be worth.

**Verification changes character at a(19), too.** The largest value is
about (n−1)·P(n): 4.9×10²⁰ at a(16), 3.1×10²² at a(17), 2.0×10²⁴ at
a(18) — all below huntlib's deterministic Miller–Rabin bound of
3.317×10²⁴, so for the first three terms the engine's own chain is a
*proof*. At a(19) the values reach 1.4×10²⁶ and the bound is gone; from
there every value carries a BLS75 certificate, and since N−1 = p−1+j·P(n)
has no structure to exploit, that means a bounded partial factorization and
Theorem 5's cube-root threshold rather than Theorem 1's square root. Gate
`g10` pins the crossing so no future edit can assume determinism it does
not have.

## Running it

```
python launch.py --selftest    # full gate battery -- must print ALL GREEN
python launch.py               # the hunt (checkpointed, resumable, indefinite)
python score.py                # correctness gates x fingerprinted benchmark
python ap_model.py             # re-derive the odds model and its validation
```

Requirements: Python 3.12+, numpy, sympy, and CuPy with a CUDA GPU. The
CPU fallback is `--engine cpu`.

The campaign runs **indefinitely** by default and stops on its own only at
the enforced ceiling of 10²⁶. `--to` and `--stop-on-discovery` are the two
deliberate stops and both are opt-in. Progress is read off *rungs* — the
model quartiles above, logged `[RUNG]` as they are passed and shown with an
ETA in every 30-second `[STATUS]` line, which also carries the census
counts per chain depth. When a term lands, the launcher retires that term's
rungs, resets the cursor to the floor and builds a completely new sieve for
the next open term, logging a `[STAGE]` line that says so.

Throttles, priced: `--workers` (2 by default, sized from a measured 0.64
cores of demand), `--gpu-yield-ms` (about 1% of the rate per 15 ms), and
`--gentle` (one worker and a 15 ms yield: about 2% of the rate for a
machine that stays comfortable). `--sieve-depth 1024` is 14% faster and
asks for five times the host; the measured table is in `launch.py`.

**Every program here stops cleanly on Ctrl+C**: the launcher checkpoints at
the last fully classified segment, logs one `[STAGE]` line and exits 130,
with no traceback even if a second Ctrl+C arrives during the save.

## Trust

The gate discipline, the discovery protocol, the census convention and the
load budget are repository-wide and documented in
[CONVENTIONS.md](../CONVENTIONS.md). What is specific to this project:

- **The oracle is sympy-only** and holds the frozen table of published
  terms; G1 checks every one against the definition, G2 re-derives a(1)–
  a(10) exhaustively one integer at a time with no wheel, and G2b checks
  the closed-form residue set against direct divisibility.
- **The two fast engines are pinned bit-for-bit** on populated windows at
  p ≈ 10⁶, 10⁹, 4×10¹³ and at the enforced ceiling of 10²⁶ (G6), and the
  comparator is itself drilled with a corrupted, a dropped and an added
  survivor (G7). G14 checks kill decisions against big-integer divisibility
  of the actual values with no engine on the other side.
- **A canary rediscovery runs before every campaign**: the production
  stream must re-derive a(13) = 3,708,797,237 from the floor, over
  3.7×10⁹ of contiguous p-line, as the *smallest* p it accepts.
- **Every claimed find is verified four ways** before it is recorded: the
  engine's own chain, sympy's independent BPSW chain over the values in
  Python integers, a from-scratch re-derivation at a sieve depth the
  campaign is not running, and a primality proof for every one of the n
  values. Any disagreement halts the campaign.
- **The evidence directory holds first occurrences only.** A chain one
  value short of the term being hunted gets one `[NEAR]` line and no file;
  everything from depth 6 up is counted in the checkpoint and appears only
  in the `[STATUS]` census.
