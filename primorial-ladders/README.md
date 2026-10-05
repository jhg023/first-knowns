# primorial-ladders — A115785, A115786 and A145743

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

**Fifteen new terms, found and verified 2026-10-02 to 2026-10-05:
a(16)–a(19) of A115785, a(17)–a(20) of A115786 and a(14)–a(20) of A145743**
— the first advance on the first two since 2006 and on the third since
2008. The integers, their verification and the campaigns are in
[RESULTS.md](RESULTS.md).

A GPU hunt for the next terms of three **shift ladders** — one unknown and
n conditions that differ by an additive constant. **A115785** asks for the
smallest prime p such that p − prime(1)#, p − prime(2)#, …, p − prime(n)#
are all prime, and **A115786** the smallest prime p such that p + 2#,
p + 3#, …, p + prime(n)# are all prime (prime(i)# the primorial, the product
of the first i primes). Both are Rick L. Shepherd's (January 2006); their
last terms, a(15) = 618,681,508,598,750,923 and a(16) = 29,065,965,967,667,
are Jens Kruse Andersen's of February 2006, and nothing has moved on either
in twenty years. **A145743** asks for the smallest composite number m such
that all n numbers m + 4·k² for k = 1, 2, …, n are prime — Farideh
Firoozbakht's (October 2008), its last two terms Donovan Johnson's of
November 2008, a(13) = 91,450,844,347. It rides the same engine.

**Status: PAUSED — open to others** — nothing is running. One campaign
per family ran between 2026-10-02 and 2026-10-05 and each was stopped
inside the filter for its next term. The frontier stands at
a(19) = 7,858,467,306,309,706,402,625,473 on A115785, with a(20) open above
71# = 5.58×10²⁶ and nothing swept there yet;
a(20) = 276,111,714,233,825,559,827 on A115786, with a(21) open and
searched empty to p = 3.7447×10²⁰; and
a(20) = 86,871,442,473,592,036,108,753 on A145743, with a(21) open and
searched empty to m = 8.9034×10²². The model puts a(21) of A115786 and of
A145743 at about a week each and a(20) of A115785 at months
([RESULTS.md](RESULTS.md), "What is open now", which also lists what a
resume owes first).

## The problem

| entry | name (%N), verbatim | published terms | published frontier | last moved |
|---|---|---|---|---|
| [A115785](https://oeis.org/A115785) `more` | Smallest prime number p such that p - prime(1)#, p - prime(2)#, ..., p - prime(n)# are all prime, where prime(i)# is the primorial of the i-th prime (A002110(i)). | a(1)–a(15) | a(15) = 618,681,508,598,750,923 | Jens Kruse Andersen, Feb 2006 |
| [A115786](https://oeis.org/A115786) `more` | Smallest prime number p such that p + 2#, p + 3#, ..., p + prime(n)# are all prime, where x# = A034386(x) is the primorial. | a(1)–a(16) | a(16) = 29,065,965,967,667 | Jens Kruse Andersen, Feb 2006 |
| [A145743](https://oeis.org/A145743) `more` | a(n) is the smallest composite number m such that all n numbers m+4*k^2 for k=1,2,...,n are prime. | a(1)–a(13) | a(13) = 91,450,844,347 | Donovan Johnson, Nov 2008 |

The two primorial entries are Carlos Rivera's Puzzle 350 (2006) and a Prime
Curio for 313; A115785 is a subset of A006512 (the greater of twin primes)
and A115786 of A001359 and A022004, as their comments say, but no entry is
an affine map of either, so nothing rides for free. A145743's comment
"There is no further term up to 5×10⁸" predates a(12) and a(13). None of
the three carried a bound at its open index. Found here, and not yet
entered in the OEIS (2026-10-05 export): a(16)–a(19) of A115785,
a(17)–a(20) of A115786 and a(14)–a(20) of A145743, whose a(16) and a(17)
are one integer.

**Two kinds of line.** On A115786 and A145743 every condition of index n is
a condition of index n + 1, so a(n+1) ≥ a(n), the sweep for a(n+1) starts
at a(n), and one integer can settle several terms at once (A115786's
a(5)–a(8) are all 41; A145743's a(8)–a(10) are all 143473). On A115785
the condition p − prime(n)# prime puts a(n) above prime(n)# + 1, and every
published term from a(13) on lies within 2% of its own primorial
(a(15) − 47# = 3.8×10¹⁵ against 47# = 6.1×10¹⁷). **Each index of A115785 is
its own short line from prime(n)#**, prime(n+1) times further out than the
last, and a find says nothing about the next: a(16) was found above 53# =
3.26×10¹⁹, a(17) above 59# = 1.92×10²¹, a(19) above 67# = 7.86×10²⁴ and
a(26), the last index under this project's ceiling, above 101# =
2.3×10³⁸. Every one of those lines is past 2⁶⁴.

**Which number goes in the OEIS.** The names give the term a letter: p on
the two primorial entries, m on A145743. An evidence file carries the
integer under that letter, `forms` reads "p - prime(k)#, k = 1..n (and p
prime)" (or "p + prime(k)#…", or "m + 4*k^2, k = 1..n (and m composite)"),
and `oeis_terms` is literally what to submit — `{"16": <integer>}` reads
"a(16) is this integer", with several indices listed when one integer is
several terms.

## The mathematics of the engine

**The killed set.** For a prime q and a constant c, q divides the term
plus c exactly when the term is ≡ −c (mod q), so the residues of the term
that q kills are

    K(q, n) = { −c mod q : c a constant of index n }

— the constants being 0 and ∓prime(k)# for k = 1..n on the primorial
entries (p itself is a form: p must be prime) and 4k² for k = 1..n on
A145743 (m is *not* a form: it must be composite, which no sieve can say
and the classification enforces). The oracle walks every residue and tests
divisibility; the CPU engine builds {−c mod q}; the GPU engine consumes
the set and never sees a form. G2b and G3 pin the three constructions
against each other at every prime under 300.

**Its size, and why the wheel is weak.** On the primorial entries every
primorial from prime(k) ≥ q is 0 modulo q, so every form from index π(q)
on kills the *same* residue 0 that p itself kills:

    w(q, n) ≤ 1 + min(n, π(q) − 1)         (A115785, A115786)

Thirteen kills at most for q = 47 where a linear ladder's 47 kills n of
its 47 residues, and six for 17. On A145743, −4k² runs over −4 times the
squares, (q − 1)/2 nonzero values and 0 (from k = q), so
w ≤ (q + 1)/2. Both bounds are below q, so no prime kills every residue:
the constellations have no fixed prime divisor, Dickson's conjecture
applies, every sequence is conjecturally infinite and a find confirms the
guiding conjecture. The small primes being nearly blind is the regime
lcm-ladders found: the primes to 59 keep 2.4×10⁻⁴ of the line at every
index of the primorial entries (shift-ladders' base-4 wheel to 103 kept
1.4×10⁻⁵), so what the hunt pays for is candidates, and the engine that
counts is the one with the highest candidate rate.

**The forced classes.** Every constant is even, so the term is odd in all
three families. Modulo 3, p and p ∓ 2 leave one class — p ≡ 1 (mod 6) on
A115785, p ≡ 5 (mod 6) on A115786 — and on A145743 the forms 4k² kill
2 (mod 3) from k = 1 and 0 (mod 3) from k = 3, so m ≡ 1 (mod 6) from n = 3.
No prime past 3 is ever forced (w ≤ π(q) < q − 1 for q ≥ 5). The engine
sweeps t with the term r + 6t; the CPU engine marks the dense line knowing
nothing of the class, so the parity gate checks the forcing as well as the
sieve.

**The exception zone.** A kill by q proves nothing unless the value exceeds
q. The smallest value is p − prime(n)# on A115785 and the term itself (or
m + 4) elsewhere, so the device starts at prime(n)# + q2 on A115785 (q2 on
the others, far below any frontier), and the integers between the
definition's floor and the engine's are classified one at a time on the
host at every filter start. It is not vacuous: A115785's a(5) = 3463 lies
inside its zone at depth 4096.

**The engine** is plus-two-cliques' engine v3 and planner p2, taken whole
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), Decision 1): the window sieve
— for a fixed wheel residue the candidates of consecutive periods form an
arithmetic progression modulo every sieve prime, so "which of the next 160
periods does q kill" is one window into a periodic bit pattern, read in one
or two 64-bit shared loads and a few funnel shifts — with subset wheels,
the 2⁶⁴ reduction bound, the narrow and wide survivor records, lazy and
folded in-block rounds, generated tail rounds, and the planner that chooses
wheel and window together to minimise the expected clock to a confirmed
find. The kernel sees killed residues, never a form; a constant added to
the term in place of a product with an earlier term changed the CPU
engine's `killed_residues` and not one line of
device code. Candidates are carried as (base, offset) with the base a
Python integer, so the A115785 lines above 2⁶⁴ cost nothing extra; the
parity gate (G9) pins GPU against CPU bit for bit on 29 populated windows:
every family, the classes 1 and 5 (mod 6), one- to three-level and subset
wheels, first levels of eight million residues on both records, windows
just above 23#, 41#, 43#, 53#, 71# and 101#, past the proof crossing and
hard against the 10⁴⁰ ceiling.

**Measured where the campaign was expected to spend its days, then
re-swept.** Nsight Compute on one sieve launch at A115785's n = 19 (the
filter whose a(19) was priced at days; [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), round 1): the
sieve kernel is 96% of the device; the window sieve and extraction are 75%
of its samples; the ALU pipe runs at 76% and the LSU at 77%, issue slots
66% busy, seven blocks per SM for shared memory where the registers allow
eight. The window costs about 12.5 instructions per prime and 160-period
window, of which the five funnel shifts and the fused ORs are the floor of
this formulation. Every inherited constant was re-swept, paired and
interleaved, and found still at its optimum on this problem but one: the
extraction batch, which the inherited rule set to one residue to keep a
seventh block per SM, where two residues at six blocks measure 1.038×
here. Two rules now decide on the *compiled* occupancy — the batch is two
unless that is register-heavy, and the queue entry is three bytes rather
than four where that buys a block — for **1.057×** at n = 19 and
1.00–1.02× at the openings. One restructure was tried and rejected
(hoisting the window's validity masks, 0.978×), and the levers that would
cut the window's loads were priced against the shared memory they would
take from occupancy and declined.

**Two kinds of promotion.** After a find on A115785 the campaign moves to
prime(n+1)# + 2 and drops the rest of the old segment, which is on a
retired line. On the monotone families the classification reads every
survivor's run to the filter plus six, so everything the old filter swept
past a find was already classified against the new filter's conditions:
the new filter resumes at the old segment's end, re-denominated by floor
into its own period with the clip at the old boundary. Both are drilled on
scratch files with the real published terms as the finds, and the whole
loop is drilled end to end by finding two consecutive published terms in
every family.

**The ceiling is 10⁴⁰, measured.** A value p ∓ prime(k)# has no
multiplier × term ± 1 structure, so each value of a discovery is proved on
its own by a bounded certificate search on N − 1 or N + 1 (huntlib's
default search, then one retry at 200 ECM curves), and rule 5h asks for
the honest ceiling to be measured: random structureless primes at 10²⁵,
10³⁰, 10³⁵ and 10⁴⁰ were proved 46 of 46 by the first search, the worst in
0.4 s ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), Measurement 1). The
selftest proves four values of a find's own shape per family at the
height. A115785's line leaves the ceiling between n = 26 (101#) and n = 27
(103# = 2.4×10⁴⁰), where that campaign ends. The deterministic Miller–Rabin
bound, 3.317×10²⁴ less the largest constant, is crossed on A115785 between
n = 18 (61#) and n = 19 (67#): from a(19) on every discovery's values are
proved by certificate, and it is a `[MILESTONE]`, never a stop.

## The odds model

Bateman–Horn over the forms of an index, the singular series computed from
the same killed sets the sieve is built from, each value about the term.
On A115785 the integral runs over v = p − prime(n)# from the definition's
floor: near it the factor 1/ln(p − prime(n)#) is large, and a grid in ln p
would put three points inside the 2% band every published term lies in.

**Validation (G11), stated before the run.** E is the expected number of
hits between an index's floor (prime(n)# on A115785, a(n−1) elsewhere) and
the a(n) that actually occurred; under a correct model it is a draw of
Exp(1). Over the 21 published terms that were searched for (strictly above
their predecessor, above the exception zone):

| A115785 | a(6) | a(7) | a(8) | a(9) | a(10) | a(11) | a(12) | a(13) | a(14) | a(15) |
|---|---|---|---|---|---|---|---|---|---|---|
| E | 1.31 | 3.39 | 4.38 | 1.44 | 4.98 | 2.78 | 2.53 | 0.80 | 1.38 | 1.42 |

| A115786 | a(9) | a(11) | a(12) | a(13) | a(14) | a(15) | a(16) | | A145743 | a(8) | a(11) | a(12) | a(13) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E | 0.48 | 0.96 | 0.17 | 0.91 | 0.42 | 0.28 | 0.07 | | E | 2.00 | 0.21 | 3.28 | 0.12 |

They sum to 33.3 at P = 0.991 under the Gamma(21, 1) law, quantiles
0.07–0.99 — inside both 0.1% tails, as the gate requires, but the families
disagree: A115785's terms come **2.4×** later than its intensity says
(mean E 2.44 over ten draws, the last three near 1.4) and A115786's early
(mean 0.47 over seven). Read A115785's medians as floors and budget
2–3× them, which is also the repository's record on first occurrences.

**What it predicted** (`model_results.json`, written before the run and
kept as the record; A115785's depths given as the
offset above prime(n)#, which is where the whole search happens):

| A115785 | above | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|
| a(16) | 53# = 3.259e19 | 1.98e16 | **4.89e16** | 9.96e16 | 1.68e17 |
| a(17) | 59# = 1.923e21 | 5.70e17 | **1.40e18** | 2.86e18 | 4.81e18 |
| a(18) | 61# = 1.173e23 | 1.73e19 | **4.25e19** | 8.64e19 | 1.45e20 |
| a(19) | 67# = 7.858e24 | 5.48e20 | **1.35e21** | 2.73e21 | 4.59e21 |
| a(20) | 71# = 5.579e26 | 1.76e22 | **4.32e22** | 8.77e22 | 1.47e23 |
| a(21) | 73# = 4.073e28 | 5.91e23 | **1.45e24** | 2.93e24 | 4.91e24 |

| A115786 | Q1 | median | Q3 | P90 | | A145743 | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|---|---|---|---|---|
| a(17) | 3.05e15 | **1.24e16** | 3.80e16 | 8.66e16 | | a(14) | 8.97e11 | **3.51e12** | 1.18e13 | 2.93e13 |
| a(18) | 7.13e16 | **2.97e17** | 9.12e17 | 2.07e18 | | a(15) | 1.36e13 | **7.28e13** | 2.71e14 | 6.99e14 |
| a(19) | 1.84e18 | **7.57e18** | 2.29e19 | 5.13e19 | | a(16) | 3.45e14 | **1.92e15** | 7.09e15 | 1.80e16 |
| a(20) | 4.78e19 | **1.93e20** | 5.74e20 | 1.27e21 | | a(17) | 1.39e16 | **7.37e16** | 2.62e17 | 6.48e17 |
| a(21) | 1.31e21 | **5.16e21** | 1.52e22 | 3.33e22 | | a(18) | 4.99e17 | **2.51e18** | 8.61e18 | 2.09e19 |
| a(22) | 3.88e22 | **1.51e23** | 4.38e23 | 9.53e23 | | a(19) | 2.13e19 | **1.02e20** | 3.40e20 | 8.08e20 |

At the measured rates ([BENCHMARKS.md](BENCHMARKS.md): 4.6×10¹⁵ p/s at
A115785's n = 16 rising to 1.3×10¹⁶ at n = 19; 5.0×10¹⁵ to 1.4×10¹⁶ p/s on
A115786; 1.4×10¹⁷ to 2.8×10¹⁷ m/s on A145743 at n = 18 and 19) the model's
expected clock to a confirmed find is: A115785 a(16) 16 s, a(17) 5 min,
a(18) 1.9 h, a(19) 44 h, a(20) 66 days; A115786 a(17) 7 s, a(18) 2 min,
a(19) 37 min, a(20) 12 h, a(21) 14 days; A145743 a(14)–a(17) seconds,
a(18) a minute, a(19) 22 min. Every one of those is a floor, and A115785's
by 2.4× — budget a week for its a(19).

**How the finds scored.** Fourteen draws (A145743's a(17) came with its
a(16) and was not searched for), each E taken from the floor its sweep
started at:

| | A115785 a(16)–a(19) | A115786 a(17)–a(20) | A145743 a(14)–a(16), a(18)–a(20) |
|---|---|---|---|
| E | 1.57, 0.21, 4.23, 0.08 | 0.03, 0.60, 4.97, 0.21 | 0.30, 0.83, 3.81, 0.27, 1.26, 4.34 |
| mean | 1.52 | 1.45 | 1.80 |

They sum to 22.72, a mean of 1.62 at P = 0.980 under Gamma(14, 1): late,
as the published terms were, and by about the same factor in all three
families — the split the published draws showed (A115785 2.4× late,
A115786 early) did not persist. Four draws landed at the 98th–99th
percentile and one at the 8th: a(18) of A115785 took 8.15 h against the
1.9 h above, a(19) of A115786 5 h against 37 min, a(20) of A145743 came at
sixteen times its median after 39 h, and a(19) of A115785, budgeted at a
week, came in 4.25 h. The filters swept whole ran at 0.98–1.01× the
rates above on the primorial entries. The open terms from where the
cursors stand: a(20) of A115785 median 4.32×10²² above 71# (45 days at the
benchmark rate), a(21) of A115786 median 6.74×10²¹ (6.6 days), a(21) of
A145743 median 3.59×10²³ (5.0 days at the rate its last filter held) —
each of them optimistic by the 1.5–2× above. The per-term table, the
campaign rates and the probabilities are in [RESULTS.md](RESULTS.md).

## Running it

Requires an NVIDIA GPU with CuPy, plus numpy and sympy.

```bash
python launch.py --selftest    # the full gate battery; must end ALL GREEN
```

```bash
python score.py                # gates x 6 fingerprinted shapes
```

```bash
python launch.py --status      # where a cursor stands; reads, never writes
```

The hunt itself is **the owner's command** (CLAUDE.md rule 0a) and is
started deliberately, never by automation:

```bash
python launch.py                       # A115785, the default
python launch.py --family A115786
python launch.py --family A145743
```

Each family keeps its own checkpoint under its own config key, and no
campaign will read another's cursor. With the paused campaigns'
checkpoints in place each command resumes at its open term (a(20), a(21),
a(21)); the checkpoints are runtime state and are not in the repository.
Without them a fresh A115785 campaign opens at
53# + 2 with the filter n = 16, covers its exception zone on the host, and
sweeps; each find moves it to the next primorial. The other two open just
above their last published term and carry the line across each find — so a
fresh clone re-derives the fifteen terms first, about 63 hours, until they
are entered in the oracle's `FOUND` ([RESULTS.md](RESULTS.md)). The
hunt is indefinite by default, resumable, checkpointed every segment, and
stops cleanly on Ctrl+C with exit 130. `--to` caps the depth,
`--stop-on-discovery` exits once **this run** confirms a find, `--workers`
overrides the pool that is otherwise sized from a measurement at the
campaign's own filter, and `--gentle` yields the device and classifies
inline for a quieter desktop.

## Trust

Read [CONVENTIONS.md](../CONVENTIONS.md) for the machinery every project
here is built to. Specific to this one:

- **Three independent implementations.** A sympy-only oracle that walks
  residues and tests divisibility, a numpy CPU engine that marks the dense
  line with no wheel at all, and a CuPy engine that generates wheel
  survivors and tests them. G9 pins the GPU stream to the CPU stream bit
  for bit on 29 populated windows (above).
- **The killed set is built three ways** (the walk, {−c mod q}, direct
  divisibility of the values) and held to its proved bound at every prime
  under 120 (G2b, G3).
- **Canaries.** The GPU stream rediscovers A115785's a(9), a(10) and
  a(11), A115786's a(12) and a(13) and A145743's a(12) and a(13) as first
  occurrences from each index's own floor, on the dense line and in class space;
  the real loop then finds a(13)–a(14) of A115785, a(14)–a(15) of A115786
  and a(12)–a(13) of A145743 end to end on scratch files, promoting itself
  between them.
- **The protocol is tested in both directions, on every family**, with the
  domain leg (a prime m is rejected on A145743 whatever its forms do) and
  the stopper that is below 2 rather than composite (A115785's a(4) = 229
  against 11#).
- **The benchmark checks itself.** `SCORE2L` and `SCORE1L` sweep the
  identical absolute window with a two-level and a one-level wheel and must
  return the same 922 survivors and checksum.
- **Every ceiling raises rather than computes**, A115785's floor among
  them: the engine refuses a window under prime(n)# + q2.
- **The evidence files speak each entry's language** (p, p, m), checked by
  the names drill on every record on disk and on the writer's header.
