# RESULTS — plus-two-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Fourteen terms: a(14)–a(19) of A083518 and a(11)–a(18) of A083519.** Found
2026-10-02 by one campaign per family, `python launch.py` and
`python launch.py --family A083519`, no flags: A083518 on engine v2 and
A083519 on engine v3, both with planner p2. The first advance on either entry
since 2004 and 2008: A083518's last terms were David Wasserman's a(9)–a(13)
of November 2004, with his comment "Next term is > 266\*10^9", and A083519's
was Donovan Johnson's a(10) of November 2008.

Each evidence file was re-verified from disk on 2026-10-02 by a harness that
shares nothing with the launcher: the prefix matched to the OEIS data (the
2026-10-02 export) plus this project's earlier finds, keyed by each entry's
own %O offset; a(n) > a(n−1) and a(n) ≡ 3 (mod 6); every condition
recomputed from the bare definition, a(n)·a(i) + 2 for every earlier term
a(i), and tested with sympy's `isprime`; every value's certificate
re-verified by `huntlib.certificate.verify` and matched to its value; the
`least_claim` range matched to the prefix; and each ledger matched to its
files. **14 files, 209 certificates, all green**: 66 BLS75 Theorem 1 on a
completely factored N − 1, and 143 deterministic Miller–Rabin below
3.317e24. Nothing is `unproved`. The largest value proved is A083519's
a(17)·a(18) + 2, 41 digits; A083518's is a(18)·a(19) + 2, 40.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine at a different depth), the
oracle's re-derivation against the whole prefix, and a `least_claim`. Times
below are the ledger's, local; a *leg* is the wall clock from the previous
find (or the campaign's start) to this one, its verification and the
promotion to the next filter included.

### A083518 — one campaign, 2026-10-02 00:59 to 09:22 (8.38 h), from a(13) = 77,597,861,913

| n | a(n) | found | leg |
|---|---|---|---|
| 14 | 2,588,149,919,487 | 10-02 00:59:15 | 8 s |
| 15 | 23,378,349,363,843 | 10-02 00:59:27 | 12 s |
| 16 | 4,516,926,122,502,183 | 10-02 00:59:35 | 8 s |
| 17 | 94,069,473,579,369,267 | 10-02 00:59:53 | 18 s |
| 18 | 3,650,348,055,212,814,105 | 10-02 01:04:10 | 4.3 min |
| 19 | 517,222,792,129,337,171,163 | 10-02 07:24:34 | 6.34 h |

a(14) is 9.7× Wasserman's bound. The campaign did not start from the bound:
it swept from a(13) + 1, so the comment is re-established as well as
superseded. After a(19) the campaign swept the filter for a(20) for 1.96 h,
209,513 of the 5,392,200 launches of its first segment, and was stopped by
the owner at 09:22:04 with that cursor saved.

### A083519 — one campaign, 2026-10-02 11:29 to 18:21 (6.86 h), from a(10) = 8,403,613,179

| n | a(n) | found | leg |
|---|---|---|---|
| 11 | 47,785,411,179 | 10-02 11:29:48 | 6 s |
| 12 | 180,282,095,955 | 10-02 11:30:01 | 13 s |
| 13 | 63,912,578,414,415 | 10-02 11:30:08 | 7 s |
| 14 | 107,761,444,900,725 | 10-02 11:30:18 | 10 s |
| 15 | 123,524,156,469,847,875 | 10-02 11:30:43 | 25 s |
| 16 | 4,584,343,952,358,163,539 | 10-02 11:34:40 | 4.0 min |
| 17 | 19,935,451,450,502,600,259 | 10-02 11:42:22 | 7.7 min |
| 18 | 1,352,093,682,658,200,396,075 | 10-02 17:56:04 | 6.23 h |

The indices are the entry's own: A083519 is offset 0, its published list is
a(0)–a(10), and the first find is a(11). After a(18) the campaign swept the
filter for a(19) for 25 min, 49,396 of the 1,774,080 launches of its first
segment, and was stopped by the owner at 18:21:07 with that cursor saved.

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per term, and one ledger
per family, `evidence/a<number>_discoveries.json`.

**What the early terms are worth**, as the README said before the run:
A083518's a(14)–a(17) took 46 s between them and A083519's a(11)–a(15)
61 s. They stood since 2004 and 2008 because nobody returned to these
entries, not because they were hard. The hunt proper was A083518's a(18)
and a(19) and A083519's a(16)–a(18), and the two long legs took the six
hours each that the table had priced.

### The least-claim basis

Each file's `least_claim` is the sweep from a(n−1) + 1 to a(n) under the
filter of index n: every condition of that index, in the forced class
a(n) ≡ 3 (mod 6). That class is a theorem from A083518's index 4 and
A083519's index 3 (README, "the mathematics of the engine"), and every term
here is in it. The floor is a(n−1) because the definition requires
a(n) > a(n−1). The wheel and the sieve depth were planned per filter:

| entry | n | wheel primes past 2 and 3 | sieve depth |
|---|---|---|---|
| A083518 | 14 | to 23, and 31 | 2^19 |
| A083518 | 15 | to 31 | 2^18 |
| A083518 | 16 | to 37 | 2^17 |
| A083518 | 17 | to 43, without 41 | 2^17 |
| A083518 | 18 | to 47, without 41 | 2^17 |
| A083518 | 19 | to 53, without 41 | 2^17 |
| A083519 | 11 | to 23 | 2^20 |
| A083519 | 12 | to 29 | 2^20 |
| A083519 | 13 | to 23, and 31 | 2^19 |
| A083519 | 14 | to 37 | 2^19 |
| A083519 | 15 | to 37 | 2^17 |
| A083519 | 16 | to 43, without 41 | 2^17 |
| A083519 | 17 | to 43 | 2^18 |
| A083519 | 18 | to 47 | 2^17 |

(A prime the wheel declines is not skipped: it is sieved instead.) A full
run has no stopper. The condition that would decide index n + 1 is
a(n+1)·a(n) + 2, and a(n) is the find itself, so there is no factor witness.
What bounds the claim is the sweep below it. G9 pins the GPU stream to the
CPU engine bit for bit on 26 populated windows, and every find was re-sieved
by the CPU engine at a different depth.

## The finds against the model

`E` is the number of hits the model expected between the floor the sweep
started at and the term that occurred, given the real prefix. If the
intensity is right it is a draw of Exp(1), mean 1. The model's medians below
are recomputed on the **real** prefix. The table written before the run
(README, `model_results.json`) had only one real row per family, and every
later row of it stood on stand-in terms.

| n | A083518: E | quantile | a(n) / median | | n | A083519: E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| 14 | 0.53 (from 2.66·10^11) | 0.41 | 0.71 | | 11 | 0.89 | 0.59 | 1.28 |
| 15 | 0.19 | 0.17 | 0.19 | | 12 | 0.22 | 0.20 | 0.28 |
| 16 | 0.78 | 0.54 | 1.19 | | 13 | 1.87 | 0.85 | 4.22 |
| 17 | 0.42 | 0.34 | 0.51 | | 14 | 0.07 | 0.07 | 0.15 |
| 18 | 0.41 | 0.34 | 0.49 | | 15 | 2.71 | 0.93 | 6.96 |
| 19 | 1.13 | 0.68 | 1.95 | | 16 | 2.75 | 0.94 | 5.26 |
| | | | | | 17 | 0.38 | 0.32 | 0.55 |
| | | | | | 18 | 0.80 | 0.55 | 1.21 |

Pooled over the fourteen draws, **E sums to 13.15, a mean of 0.94**, at
P = 0.44 under its Gamma(14, 1) law: the intensity is right. With G11's nine
published draws (sum 7.79) the twenty-three draws sum to 20.94, P = 0.35.
Per family, A083518 averages 0.58 over 6 (P = 0.14, its terms a little
early) and A083519 1.21 over 8 (P = 0.75). The draws scattered as Exp(1)
does: A083519's a(15) and a(16) landed at the 93rd and 94th percentiles,
5–7× their medians, which is why its a(15) took 25 s where the table had
priced under 5, while its a(14) landed at the 7th. A083518's a(14) is
scored from the entry's 2.66·10^11, the only floor a draw from that row can
be conditioned on; from a(13) it reads E = 0.62. Both long legs landed
inside the interquartile range: a(19) of A083518 at 1.95× its median and
a(18) of A083519 at 1.21×.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags. The
campaign rate is the line from a(n−1) to a(n) over the leg's wall clock, so
it understates the engine: the leg also sweeps the rest of the find's
segment and verifies the find. For the filter each campaign was stopped in,
the rate is the launches swept over the wall clock since the last find, the
engine's build and the pool's resizing included.

| family, filter | engine | line swept | wall clock | campaign rate, a(n)-line/s | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md); * = priced on a stand-in filter) |
|---|---|---|---|---|---|
| A083518 n = 14..17 | v2 | 9.4e16 | 46 s for four finds | — | under 2 s to 34 s* each |
| A083518 n = 18 | v2 | 3.6e18 | 4.3 min | 1.4e16 | 1.7e16* |
| A083518 n = 19 | v2 | 5.1e20 | 6.34 h | 2.3e16 | 2.7e16* |
| A083518 n = 20, stopped in segment 1 | v2 | 2.9e20 | 1.96 h | 4.1e16 | 4.0e16* (v2); 4.6e16 measured on v3 at this real filter |
| A083519 n = 11..15 | v3 | 1.2e17 | 61 s for five finds | — | under 5 s* each |
| A083519 n = 16 | v3 | 4.5e18 | 4.0 min | 1.9e16 | 2.6e16* (v2), 4.4e16* (v3) |
| A083519 n = 17 | v3 | 1.5e19 | 7.7 min | 3.3e16 | 4.6e16* (v2), 5.6e16* (v3) |
| A083519 n = 18 | v3 | 1.3e21 | 6.23 h | 5.9e16 | 7.2e16* (v2), 8.9e16* (v3) |
| A083519 n = 19, stopped in segment 1 | v3 | 1.5e20 | 25 min | 9.7e16 | 1.2e17* (v2), 1.5e17* (v3) |

A083518 ran at 0.84× its stand-in price on the a(19) leg and at 1.04× on
the filter for a(20), where the real filter planned the wheel to 59 without
41 and the stand-in had planned it to 53. **A083519 ran at about 0.67× its
v3 price on every filter past the openings**, a(16) through the filter for
a(19), where its real filters planned the same wheels as the stand-ins. The
A083519 campaign shared the desktop GPU for the whole of its run (ambient
load moves absolute rates by about 30% here, OPTIMIZATION.md rule 3), and
whether the gap is the machine or the plan was not measured. It is the first
thing to measure when the family resumes ("What is open now").

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths). The run of a
survivor, a candidate for a(n), is in index units: the family's offset plus
the number of leading conditions a(off)·a(n) + 2, a(off+1)·a(n) + 2, … that
are prime, capped at the filter. The offset is 1 for A083518 and 0 for
A083519, so a run of 0 in A083519 means a(n) + 2, its product with a(0) = 1
plus two, is composite.

    A083518   8: 508167  9: 197314  10: 69740  11: 25466  12: 8485  13: 2568
              14: 784  15: 233  16: 60  17: 23  18: 5  19: 1
                                           near 14   survivors 643,006,428
    A083519   8: 237608  9: 86184  10: 30218  11: 9150  12: 2794  13: 822
              14: 210  15: 52  16: 10  17: 2  18: 1
                                           near 18   survivors 565,480,727

A run one short of the open term got a `[NEAR]` line and was verified as a
health check. Everything shorter is a count and nothing else. Each extra
rung costs a factor of 2.6–3.9 through run 15 on both families. These are
counts of *sieve survivors*, not densities. A filter-n sieve removes a
candidate whose later conditions have a small factor, so the counts are
comparable within a campaign and not across filters. When a find lands, the
survivors of its segment that lie past it are dropped uncounted: they were
classified without the condition the find creates, and they are swept again
and counted once under the new filter.

## What is open now

**PAUSED — open to others.** Nothing is running. Both campaigns were stopped
by the owner inside the first segment of the filter for their open term,
A083518 1.96 h after a(19) and A083519 25 min after a(18). Neither claims
coverage past its last term: a find restarts the sweep at itself, and the
coverage cursor of a segment moves only when the segment closes. So the
floor for each open term is the definition's, a(n) > a(n−1), and the work
cursor saved in each checkpoint (the launch index inside the open segment)
is what a resume continues from.

| entry | frontier (this project's) | open next | filter | median, on the real prefix | P90 | at the last filter's campaign rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|
| A083518 | **a(19) = 517,222,792,129,337,171,163** | a(20) | n = 20, wheel to 59 without 41, wide | 1.17e22 | 5.65e22 | 7.2 days at 4.1e16 a(n)-line/s (6.4 on v3's 4.6e16) | 25% / 72% / 98% |
| A083519 | **a(18) = 1,352,093,682,658,200,396,075** | a(19) | n = 19, wheel to 53, wide | 4.81e22 | 2.35e23 | 11.3 days at 9.7e16 | 16% / 56% / 91% |

(`plus2_model` on the real prefix, rerun 2026-10-02 in a scratch process:
the finds registered, nothing written. "Days" is the model's expected line
to a *confirmed* find, 2.58e22 and 9.42e22, over the rate the open filter
actually ran at before it was stopped. The terms after those, projected on
stand-ins: A083518's a(21) median 6.1e23, A083519's a(20) 1.9e24, each
about two months at these rates. `model_results.json` is the table stated
before the run and stays as the record.)

**Both open terms are about a week each**, with A083518's the better bet.
The lever priced for them is engine v3's own list (OPTIMIZATION_LOG.md round
3, "Priced and unbuilt"): the planner's width curve re-fit on v3 first.

**Resuming.** Nothing new is needed to be correct: `python launch.py`
continues A083518 at n = 20 and `python launch.py --family A083519`
continues A083519 at n = 19, from the cursors above with census and finds
intact. The A083518 checkpoint was written by engine v2 and is accepted by
v3 at its launch (OPTIMIZATION_LOG.md round 3, "The cursor"), so its first
`[STAGE]` line says the cursor was inherited and nothing is re-swept.
**Whoever resumes runs `python launch.py --selftest` and `python score.py`
first** (CLAUDE.md rule 2). Owed before either is offered again:

- the fourteen finds into the oracle's `FOUND`, so that G1b re-derives them
  from the definition and a fresh clone opens at the new frontier rather
  than at a(14) and a(11). The offset drill and `open_n` are keyed to the
  published list, so this is a launcher change, not a table edit, and it was
  not made at the pause. Until it is, the frontier lives in the checkpoints
  (and in this file), and a fresh clone without them re-derives every term
  from the published frontier, which costs the 15 hours above;
- a frozen benchmark shape at each live filter, A083518 n = 20 and A083519
  n = 19 (rule 5g: the shapes are at the openings, n = 14 and n = 11; a
  shape at a wide filter cannot be a whole segment, which is 45 h there, so
  it needs a launch-denominated shape);
- a paired measurement at those filters against the campaign's own rate,
  which settles A083519's 0.67× and replaces the stand-in prices above.

Where each campaign stands is read with `python launch.py --status` and
`python launch.py --status --family A083519`, which touch nothing.

## The OEIS entries

None of the fourteen terms is entered yet: the 2026-10-02 export (A083518
revision #15, A083519 revision #24) still ends A083518 at a(13) and A083519
at a(10). Nothing is submitted from inside the pipeline (CLAUDE.md rule 5).
`oeis_terms` in each evidence file is what to submit, keyed by the entry's
own OEIS index: A083519's first new term is **a(11)**, not a(12). A083518's
comment "Next term is > 266\*10^9" is superseded by a(14) itself, and its
"Conjecture: sequence is finite" now has nineteen terms against it. Two
notes for the submission: A083518's revision #15 (Feb 2026) added no %E
line and the local export's history begins on 2026-09-01, so
oeis.org/A083518/history should be read before submitting in case a term
was announced anywhere but %S; and A083519's own %e line says "a(4) = 9"
where by its %O line 9 is a(3).
