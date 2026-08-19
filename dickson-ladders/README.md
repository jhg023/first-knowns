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

**Results so far: a(10) = 9,328,409,578,841,430,
a(11) = 433,871,469,806,557,860 and
a(12) = 55,119,263,286,518,170,740**, all three found and verified
2026-08-18 — the first computational advance on this sequence since
October 2014, when Hiroaki Yamanouchi computed a(9) = 3,332,396,388,090
and left a(10) > 1.54665×10¹³. Each was verified four ways, including a
Brillhart–Lehmer–Selfridge primality certificate for every one of its
values, and each was re-verified from its evidence file before
publication. Details in [RESULTS.md](RESULTS.md).

**Status: ACTIVE** — the campaign is hunting **a(13)**, the deepest term
the model makes a prediction for.
The engine is v2 (913x the first gated engine on the production shape) and
the campaign around it was re-configured on 2026-08-18 for a measured
**27.9×** end-to-end, from 2.4×10¹⁵ to **6.8×10¹⁶ k/s**
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3). Most of that was not the
engine: the hunt was sieving one step behind the frontier, on a wheel 13×
finer than a(12) can possibly need. **a(12) is what it bought** — found
9 minutes 45 seconds into the re-configured campaign, at a depth the old
configuration would have needed about six and a half hours to reach.
The model put a(10) at median 1.68×10¹⁵, a(11) at 7.18×10¹⁶ and a(12) at
1.83×10¹⁹; all three landed late, at quantiles 0.915, 0.923 and 0.787 —
see the model scoring below and in RESULTS.md. It puts a(13) at 2.14×10²¹,
about five hours of sweep from where the cursor now stands. Predictions
are stated in full below and were fixed *before* the run, which is the
only time they are worth anything. Hunts are started deliberately by the
repository owner, never by an agent.

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
`[DISCOVERY]`, and the only thing that is evidenced. With a(12) settled, a
run-12 value is one short of a(13) and gets a single `[NEAR]` line with
its ordinal (verified 3-way — own chain, sympy, alternate-alignment
re-sieve — but not evidenced), and every run-7…11 value is **counted
only**: it appears in the census counts of the 30-second `[STATUS]`
heartbeat (`census 7:1368 8:352 9:78 10:27 11:2 12:1`) and nowhere else.
The moment a(13) lands, run-12 values drop into that count too. A run of
14 settles a(13) and a(14) at once, each logged once. `evidence/` holds
first occurrences only.
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
| a(14) | 5.02×10²² | **1.68×10²³** | 4.31×10²³ | 8.55×10²³ |

a(14) was added to the model on 2026-08-19, once a(12) had landed and the
hunt was within a day of a(13); a(10)–a(13) are byte-identical to the
predictions fixed before the run, so nothing above is hindsight. **The
a(14) row is the first one the campaign cannot simply outrun**: the
enforced ceiling of the 30030 wheel is 1.20×10²³, which sits between
a(14)'s Q1 and its median — sweeping the whole remaining wheel is worth
E = 0.54, a 41% chance of also landing a(14) (about 21% if the optimism
factor below is real). Going past that is not a `--to` change; it needs a
raised `J_CEIL`, and the wheel itself does not widen again until filter 16.

At the v2 rate (1.63×10¹⁷ k/s on the production n = 13 shape; the
end-to-end n = 10 rate is host-bound at 2.45×10¹⁵ k/s — see
[BENCHMARKS.md](BENCHMARKS.md)) that is **under a second to the a(10)
median, half a minute to a(11), minutes to a(12), and 3.6 hours to
a(13)** (P90 19 hours). The first three of those are now history rather
than forecast: a(10), a(11) and a(12) all landed, each a few times past
its median (table below). At the v1 rate a(13) was months to years; the
ledger of how that gap closed, with every reject and its price, is
[OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md).

**How the finds scored** (out of sample, against the table above):

| term | found at | model median | E at the find | quantile |
|------|----------|--------------|---------------|----------|
| a(10) | 9.33×10¹⁵ | 1.68×10¹⁵ | 2.47 | 0.915 |
| a(11) | 4.34×10¹⁷ | 7.18×10¹⁶ | 2.57 | 0.923 |
| a(12) | 5.51×10¹⁹ | 1.83×10¹⁹ | 1.54 | 0.787 |

All three are late draws — 5.5×, 6.0× and 3.0× past their medians, where
the median wait is E = ln 2 ≈ 0.69. Pooling them as Exp(1) draws gives a
maximum-likelihood optimism factor of **2.2×** with a 95% interval of
roughly **[0.9, 10.6]**; that still contains 1, so it is still not
evidence the singular series is wrong. The third draw was the mildest of
the three and *lowered* the estimate (it was 2.5× on two), while the
one-sided tail — P(ΣE ≥ 6.58) for three Exp(1) draws — tightened to
**0.04**. Three late draws in a row are worth watching; a(13) is the one
that decides it.

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
read off **rungs** — the model's Q1/median/Q3/P90 for every **open** term
(from `model_results.json`) plus the ceiling — logged `[RUNG]` as each is
passed and shown with an ETA in every `[STATUS]`. **A rung retires with
its term:** the moment a term is found, its unreached quartiles leave the
ladder, a `[RUNG]` line says so, and both the next rung and the live odds
in `[STATUS]` re-aim at the next open term. (Before that was true, the
hunt found a(12) at k = 5.51e19 and went on advertising `next a(12) P90 at
9.51e+19` while it swept for a(13).)
`--to K` caps a run deliberately and `--stop-on-discovery` halts after a
first occurrence; both are opt-in. The **filter follows the frontier**,
and how far behind it follows is the single largest lever in the project.

The filter sets the wheel: W(n) is the product of the primes ≤ n+1,
because run(k) ≥ n forces q | k for every prime q ≤ n+1 (m runs over a
complete residue system mod q, so some m has m·k² ≡ −1, and that value is
larger than q above the floor). With the default **`--filter-lag 0`** the
sieve asks only for the next open term — n = frontier + 1, which is **13**
now that a(12) has landed — so it rides the **30030** wheel rather than
the 2310 one: **13× fewer candidates per unit of k-line and 13× fewer
survivors to classify.** Nothing about the least-claim weakens, because
a(13) *is* a multiple of 30030 by that same argument, so the coarser wheel
skips no candidate that could be a(13). (W(13) = W(12) = 30030, both being
the primes ≤ 14, so the a(12) find moved the filter without moving the
wheel or the cursor.)

`--filter-lag 1` runs a step behind instead: the sieve stays at n =
frontier, so run-12 values (one short of a(13)) still appear and get their
`[NEAR]` line and the census fills in below the frontier. That is
bookkeeping, and it costs a factor of thirteen. When a step widens the
wheel the cursor is re-denominated by floor — an overlap of under one
period, never a gap — and logged as a `[STAGE]` line.

Every 30 s of wall clock (`--heartbeat`) the launcher logs a `[STATUS]`
line from its own timer thread — whatever the main loop is doing: position,
end-to-end rate, survivors, **the census counts per run length from 7 to
the frontier** (`census 7:280 8:71 9:28 10:8` — how many run-7s, run-8s, …
the campaign has met; the only place those values appear), finds, live
model odds, the next rung and its ETA — and, if no segment has closed since
the previous line, what it is busy with and for how long, so a stall never
looks like a hang. `--status` prints the same counts from the checkpoint.

**Ctrl+C ends the run, it does not crash it.** The launcher writes a
checkpoint **at the last fully classified segment** — not the live cursor,
whose counters are updated per candidate and would double-count the census
when the segment is redone — logs one `[STAGE]` line saying where it
stopped, and exits **130**. No traceback, including when a second Ctrl+C
lands while the checkpoint is being written: the shutdown ignores further
interrupts until the file is on disk (`huntlib.shutdown`; CONVENTIONS.md
"Stopping a run"). Resuming redoes only the segment that was in flight.

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

**`--q2 D` sets the sieve depth** (default **262144**, against the frozen
benchmark depth of 65536). Depth is the dial between the two sides of the
pipe: deeper sieving costs device time and removes survivors the host would
otherwise have to classify. Measured at n = 12, k ≈ 10¹⁹, per 10¹⁸ of
k-line:

| `--q2` | device | survivors | host core-s | pool needed | end-to-end |
|--------|--------|-----------|-------------|-------------|------------|
| 65536 | 14.35 s | 2,293,610 | 104.8 | 8 workers | 6.97×10¹⁶ k/s |
| 131072 | 14.93 s | 1,106,720 | 50.6 | 4 workers | 6.70×10¹⁶ k/s |
| **262144** | **14.78 s** | **560,509** | **25.6** | **2 workers** | **6.77×10¹⁶ k/s** |
| 524288 | 16.07 s | 292,700 | 13.4 | 1 worker | 6.22×10¹⁶ k/s |

The device is nearly **flat** from 65536 to 262144 — the extra primes land in deep
compaction rounds whose populations are already tiny — so four times the
depth costs the device 3% and takes four times the work off the host. All
four rows are within 3% end-to-end, which means the real choice is not
speed but **how much of the machine the hunt asks for**: eight host
processes, or two.

Deepening the sieve is also what found a **correctness bug that had been
latent since the engine was written**. The walk that builds the kill-bit
table squares a residue, so its intermediates reach q²; it was written in
32-bit, exact only for q < 2¹⁶ — and because every gate in the file used
the default depth of 65536, no test had ever evaluated a prime whose square
leaves u32. At 262144 the table came out wrong above 2¹⁶ in *both*
directions, so the sieve killed candidates it should have kept, and the
a(7) canary went missing on the first smoke run. The walk is u64 now (exact
to q < 2³¹) and `g16_deep_sieve_arithmetic` gates the table against
big-integer divisibility at the campaign depth, sampling primes on both
sides of 2¹⁶. The lesson is in [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md):
a gate that only ever runs at one point in a parameter's range does not
test the parameter.

`--workers N` sets the classification pool (default **4**; `1` is the
serial path). Two keep up with the device at the settings above, so the
default is twice the requirement and the pool sits at ~38% duty. It is
sized from that measurement rather than from the core count: a hunt runs
for days on somebody's desktop and must leave the machine usable, and
asking for more than the device can absorb buys nothing anyway.
Classification itself was also made 2.4× cheaper (111.2 →
45.7 µs per survivor) by testing base 2 first: a strong-test *failure* is a
proof of compositeness, so a base-2 chain gives a rigorous upper bound on
the run at one modular exponentiation instead of seven, and the full base
set is re-run only when that bound reaches a length the campaign would
actually record. **Every run length written down still comes from the full
base set.**

The pool is started **one interpreter at a time** (`--worker-ramp`, default
0.35 s) at below-normal priority, warm before the first segment, because N
fresh interpreters importing numpy and sympy in the same instant is the
largest and fastest host load step the campaign makes — and it lands while
the device is flat out on the next segment. Segments are 2⁴² candidates;
`--seg-span` in k overrides.

## What the campaign asks of the machine

A hunt runs for days on somebody's desktop, so this one is sized to leave
the machine usable rather than to take the last percent of throughput.
All of it is measured rather than asserted:

- **it asks for a quarter of the CPU an earlier default did** (4 workers,
  ~38% duty), and gives up 2% of throughput to do it;
- **the pool ramps** instead of stamping — one interpreter at a time, at
  below-normal priority, warm before the first segment, because N fresh
  interpreters importing numpy and sympy in the same instant is the
  largest and fastest host load step a campaign makes, it lands while the
  device is flat out on the next segment, and the pool has a whole segment
  of slack in which to avoid it;
- **the device no longer square-waves.** Before, the pool was the
  bottleneck by 2.3× and the GPU idled 60% of the time, alternating
  98%/12% utilization every few seconds — thousands of full-amplitude load
  transitions an hour. It is now the device that binds, so it runs at a
  steady load instead;
- **`--gpu-yield-ms D`** idles the device D ms per segment and
  **`--gentle`** is a preset that halves the workers, slows the ramp and
  sets a 25 ms yield, for a few percent of the rate — there when a machine
  is shared with something else, or is simply not to be leaned on;
- **a crash costs one segment, not the campaign** — see below;
- **the campaign logs the machine's state at start** (GPU, SM count, VRAM
  held, driver, power limit, max clock, temperature), so the log answers
  what the run was actually holding.

What this program deliberately does **not** do is change a machine setting
for you: no clock caps, no power limits, no priority games beyond
below-normal on its own workers. Those are the owner's to choose.

### A crash must not cost the cursor

A checkpoint written across an abrupt stop came back as **785 bytes of
NUL**: exactly its own length, none of its content. `os.replace` is atomic
for the directory *entry*; the *data* was still in the page cache when the
process stopped. Saves now `fsync` before the replace and rotate the
previous file to `.bak`, so at every instant at least one complete
checkpoint is on disk. A file that is present but unreadable now raises
`CheckpointCorrupt` rather than being treated as absent — for a live
frontier those two demand opposite responses, and the old behaviour would
have quietly restarted the sweep at the floor. Both paths are drilled in
`--selftest` against the exact 785-NUL corruption.

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
