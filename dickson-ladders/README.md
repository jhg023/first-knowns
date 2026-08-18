# dickson-ladders

> **Authorship disclaimer:** None of the code in this project was written
> by me. Every line — engines, CUDA kernel, verification machinery, and
> this documentation — was authored by **Claude (Anthropic's AI)** at my
> direction.

The hunt for new terms of [OEIS A247965](https://oeis.org/A247965): the
least k such that **m·k² + 1 is prime for every m = 1, 2, …, n**. The
sequence is `nonn,hard,more`; its last computational advance was in
**October 2014**, and the four terms this project targets — a(10) through
a(13) — have never had an upper bound published for them.

**Results so far: a(10) = 9,328,409,578,841,430 and
a(11) = 433,871,469,806,557,860**, both found and verified 2026-08-18 —
the first computational advance on this sequence since October 2014, when
Hiroaki Yamanouchi computed a(9) = 3,332,396,388,090 and left
a(10) > 1.54665×10¹³. Each was verified four ways, including a
Brillhart–Lehmer–Selfridge primality certificate for every one of its
values, and each was re-verified from its evidence file before
publication. Details in [RESULTS.md](RESULTS.md).

**Status: ACTIVE** — the campaign is running and hunting **a(12)**, the
next open term, past the model's median for it. The engine is v2 (913x the
first gated engine on the production shape,
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)). The model put a(10) at median
1.68×10¹⁵ and a(11) at 7.18×10¹⁶; both landed late, at quantiles 0.915 and
0.923 — see the model scoring below and in RESULTS.md. It puts a(12) at
1.83×10¹⁹ and a(13) at 2.14×10²¹. Predictions are stated in full below and
were fixed *before* the run, which is the only time they are worth
anything. Hunts are started deliberately by the repository owner, never by
an agent.

## The problem

Michel Lagneau proposed the sequence in September 2014; Derek Orr and
Michel Marcus filled in the small terms within days, and Hiroaki
Yamanouchi computed a(7)–a(9) and the two lower bounds on October 1,
2014. Nothing computational has happened to it since — the only edits in
the eleven years after are editorial.

| n | a(n) |
|---|------|
| 1 | 1 |
| 2 | 1 |
| 3 | 6 |
| 4 | 3,240 |
| 5 | 113,730 |
| 6 | 30,473,520 |
| 7 | 3,776,600,100 |
| 8 | 16,341,921,960 |
| 9 | 3,332,396,388,090 |
| 10 | **> 15,466,500,000,000** (open) |
| 11 | **> 107,669,100,000,000** (open) |
| 12, 13 | **open, no bound published** |

Why it is open rather than solved: a k that works for n must make n
distinct quadratic forms simultaneously prime, and even the n = 1 case —
are there infinitely many primes of the form k²+1? — is Landau's fourth
problem, open since 1912. Nobody can prove a(10) exists. Dickson's
conjecture says it does, Bateman–Horn says roughly where, and the only
way to find it is to sweep. That is the same bargain as the sibling
project in this repository: **a find confirms the conjecture, never
refutes it**, and every window swept could contain it.

The published bounds are *lower* bounds — searched-and-empty ranges, not
ceilings. There is no depth at which the hunt is guaranteed to end.

## The mathematics of the engine

**1. The wheel is forced, and it is enormous.** For a prime q ≤ n+1 and
a k not divisible by q, the residue u = −k⁻² mod q is one of
1, …, q−1 ⊆ {1, …, n}, so the value u·k²+1 is divisible by q — composite
as soon as it exceeds q. Every candidate is therefore a multiple of

  W(n) = product of the primes q ≤ n+1  (2310 at n = 10, 30030 at n = 12)

and the search line is 1/2310 as long as it looks. Every published term
above the floor sits on its wheel; **G1** checks that rather than
assuming it. (The exception zone is real: a(1) = a(2) = 1 works because
1·1+1 *is* the prime 2. The engines refuse to run below k = 10⁴ and the
oracle owns everything under it.)

**2. Representation: (W, j), never k.** A candidate is the pair (W, j)
with k = W·j. The value k passes 2⁶⁴ around a(12) and the *values*
m·k²+1 pass it before a(8) — but no engine ever forms either. Every
sieve test needs only

  k mod q = ((W mod q) · (j mod q)) mod q

and j stays inside u64 to the enforced ceiling (4×10¹⁸, i.e. k up to
9.2×10²¹ on the 2310 wheel). One engine spans the whole range; there is
no second engine waiting at the machine-word boundary, which is
[OPTIMIZATION.md](../OPTIMIZATION.md) §2.7 applied at the start of a
project instead of after it hurts.

**3. The sieve.** For a prime q > n+1 the killed residues of k are the
roots of k² ≡ −1/m (mod q) over m = 1..n: two roots for each m with
(−m|q) = +1, disjoint across m, so exactly 2·#{m ≤ n : (−m|q) = +1} of
them. The two engines exploit that fact in deliberately different ways —

- the **CPU engine** (`ladder_search.py`) builds the root table with
  sympy's `sqrt_mod`, converts it to j-residues, and marks arithmetic
  progressions with numpy slice strides;
- the **GPU engine** (`ladder_gpu.py`) never takes a square root. It
  derives every kill decision on the device from the residue *walk* —
  t = k² mod q by Barrett reduction, then r ← r + t from r = t+1, n
  times, killing on r = 0, which is m·k²+1 mod q for m = 1..n with no
  multiplication — evaluated once per (prime, residue) into a bit table
  that the sieve then consumes: the first 16-23 primes as 64-bit kill
  patterns OR-ed once per 64 candidates (stage 1a), the rest as one
  Barrett plus one bit probe per surviving candidate in compaction
  rounds (stage 1b). The v1 kernel, which walked every candidate against
  every prime, is kept in the file as the parity reference for **G15**
  and is unreachable from the campaign.

They share no subroutine — square roots and numpy strides on one side,
the walk, Barrett arithmetic and bit patterns on the other — so **G6**
(bit-for-bit parity on populated windows from j = 10⁶ up to the enforced
ceiling) and **G14** (the GPU stream against big-integer divisibility of
the actual values, no engine on the other side) are real checks rather
than tautologies.

**4. Host classification, designed cheap on day one and pipelined on
day two.** Survivors are classified by run length with a
strong-probable-prime chain that tests m = 1 first and stops at the first
composite; 61% of survivors die on the first test. The sibling project
learned the hard way that a fast kernel turns the host into the
bottleneck (its host share went from 2% to 52% while nobody was
watching), so this one measured the split from the first commit, and
when the v2 kernel made the host 92% of the wall the launcher grew a
process pool that classifies segment i−1 while the device sieves segment
i, consuming results in ascending order so the least-claim ordering is
untouched. At the n = 13 filter the host is 18% of device time and fully
hidden; at n = 10 it binds at 2.2x, on legs that take seconds — see
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

**4a. A discovery is a first occurrence, logged once; the census is
counted, not narrated.** The launcher's frontier promotes itself the
moment a longer run is verified (and is stored in the checkpoint, saved
at the end of that segment): the first k with run ≥ 10 is a(10), a
`[DISCOVERY]`, and the only thing that is evidenced. After that, a run-10
value is one short of a(11) and gets a single `[NEAR]` line with its
ordinal (verified 3-way — own chain, sympy, alternate-alignment re-sieve —
but not evidenced), and every run-7/8/9 value is **counted only**: it
appears in the census counts of the 30-second `[STATUS]` heartbeat
(`census 7:280 8:71 9:28 10:8`) and nowhere else. The moment a(11) lands,
run-10 values drop into that count too. A run of 12 settles a(11) and
a(12) at once, each logged once. `evidence/` holds first occurrences only.
Repo-wide convention: [CONVENTIONS.md](../CONVENTIONS.md).

**5. Certificates, because this problem hands them over.** The values
m·k²+1 pass huntlib's deterministic Miller–Rabin bound (3.317×10²⁴)
*before a(9)*, so probable-prime tests are evidence and not proof. But
N − 1 = m·k² is our own number: factor m and k and the factorization is
complete, which is exactly what Brillhart–Lehmer–Selfridge Theorem 1
needs. Every claimed find therefore carries a **primality certificate**
for all n of its values — a per-factor witness set, re-verified from
scratch by the evidence checker — instead of a probable-prime assertion.

The other half of a least-claim never needed certificates: a candidate is
rejected because a small prime divides one of its values (a proof) or
because a strong test fails (also a proof). So "this is the least k"
rests on rigorous ground for the whole swept range, and "these n values
are prime" rests on certificates. **G11** drills the verifier with a
forged witness and a falsified factorization; both must be rejected.

The witness search takes its bases from the primes in ascending order, as
many as it takes, not from a fixed short list — and the reason is
structural, not paranoia. For every prime q dividing k (and k is a wheel
multiple), N = m·k²+1 ≡ 1 (mod q), and reciprocity with (N−1)/2 even makes
q a quadratic residue mod N; 2 itself is a residue for every even m. So the
wheel primes can never witness p = 2, and a list of the first eleven primes
left only five or six coin flips per value: it ran out on a genuine run-10
census value at m = 2 (every prime below 41 a residue) and aborted a
campaign with a false alarm. **G12** replays that value: the eleven-prime
list must fail and the open-ended search must certify it.

## The odds model

`ladder_model.py` computes the Bateman–Horn prediction with a
numerically evaluated singular series (primes to 2×10⁶, tail bounded),
using two closed forms for the killed-residue count w_q that **Z4** pins
against the oracle's direct divisibility count at every prime below 400.

Validation, on the six known terms it did not help find — their expected
counts at the true a(n) should scatter around 1, and do:

| a(4) | a(5) | a(6) | a(7) | a(8) | a(9) |
|------|------|------|------|------|------|
| E = 1.07 | 1.01 | 1.05 | 2.15 | 0.39 | 0.69 |

**Predictions, stated before the run** (first occurrence, so
P(a(n) > K) = e^(−E); conditional on the published searched-empty range
where one exists):

| term | Q1 | **median** | Q3 | P90 |
|------|----|-----------|----|-----|
| a(10) | 5.22×10¹⁴ | **1.68×10¹⁵** | 4.33×10¹⁵ | 8.67×10¹⁵ |
| a(11) | 2.12×10¹⁶ | **7.18×10¹⁶** | 1.88×10¹⁷ | 3.78×10¹⁷ |
| a(12) | 5.33×10¹⁸ | **1.83×10¹⁹** | 4.75×10¹⁹ | 9.51×10¹⁹ |
| a(13) | 6.34×10²⁰ | **2.14×10²¹** | 5.50×10²¹ | 1.09×10²² |

At the v2 rate (1.63×10¹⁷ k/s on the production n = 13 shape; the
end-to-end n = 10 rate is host-bound at 2.45×10¹⁵ k/s — see
[BENCHMARKS.md](BENCHMARKS.md)) that is **under a second to the a(10)
median, half a minute to a(11), minutes to a(12), and 3.6 hours to
a(13)** (P90 19 hours). At the v1 rate a(13) was months to years; the
ledger of how that gap closed, with every reject and its price, is
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

**How the finds scored** (out of sample, against the table above):

| term | found at | model median | E at the find | quantile |
|------|----------|--------------|---------------|----------|
| a(10) | 9.33×10¹⁵ | 1.68×10¹⁵ | 2.47 | 0.915 |
| a(11) | 4.34×10¹⁷ | 7.18×10¹⁶ | 2.57 | 0.923 |

Both are late draws — 5.5× and 6.0× past their medians, where the median
wait is E = ln 2 ≈ 0.69. Pooling them as Exp(1) draws gives a
maximum-likelihood optimism factor of 2.5× with a 95% interval of roughly
[0.9, 20.8]; that contains 1, so it is not evidence the singular series is
wrong, and two events cannot resolve a bias of that size. a(12) is the one
that would make it interesting: three late draws in a row would be worth
taking seriously.

## Running it

```
python launch.py --selftest    # full gate battery + drills
python launch.py               # THE HUNT: resumes at the frontier and
                               # runs INDEFINITELY -- to the enforced
                               # ceiling of its wheel, the last rung
python launch.py --status      # scoreboard
python score.py                # gates x fingerprinted benchmarks
python ladder_model.py         # rebuild the odds model + its gates
```

The campaign never stops on its own before the last rung. Progress is
read off **rungs** — the model's Q1/median/Q3/P90 for every open term
(16 of them, from `model_results.json`) plus the ceiling — logged
`[RUNG]` as each is passed and shown with an ETA in every `[STATUS]`.
`--to K` caps a run deliberately and `--stop-on-discovery` halts after a
first occurrence; both are opt-in. The **filter follows the frontier**:
with the default `--filter-lag 1` the sieve runs at n = frontier, so once
a(10) lands it hunts a(11) while still seeing run-10 values (one short of
a(11): each gets a `[NEAR]` line) and counting shorter runs in `[STATUS]`,
steps to n = 11 when a(11) lands, and so on; when a step widens the wheel
(11 → 12 takes 2310 → 30030) the cursor is re-denominated by floor — an
overlap of under one period, never a gap — and logged as a `[STAGE]`
line. `--filter-lag 0` is the fastest hunt (n = frontier + 1, nothing
below the next open term is seen).

Every 30 s of wall clock (`--heartbeat`) the launcher logs a `[STATUS]`
line from its own timer thread — whatever the main loop is doing: position,
end-to-end rate, survivors, **the census counts per run length from 7 to
the frontier** (`census 7:280 8:71 9:28 10:8` — how many run-7s, run-8s, …
the campaign has met; the only place those values appear), finds, live
model odds, the next rung and its ETA — and, if no segment has closed since
the previous line, what it is busy with and for how long, so a stall never
looks like a hang. `--status` prints the same counts from the checkpoint.

The launcher preludes every fresh campaign with an exhaustive oracle
sweep of [1, 10⁴) — which must return a(1)–a(4) and nothing else — and
then makes the production engine **rediscover a(7), a(8) and a(9)
end-to-end as first occurrences**, sweeping from the floor. A stream that
cannot find what is known does not get to report what is not.

`--stop-on-discovery` follows the repo-wide convention: only a first
occurrence beyond the campaign frontier (≥ 10 at start; the frontier
promotes itself as finds land and the promotion lives in the checkpoint)
halts the hunt, and only when the flag is given. Further k with a settled
run length are census — counted, one `[NEAR]` line if one short of the
next open term, never evidenced — rather than stopping a leg or being
logged as a second discovery. Terms found in earlier campaigns can also
be seeded into `CAMPAIGN_FOUND` in the launcher.

`--workers N` sets the classification pool (default **8**, or fewer on a
small machine; `1` is the serial path). The default used to be *core count
minus four* — 60 processes on a 64-thread machine — and the spawn burst (60
interpreters importing numpy and sympy at once, while the device is flat
out) hard-hung the development machine ~30 s into every campaign start,
fans running and the display link dead. **A hunt runs for days on
somebody's desktop: it does not get to take the whole machine.** Eight is
the known-stable setting, not the fast one.

It is deliberately conservative, and the price is measured. On a live
campaign at n = 11, k ≈ 9.5×10¹⁸: the sweep classifies ~70,000 survivors/s
at ~105 µs each, so the pool carries **~7.4 cores**; eight workers run at
~92% duty while the **device sits idle 60% of the time** (utilization
alternates 98%/12%, mean 41%). Per 10¹⁶-k segment that is ~4.0 s of pool
against ~1.8 s of device — **host-bound by 2.3×**. The knee is around
**18 workers**, where the device becomes the binding side again and
throughput would rise ~2.5× to ~6×10¹⁵ k/s.

So raising `--workers` toward that knee is real throughput, and the spawn
burst scales with the number — 16 is a quarter of what hung the machine.
Raise it a few at a time and watch, rather than returning to a number that
fills the machine. Per-survivor cost also grows with depth (more digits per
Miller–Rabin test), and a shallow re-run is hungrier still: at the n = 10
filter the host needs ~19 cores. Segments are 2⁴² candidates;
`--seg-span` in k overrides.

Requires Python 3.12+, numpy, sympy, CuPy + CUDA GPU (or `--engine cpu`,
which is the gating reference and orders of magnitude too slow to hunt
with).

## Trust

This project follows the repository-wide
[CONVENTIONS](../CONVENTIONS.md): three independent implementations
(oracle / CPU / GPU) with bit-parity gates on populated windows up to the
enforced ceiling, canary rediscoveries that must fire before production
runs, planted-fake drills in both directions, and a discovery protocol
whose every claim is checkable from the evidence file alone.

Project-specific: because the values outgrow deterministic Miller–Rabin
early, this hunt's evidence carries **primality certificates** rather
than probable-prime claims, and the certificate verifier is itself
drilled with forgeries (**G11**). See `evidence/` for the artifacts.
