# Benchmarks — difference-ladders

`python score.py` prints a SCORE only when every gate is green AND every
frozen benchmark shape reproduces its work fingerprint exactly (survivor
count and xor of the surviving b). The SCORE is the END-TO-END line of the
term swept per second at the headline shape, in millions of b per second.
The headline sits at a day-long filter (CLAUDE.md 3b): **A216666's n = 11**,
whose term the model puts six months away at the measured rate, at
b = 3·10²¹, inside that search. Every campaign shape is the configuration
the launcher plans at its filter (the families-stay-apart drill holds them
to it), with the device Fermat stage on its five forms, at a pinned launch
decomposition and a frozen height, and is timed over EXACTLY its 16
launches (engine v2's `max_launches`; see the protocol note below).

## The ledger

| date | engine / planner | SCORE | what changed |
|---|---|---|---|
| 2026-11-23 | v1 / p1 | **132,111,633** | first frozen reading (OPTIMIZATION_LOG.md round 0): cyclotomic-ladders' engine v2 with this project's kill sets and Fermat arithmetic; PRP_FORMS = 5 measured; the heap the gates leave frozen before the shapes run |
| 2026-11-23 | v1 / p1 | 131,787,735 | the same code at the end of the session (the certificate route's complete quadratic factoring and one more canary added; no engine change): every fingerprint reproduced, 0.998 of the first reading |
| 2026-11-23 | v2 / p2 | **198,578,537** | round 1: the sieve set chosen by kill value to 32768 with its primes past 8192 hash-tested, the Fermat stage on its own stream with three launch buffers and squarings by a squaring, the in-block rounds' item loop rolled up past a budget, TAIL_ROUND_DROP 0.8, SIEVE_TAU 6.2·10⁻⁴; the campaign shapes re-frozen (a different sieve set, so a different stage stream) and timed by the exact-launch protocol. **1.507 of the ledger's last row = 1.415 (the engine, paired) × 1.063 (the protocol)**, both measured at the SCORE shape |

The first full score.py run of 2026-11-23 read 120,006,410 with every
fingerprint reproduced: the shapes ran 1.1x to 5x under their fresh-process
rates because Python's collector was walking the gates' leftover heap
between launches; `gc.freeze()` after the gates removed it (round 0). That
reading is not a ledger row: it measured the battery, not the engine. The
same session's first readings on v2 (SCORE 199,143,716, anchors at a third
of their rates) are not a row either: the gates had walked the card's 24 GB
through CuPy's cached blocks, WDDM paged, and every shape timed after them
ran in a degraded context until the engine stopped allocating its tail
queues before the first launch (round 1).

**The protocol change (Rule 4).** Through v1 a campaign shape broke off the
sweep after its 16 results and closed it with the next launch still in
flight, so the timer held 17 launches' device time for 16 counted; with v2's
three launch buffers it would hold 18. score.py now times exactly 16
(`sweep(..., max_launches=16)`, which stops enqueueing and drains). Measured
at the SCORE shape on the v2 code: v1's configuration (which reproduces v1's
frozen fingerprint exactly) 1.321·10¹⁴ b/s by the old protocol and
1.405·10¹⁴ by the new — **the protocol alone 1.063**; v2 1.766·10¹⁴ and
1.987·10¹⁴ — **the engine alone 1.415** under the new protocol, as the
steady-state A/B measured it.

## The shapes

| label | sequence, filter | height (b) | b/s | candidates/s | role |
|---|---|---|---|---|---|
| **SCORE** | A216666, n = 11 | 3·10²¹ | 1.986×10¹⁴ | 1.015×10¹² | the day-long filter (a(11)) |
| D24 | A216668, n = 24 | 3·10¹⁹ | 2.389×10¹³ | 6.17×10¹¹ | the day-long filter (a(24), p = 89 joins) |
| S9 | A216666, n = 9 | 5.58·10¹⁰ (a(8)) | 4.751×10¹³ | 7.17×10¹¹ | the opening |
| S10 | A216666, n = 10 | 3.7·10¹⁵ (a(9)'s median) | 1.438×10¹⁴ | 8.73×10¹¹ | the first promotion |
| D18 | A216668, n = 18 | 2.89·10¹¹ (a(17)) | 1.067×10¹³ | 4.03×10¹¹ | the opening (n = 19 to 23 sieve the same forms) |
| SCORE2L | A216666, n = 9, (13],(23] | period 600 | 1.031×10¹² | 5.45×10¹⁰ | anchor: two-level wheel, sieve stream |
| SCORE1L | A216666, n = 9, primes to 13 | the same window | 1.555×10¹² | 1.99×10¹¹ | anchor: one-level wheel, identical fingerprint |
| SCORE6 | A216668, n = 6, primes to 13 | 10¹¹ | 3.562×10⁹ | 4.56×10⁸ | anchor: a survivor-heavy filter |

Each campaign shape is the first 16 launches of the segment holding its
height; the opening shapes' segments are period 0, clipped at the engine
floor, which is where each campaign starts. Rates are medians of three or
five timed runs after one warm-up, on an RTX 4090. The anchors sieve every
prime to their own depth with no Fermat stage; SCORE6 runs 6% slower than
its v1 configuration at TAIL_ROUND_DROP 0.8, which every campaign filter
measured faster (round 1) — the campaigns decide.

Paired against engine v1's configuration on the same code, steady state
(round 1): A216666 n = 9 **1.328**, n = 10 **1.329**, n = 11 **1.415**;
A216668 n = 18 **1.692**, n = 24 **1.511**.

## The frozen fingerprints

The campaign shapes were RE-FROZEN 2026-11-23 on engine v2 / planner p2:
v2 sieves a different set of primes (the value rule), so different values
reach the Fermat stage and its stream is a different, equally correct one
(G24 pins it to the CPU engine sieving the same set, filtered by the CPU
Fermat chain); three runs each, identical. The anchors' streams do not
depend on the selection and reproduce their v1 fingerprints unchanged.

| label | count | xor | (tchunk, nu, pb) |
|---|---|---|---|
| SCORE | 834 | 29662494119915843287 | (46592, 1, 256) |
| D24 | 1641 | 30553643201573126792 | (4096, 1, 256) |
| S9 | 11238 | 134500289900383 | (253440, 1, 256) |
| S10 | 4310 | 248479526521910636 | (13696, 1, 256) |
| D18 | 16216 | 39174857474391 | (164480, 1, 256) |
| SCORE2L | 6242 | 974192456 | — |
| SCORE1L | 6242 | 974192456 | — |
| SCORE6 | 9549 | 100006044018 | — |

The v1 campaign fingerprints, reproduced exactly by v1's configuration on
the v2 code: SCORE 1965 / 3005121492909293006085, D24 3199 /
30921444358059622733, S9 19004 / 157274159624077, S10 8499 /
266833324717289126, D18 28424 / 4413080787833. With six Fermat forms on
A216666 (round 0) the v1 shapes read SCORE 64 / 102678456802151546, S9 762
/ 91641827133104 and S10 273 / 473949784540348575 — a different workload,
recorded and not frozen.

## Wall clock at the measured rates

From the model's quantiles (README) at the rates above; A229073 rides
A216666's line and costs nothing extra.

| term | rate used | Q1 | median | Q3 | P90 |
|---|---|---|---|---|---|
| A216666 a(9) | S9 4.75×10¹³ b/s | 23 s | 77 s | 3 min | 6 min |
| A216666 a(10) | S10 1.44×10¹⁴ | 3.1 h | 9.7 h | 24 h | 1.9 days |
| A216666 a(11) | SCORE 1.99×10¹⁴ | 60 days | 6.1 months | 15 months | 2.4 years |
| A216668 a(18) | D18 1.07×10¹³ | 3 min | 10 min | 26 min | 51 min |
| A216668 a(24) | D24 2.39×10¹³ | 4 days | 14 days | 34 days | 64 days |

Under engine v1 the medians were 13.7 hours, 9.2 months and 22 days. The
survey that chose this cluster assumed 5·10¹² candidates a second (about
1.3·10¹⁵ b/s at A216666 n = 11); the engine now measures 4·10¹¹ to 1.0·10¹²
on these filters, so every clock above is still five to twelve times the
survey's. Where the time goes is OPTIMIZATION_LOG.md round 1's termination
table.
