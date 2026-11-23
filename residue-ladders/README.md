# residue-ladders

> **Authorship disclaimer:** None of this code was written by me — it was
> entirely authored by **Claude (Anthropic's AI)** at my direction.

A GPU hunt for new terms of five sibling entries, the power-residue
ladders: [A002226](https://oeis.org/A002226), "Smallest prime p such that
first n primes (p_1=2, ..., p_n) are quintic residues mod p", and the same
sentence with 7th power residues ([A002227](https://oeis.org/A002227)),
11th power residues ([A002228](https://oeis.org/A002228)), 13th power
residues ([A060363](https://oeis.org/A060363)) and 17th power residues
([A060364](https://oeis.org/A060364)). The tables go back to Western and
Miller (1968) and three of the entries are in Sloane's 1973 Handbook; they
stand at 15, 12, 10, 8 and 9 terms, the last of them found by a search to
2^42 in 2024 (A060363: to 10^11, in 2001). No sieve exists for the
property in the integers, so the engine tests every candidate prime of
each line with one modular power, at 5.6·10^11 to 2.5·10^12 p per second on
an RTX 4090. **Standing result ([RESULTS.md](RESULTS.md)): twenty new
terms** — a(16) through a(20) of A002226, a(13) through a(17) of A002227,
a(11) through a(13) of A002228, a(9) through a(12) of A060363 and a(10)
through a(12) of A060364.

**Status: PAUSED — open to others** — nothing is running. Built and
validated 2026-11-21; one campaign per family, each from the first
candidate of its line with the published terms rediscovered as canaries,
ran 2026-11-22 to 11-23 (UTC), 38 hours on the campaigns' clocks together,
and found the twenty terms above — the first advance on A060363 since 2001
and on the other four since 2024. Each campaign was stopped inside the
search for its next term, so every open index is searched empty
to p = 2.7555×10^15 on A002226 (a(21) open), 4.7549×10^16 on A002227
(a(18) open), 5.9176×10^13 on A002228 (a(14) open), 2.1644×10^16 on
A060363 (a(13) open) and 1.6197×10^17 on A060364 (a(13) open). Whoever
resumes runs `python launch.py --selftest` and `python score.py` first.

## The problem

Fix an odd prime power exponent — 5, 7, 11, 13 or 17 — and call it the
power. For a prime p with p − 1 divisible by the power, exactly one
nonzero residue in that many is a power-th power mod p. a(n) is the
smallest such p of which all of the first n primes p_1 = 2, ..., p_n are
power-th power residues.

**The convention the entries leave unsaid.** When p − 1 is not divisible by
the power, every nonzero residue mod p is a power-th power (fifth powers
permute the residues mod 7), so the sentence read literally would begin
a(n) = 3. The entries begin 151, 631, 331, 4421, 1429: the tables are over
the primes p with p − 1 divisible by the power, as the cubic sibling
A002225 says in a comment. The oracle's gate G0 pins this reading to the
five published first terms.

**The frontier.** A. E. Western and J. C. P. Miller's *Tables of Indices
and Primitive Roots* (1968) is the source; Don Reble extended all five in
2001; Sergey Paramonov extended four of them in April 2024 — A002226 to
a(15) = 3167880361091, A002227 to a(12) = 2701344818803 (with the comment
a(13) > 2^42), A002228 to a(10) = 4331892405391, A060364 to a(9) =
4143277702703. A060363 stands where Reble left it, a(8) = 72942989237 with
"no more terms through 10^11".

**Why it is open.** Whether p_i is a residue mod p is not a congruence
condition on p (for the quadratic analogue it is, by quadratic reciprocity,
which is why pseudosquares are sieved to 2^80 and these are not): by
Eisenstein's reciprocity law it is a congruence on a prime of the
cyclotomic field above p. In the integers there is nothing to sieve but
primality, and every prime of the line has to be tested. Each further term
costs the power times the last one.

**A sieve does exist one field up, for the quintic line.** In the fifth
cyclotomic field every prime p of the line is the norm of an element, and
for a suitably normalised element "p_i is a quintic residue mod p" becomes
a congruence on its four coordinates mod p_i. A scratch prototype of that
sieve on the device (2026-11-21, following finding RSL-006 of the Codex
review) agrees with this engine on every prime it was compared on and
sweeps the quintic line 146 times faster at 10^17. It is not an engine yet
and nothing here uses it; OPTIMIZATION_LOG.md round 4 has the measurements
and what an engine would need.

## The mathematics of the engine

**The line.** The power is odd and p is odd, so p − 1 is divisible by twice
the power: the candidates of a family are the integers 1 more than a
multiple of twice the power, in order — 11, 21, 31, ... for the quintic
line. Every prime the entry can mean is one of them.

**The test.** By Euler's criterion, p_i is a quintic residue mod p exactly
when p_i^((p−1)/5) ≡ 1 (mod p) (and likewise with 7, 11, 13, 17 in place of
5). The engine computes it as a square root: (p − 1)/5 is even, a square
root of 1 mod a prime is ±1, so the condition is p_i^((p−1)/10) ≡ ±1. The
first of these, for p_1 = 2, does three jobs at once for a candidate that
may not be prime: a prime of which 2 is not a residue fails it (four primes
in five on the quintic line, sixteen in seventeen on the last), and a
composite fails it unless it is a base-2 pseudoprime of a special kind,
because passing forces 2^(p−1) ≡ 1. There is therefore no primality pass:
one modular power per candidate decides almost everything. For p_1 = 2 the
device takes the inverse power, which is ±1 exactly when the power is and
can be started five squarings in from a single word (finding RSL-005 of
the Codex review; the engine's header has the identity).

**A launch** takes 2^30 consecutive candidates of the line through these
kernels:

1. *Sieve.* Candidates with a prime factor among the first 512 odd primes
   are dropped (they are composite). One thread holds 256 candidates in
   four registers: the primes below 64 by a rotated 64-bit pattern per
   word, the rest by marking their at most four multiples. A sieve prime q
   is used only in launches that begin above q. About 17% of candidates
   survive; two in five of the survivors are prime.
2. *The first test*, on every survivor: 2 raised to (p − 1)/10 (on the
   quintic line) by 64-bit Montgomery arithmetic, two candidates per thread
   with their squarings interleaved, and below 2^60 without the conditional
   subtraction of each squaring. This is 58% of the device time.
3. *The run*, on the candidates that passed: the same test for p_2 = 3,
   p_3 = 5, ... until one fails. The number of leading passes is the
   candidate's run. The first two of these are kernels of their own, each
   handing its passes to the next, so that a thread which has already
   failed does not hold its neighbours.

The device hands back every candidate whose run reaches the census floor.
The host proves each prime (deterministic Miller–Rabin, valid far above
2^63), re-reads its run with plain integer arithmetic — a disagreement is
an alarm — and classifies it against the frontier, the largest index
settled: a run above it is a discovery, settling every index up to the run
at once; a run equal to it is a near miss, one prime short of the open
term; shorter runs down to the floor are counted.

**What a discovery carries.** For each of the first n primes an explicit
root x with x^5 ≡ p_i (mod p) (or the 7th, ... power), so that "p_i is a
residue" is one modular power for anyone; for the first prime that is not a
residue, the value of its symbol, which is not 1; a Lucas certificate for p
(the factorization of p − 1 and a primitive root); and three confirmations
— the engine's, an independent implementation (sympy, the oracle, the
roots), and a re-derivation by different machinery (the device at another
alignment and sieve depth, and the CPU engine on the 16,384 candidates
around p).

**The least-p claim** rests on this project's own sweep from the first
candidate of the line — every candidate below p dropped as composite on a
small factor or on the first test, or as a prime of which 2 is not a
residue by the same test, or read to a run that was too short — with the
published terms rediscovered on the way. It is conditional on nothing.

**The ceiling is p < 2^63, enforced, and lower than the repository's
default of 10^40 for a measured reason.** That default belongs to hunts
whose sieve thins the line and whose terms are proved by certificate; here
the cost is linear in p. At the measured rates 2^63 is 190 days of device
time on the quintic line, 126 on the 7th-power line, 68, 57 and 43 on the
others, and the model's medians put four to eight open terms of every
family below it. Montgomery arithmetic with one 64-bit word needs
p < 2^63; a wider engine would buy line that is months to a year away.

## The model

Among the primes p with p − 1 divisible by the power, Chebotarev's theorem
gives the primes of run at least n the density (power)^−n. To first order
the first prime of run ≥ n past a cursor is the first event of a Poisson
process, and its expected count between two heights — the *exposure* — is
the number of primes of the class between them divided by (power)^n.

**The published terms are late, and the model says so.** Under that
independence the exposures between consecutive distinct published terms
would be standard exponentials. Over the 51 distinct terms of the five
entries their mean is 1.69: a Kolmogorov–Smirnov test rejects independence
(0.341 against a 5% critical value of 0.190), and the fitted rate is 0.59
± 0.08 of the independent one. The cause is a bias of Chebyshev's kind,
measured before the model was written (OPTIMIZATION_LOG.md, round 0):

- the prime ideals of degree two of the cyclotomic field — over the primes
  that are −1 mod the power — have every rational integer as a residue, and
  the explicit formula charges them against exactly the class this hunt
  counts. For one residue condition the deficit it predicts is the square
  root of the height over (the power less one) times its logarithm: 72
  primes of the quintic class below 4·10^7, and the measured deficit,
  averaged over the first 24 primes, is 89 of 121,651;
- the deficit falls off for conditions on products of several primes and
  is largest for the smallest primes: below 2·10^7 the quintic line has 451
  primes of run ≥ 4 where independence expects 508, while over 10^8 to
  3·10^10 the count of run ≥ 4 is 0.997 of expectation and of run ≥ 6,
  0.982;
- both engines agree on every one of those primes (9,776 primes of run ≥ 4
  on the 7th-power line between 10^8 and 3.1·10^9, device and CPU
  identical), so the deficit is arithmetic, not a miss.

No closed form is claimed for the bias near a first occurrence, where it is
far from small. The model therefore carries **one fitted constant, LATE =
0.59**: a first occurrence is the first event of a Poisson process of rate
LATE per unit of exposure. With it the 51 exposures sit at a distance of
0.149 from the exponential instead of 0.341 — but one constant fits them
only marginally. It was estimated from the same 51 numbers, and for a
fitted exponential of that size the 5% point of the distance is 0.149 and
the 1% point 0.176 (gate M1 simulates that null), so the published terms
are consistent with a single constant at about one chance in twenty. The
later half of the terms gives 0.67 and the earlier half 0.52: LATE probably
drifts toward 1 with height, which would bring the terms below EARLIER
than this table says. The finds are scored against it in RESULTS.md: they
came early, at a mean exposure of 0.51 against the fitted 1.69, so the
fitted constant ran late on all five lines.

A forecast starts from everything known to be empty: the last published
term, or the bound the entry states above it (A002227: a(13) > 2^42;
A060363: no more terms through 10^11), and a campaign's own cursor once it
is past both.

**Predictions, stated before any sweep** (2026-11-21, reissued the same
day with engine v2's rates and the origins above; medians, with the device
clock from the first candidate at the measured rate; `model_results.json`
has the quartiles and the 90% points):

| entry | rate (p/s) | open terms: median p (clock) |
|---|---|---|
| A002226 | 5.61·10^11 | a(16) 2.5·10^13 (44 s) · a(17) 1.2·10^14 (3 min) · a(18) 6.0·10^14 (18 min) · a(19) 3.1·10^15 (1.5 h) · a(20) 1.6·10^16 (8.1 h) · **a(21) 8.5·10^16 (42 h)** · a(22) 4.4·10^17 (9.2 d) |
| A002227 | 8.45·10^11 | a(13) 2.5·10^13 (30 s) · a(14) 1.6·10^14 (3 min) · a(15) 1.1·10^15 (22 min) · a(16) 8.4·10^15 (2.7 h) · a(17) 6.2·10^16 (20 h) · **a(18) 4.5·10^17 (6.2 d)** · a(19) 3.3·10^18 (46 d) |
| A002228 | 1.57·10^12 | a(11) 1.1·10^14 (1 min) · a(12) 1.2·10^15 (13 min) · a(13) 1.5·10^16 (2.6 h) · **a(14) 1.7·10^17 (31 h)** · a(15) 2.0·10^18 (15 d) |
| A060363 | 1.88·10^12 | a(9) 4.3·10^12 (seconds) · a(10) 6.0·10^13 (32 s) · a(11) 8.4·10^14 (7 min) · a(12) 1.2·10^16 (1.7 h) · **a(13) 1.6·10^17 (24 h)** · a(14) 2.3·10^18 (14 d) |
| A060364 | 2.49·10^12 | a(10) 1.3·10^15 (9 min) · a(11) 2.4·10^16 (2.6 h) · **a(12) 4.3·10^17 (48 h)** · a(13) 7.9·10^18 (37 d) |

Bold marks each family's day-long filter — the first term whose median
clock is a day or more — which is where the SCORE shape sits and every
optimization round was measured (engine v2 took a(17) of A002227 under a
day, and its shape moved to a(18)). A term's quartiles span roughly a factor
of five (an exponential waiting time), and one term in (the power) is a
tie: the same prime settles two indices.

## Running it

Requirements: an NVIDIA GPU with CUDA, Python 3 with CuPy, NumPy and SymPy.

```
python launch.py --selftest          # the gate battery; must end ALL GREEN (~95 s)
python launch.py --status            # where each family's cursor is; writes nothing
python score.py                      # gates x the ten frozen benchmarks (a few minutes)

python launch.py                     # THE HUNT: A002226, indefinite, resumable
python launch.py --family A060363    # another entry
python launch.py --to 1e16           # sweep every candidate p <= 10^16, then stop
python launch.py --stop-on-discovery # stop once this run confirms a new term
```

One checkpoint and one evidence ledger per family; one campaign at a time
(they share the device). A campaign runs until p = 2^63 unless stopped;
Ctrl+C ends it at the last segment boundary with the checkpoint written.
`--gpu-yield-ms N` idles the device N ms after each launch (a launch is 15
to 19 ms: N = 1 costs 5–6%) and `--gentle` idles a tenth of each launch's
time (about 9%). A launch holds about 1.6 GB of device memory. There is no host pool to size: at the open terms the host
verifies a few thousand primes per term, 60 microseconds each.

## Trust

The repository's [CONVENTIONS.md](../CONVENTIONS.md) apply in full. What is
specific here:

- **Three implementations.** The oracle (`residue_reference.py`) lists the
  set of powers mod p and checks Euler's criterion against it on every
  small prime; the CPU engine (`residue_search.py`) sieves with numpy and
  takes every power with Python integers; the GPU engine
  (`residue_gpu.py`) uses Montgomery arithmetic. Gate P1 pins the device
  stream to the CPU stream on 45 populated windows from the line's first
  candidate to the ceiling, both sides of the 2^60 boundary of its lazy
  arithmetic included; P2 shows it does not depend on the launch size, the
  alignment or the sieve depth; P5 shows the host's primality leg removing
  exactly the composites the first test lets through; P7 compares the first
  test with plain Python on every candidate, prime or composite, of windows
  placed on the corners of its arithmetic; P8 shows the staged run equal to
  the unstaged one at every floor; P0 sweeps the last candidates under 2^63.
- **Canaries.** A campaign rediscovers every published term in order from
  the first candidate, or halts. All 54 are also found by both engines in
  isolation (S3, P4), and 24 are rebuilt by the oracle from scratch.
- **Sampled parity.** Every 20 seconds a campaign compares the device with
  the CPU engine on 2,048 candidates of the launch just swept, at floor 1 —
  the check that covers what the device dropped.
- **A find is published after its segment is checked.** The three
  confirmations run where the prime is met; the evidence file and the
  `[DISCOVERY]` line wait for the canary and parity checks of the segment
  that holds it. Ctrl+C writes the last completed boundary; `--to` is exact
  and inclusive; a prime whose run filled the engines' cap of 40 primes
  would halt the campaign rather than be settled on a run nobody read to
  its end. Each is drilled in the selftest.
- **The model was wrong before it was right, and is still only marginal**:
  the independence model fails its validation gate on the published terms,
  and the fitted constant passes it at about one chance in twenty when
  judged against the right null (M1 reports both).
- Codex completed a static mathematical review of all five families on
  2026-11-21; engine v2, the launcher's four fixes and the model's are its
  dispositions. [Review and finding dispositions](codex-reviews/README.md)
