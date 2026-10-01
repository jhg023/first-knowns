# RESULTS — product-cliques

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Eleven terms: a(16)–a(19) of A034881 and a(12)–a(18) of A219761.** Found
2026-09-29 to 2026-10-01 by one campaign per family, `python launch.py` and
`python launch.py --family A219761`, no flags, engine v2 with planner p3. The
first advance on either entry since 2012: A034881's last terms were Don
Reble's a(14)–a(15) of October 2012, and A219761's were Robert G. Wilson v's
a(10)–a(11) of December 2012.

Each evidence file was re-verified from disk on 2026-10-01 by a harness that
shares nothing with the launcher: the prefix matched to the OEIS data (the
2026-10-01 export) plus this project's earlier finds, a(n) > a(n−1), every
condition recomputed from the bare definition — a(n)·a(i) + 1 for every
earlier term, and a(n)² + 1 in A219761 — and tested with sympy's `isprime`,
every value's certificate re-verified by `huntlib.certificate.verify` and
matched to its value, the `least_claim` range matched to the prefix, and each
ledger matched to its files. **11 files, 171 certificates, all green**: 79
BLS75 Theorem 1 on a completely factored N − 1, and 92 deterministic
Miller–Rabin below 3.317e24. Nothing is `unproved`. The largest value proved
is A219761's a(18)² + 1, 44 digits; A034881's largest is a(18)·a(19) + 1, 42.

Every file also carries the three-way verification (huntlib's Miller–Rabin
chain, sympy's BPSW, a re-sieve by the CPU engine at a different depth), the
oracle's re-derivation against the whole prefix, and a `least_claim`. Times
below are the ledger's, local; a *leg* is the wall clock from the previous
find (or the campaign's start) to this one, its verification and the
promotion to the next filter included.

### A034881 — one campaign, 2026-09-29 14:52 to 22:52 (8.00 h), from a(15) = 18,216,437,241,240

| n | a(n) | found | leg |
|---|---|---|---|
| 16 | 23,428,808,078,503,956 | 09-29 14:52:27 | 10 s |
| 17 | 3,147,178,220,692,870,716 | 09-29 14:54:17 | 110 s |
| 18 | 247,669,863,444,798,832,776 | 09-29 16:08:51 | 1.24 h |
| 19 | 2,412,240,527,764,607,793,810 | 09-29 22:51:12 | 6.71 h |

a(16) is 17% above the entry's comment "a(16) > 2·10^16". The campaign did
not start from the comment: it swept from a(15) + 1, so the comment is now
re-established as well as superseded.

### A219761 — one campaign, 2026-09-29 22:52 to 2026-10-01 17:59 (43.12 h), from a(11) = 7,746,764,190

| n | a(n) | found | leg |
|---|---|---|---|
| 12 | 2,813,127,048,186 | 09-29 22:52:58 | 6 s |
| 13 | 12,023,634,382,260 | 09-29 22:53:09 | 12 s |
| 14 | 3,855,909,921,391,056 | 09-29 22:53:19 | 10 s |
| 15 | 19,494,730,875,153,690 | 09-29 22:53:31 | 12 s |
| 16 | 159,274,925,587,504,080 | 09-29 22:55:14 | 103 s |
| 17 | 1,912,285,521,658,468,320 | 09-29 22:56:37 | 83 s |
| 18 | 8,981,486,409,894,740,569,620 | 10-01 17:59:43 | 43.05 h |

Evidence: `evidence/<entry>_a<n>_<a(n)>.json`, one per term, and one ledger
per family, `evidence/a<number>_discoveries.json`.

**What the early terms are worth**, as the README said before the run:
A219761's a(12)–a(17) took four minutes between them, and A034881's
a(16)–a(17) two. They stood since 2012 because nobody returned to these
entries, not because they were hard. The hunt proper was A034881's a(18)
and a(19) and A219761's a(18).

### The least-claim basis

Each file's `least_claim` is the sweep from a(n−1) + 1 to a(n) under the
filter of index n: every condition of that index, in the forced class
a(n) ≡ 0 (mod 6). That class is a theorem from a(3) on (README, "the
mathematics of the engine"), and every term here is in it. The floor is
a(n−1) because the definition requires a(n) > a(n−1). No entry carried a
searched bound except A034881's comment on a(16), and the campaign did not
rely on it. The wheel and the sieve depth were planned per filter:

| entry | n | wheel primes past 2 and 3 | sieve depth |
|---|---|---|---|
| A034881 | 16 | to 37 | 2^17 |
| A034881 | 17 | to 41 | 2^17 |
| A034881 | 18 | to 47, without 43 | 2^17 |
| A034881 | 19 | to 53, without 43 | 2^17 |
| A219761 | 12 | to 29 | 2^20 |
| A219761 | 13 | to 37, without 31 | 2^20 |
| A219761 | 14 | to 41, without 31 | 2^19 |
| A219761 | 15 | to 41 | 2^18 |
| A219761 | 16 | to 47, without 43 | 2^17 |
| A219761 | 17 | to 47, without 43 | 2^18 |
| A219761 | 18 | to 53, without 43 | 2^17 |

(A prime the wheel declines is not skipped: it is sieved instead.) A full
run has no stopper. The condition that would decide index n + 1 is
a(n+1)·a(n) + 1, and a(n) is the find itself, so there is no factor witness.
What bounds the claim is the sweep below it. G9 pins the GPU stream to the
CPU engine bit for bit on 24 populated windows, and every find was re-sieved
by the CPU engine at a different depth.

## The finds against the model

`E` is the number of hits the model expected between the floor the sweep
started at and the term that occurred, given the real prefix. If the
intensity is right it is a draw of Exp(1), mean 1. The model's medians below
are recomputed on the **real** prefix. The table written before the run
(README, `model_results.json`) had only one real row per family, and every
later row of it stood on stand-in terms.

| n | A034881: E | quantile | a(n) / median | | n | A219761: E | quantile | a(n) / median |
|---|---|---|---|---|---|---|---|---|
| 16 | 0.08 (from 2·10^16) | 0.07 | 0.42 | | 12 | 1.13 | 0.68 | 2.06 |
| 17 | 1.67 | 0.81 | 3.29 | | 13 | 0.18 | 0.17 | 0.22 |
| 18 | 2.43 | 0.91 | 5.03 | | 14 | 1.43 | 0.76 | 2.78 |
| 19 | 0.66 | 0.48 | 0.95 | | 15 | 0.26 | 0.23 | 0.34 |
| | | | | | 16 | 0.10 | 0.10 | 0.09 |
| | | | | | 17 | 0.05 | 0.05 | 0.03 |
| | | | | | 18 | 1.56 | 0.79 | 3.07 |

Pooled over the eleven draws, **E sums to 9.54, a mean of 0.87**, at
P = 0.36 under its Gamma(11, 1) law. That is the intensity about right,
where G11's twelve published draws (a disjoint set, sum 5.79, P = 0.016) had
said terms come early. Per family, A034881 averages 1.21 over 4 and A219761
0.67 over 7. A219761's a(16) and a(17) landed at the 10th and 5th
percentiles, a(17) at 3% of its median, which is why its six cheap terms
cost four minutes where the table had priced 1.5 h for a(17) alone. A034881's
a(16) is scored from the entry's 2·10^16, the only floor a draw from that
row can be conditioned on; from a(15) it reads E = 0.75. Across all
twenty-three draws the mean is 0.67 (P = 0.04): on these two entries the
terms still come a little early against the model, so the open-term medians
below lean conservative.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the ledger timestamps and the checkpoints, per filter, no flags. The
campaign rate is the line from a(n−1) to a(n) over the leg's wall clock, so
it understates the engine slightly: the leg also sweeps the rest of the
find's segment and verifies the find.

| family, filter | line swept | wall clock | campaign rate, a(n)-line/s | the engine at that filter ([BENCHMARKS.md](BENCHMARKS.md); * = priced on a stand-in filter) |
|---|---|---|---|---|
| A034881 n = 16, 17 | 3.1e18 | 2 min | — | 4 s and 65 s* |
| A034881 n = 18 | 2.4e20 | 1.24 h | 5.5e16 | 5.0e16* |
| A034881 n = 19 | 2.2e21 | 6.71 h | 9.0e16 | 8.1e16* |
| A219761 n = 12..17 | 1.9e18 | 3.7 min for six finds | — | under a second to 1.5 h* each |
| A219761 n = 18 | 9.0e21 | 43.05 h | 5.8e16 | 8.0e16* |

A034881's two long legs ran at 1.1× their stand-in prices. **A219761's
n = 18 leg ran at 0.72× its price.** The real filter planned a different
wheel from the stand-in's: to 53 without 43, where the stand-in had planned
the full wheel to 47. Whether the gap is that plan or the machine was not
measured (the GPU is shared with the desktop), and it is the first thing to
measure when the family resumes ("What is open now").

## The census

Counts per run length from each checkpoint, as printed in every `[STATUS]`
line (the finds themselves are included at their run lengths). The run of a
survivor, a candidate for a(n), is 0 if A219761's a(n)² + 1 fails, and
otherwise 1 plus the number of leading conditions a(1)·a(n) + 1,
a(2)·a(n) + 1, … that are prime, capped at the filter:

    A034881   8: 791693  9: 285667  10: 101084  11: 33978  12: 10926  13: 3406
              14: 938  15: 253  16: 76  17: 22  18: 4  19: 1
                                           near 16   survivors 574,909,166
    A219761   8: 531954  9: 170939  10: 55273  11: 16447  12: 5004  13: 1383
              14: 365  15: 108  16: 20  17: 8  18: 1
                                           near 13   survivors 3,104,074,115

A run one short of the open term got a `[NEAR]` line and was verified as a
health check. Everything shorter is a count and nothing else. Each extra
rung costs a factor of 2.8–3.8 through run 15 on both families. These are
counts of *sieve survivors*, not densities. A filter-n sieve removes a
candidate whose later conditions have a small factor, so the counts are
comparable within a campaign and not across filters. When a find lands, the
survivors of its segment that lie past it are dropped uncounted: they were
classified without the condition the find creates, and they are swept again
and counted once under the new filter. A219761 classified 3.1 billion
survivors in 43 hours, 5.4 times A034881's count, over 3.7 times the line.

## What is open now

**PAUSED — open to others.** Nothing is running. Both campaigns stopped
right after a find, A034881 81 s after a(19) and A219761 7 s after a(18).
Neither claims coverage past its last term: a find restarts the sweep at
itself. So the floor for each open term is the definition's, a(n) > a(n−1).

| entry | frontier (this project's) | open next | filter | median, on the real prefix | P90 | at the last leg's campaign rate | P(found) in a day / a week / 30 days |
|---|---|---|---|---|---|---|---|
| A034881 | **a(19) = 2,412,240,527,764,607,793,810** | a(20) | n = 20 | 8.8e22 | 4.3e23 | 11 days at 9.0e16 a(n)-line/s | 10% / 39% / 77% |
| A219761 | **a(18) = 8,981,486,409,894,740,569,620** | a(19) | n = 19 | 1.7e23 | 7.8e23 | 32 days at 5.8e16 | 3% / 18% / 48% |

(`product_model` on the real prefix, rerun 2026-10-01 in a scratch process:
the finds registered, nothing written. The rates are those the last filter
of each campaign actually ran at; the next filter's rate is not measured.
BENCHMARKS.md priced both next filters, on stand-ins, at 1.0e17 a(n)-line/s,
which would make A034881's a(20) about 10 days and A219761's a(19) about 20
days at their medians. `model_results.json` is the table stated before the
run and stays as the record.)

**Both open terms are multi-week.** One lever was priced for them: the full
wheel to 53 at A034881's n = 20, 1.23× on the stand-in filter
(OPTIMIZATION_LOG.md "Priced and unbuilt" 1). That price was set against a
plan that took the full wheel to 47. The real filter already plans the
wheel to 53 without 43, so what the lever is worth now is unmeasured.

**Resuming.** Nothing new is needed to be correct: `python launch.py`
continues A034881 at n = 20, and `python launch.py --family A219761`
continues A219761 at n = 19, from the cursors above with census and finds
intact. **Whoever resumes runs `python launch.py --selftest` and `python
score.py` first** (CLAUDE.md rule 2). Owed before either is offered again:

- the eleven finds into the oracle's `FOUND`, so that G1b re-derives them
  from the definition and a fresh clone opens at the new frontier rather
  than at a(16) and a(12);
- a frozen benchmark shape at each live filter, A034881 n = 20 and A219761
  n = 19 (rule 5g: the shapes are at the openings, n = 16 and n = 12);
- a paired measurement at those filters, which settles A219761's 0.72× and
  replaces the stand-in prices above.

Where each campaign stands is read with `python launch.py --status` and
`python launch.py --status --family A219761`, which touch nothing.

## The OEIS entries

None of the eleven terms is entered yet: the 2026-10-01 export still ends
A034881 at a(15) and A219761 at a(11). Nothing is submitted from inside the
pipeline (CLAUDE.md rule 5). `oeis_terms` in each evidence file is what to
submit. A034881's comment "a(16) > 2*10^16" is superseded by a(16) itself.
