# BENCHMARKS — hl-records (A331940)

> **Authorship disclaimer:** As with the rest of this project, this
> document and the code it describes were authored by **Claude
> (Anthropic's AI)** at the repository owner's direction.

`python score.py` prints a SCORE only if every gate is green and all four
frozen shapes reproduce their fingerprints. The unit is 10^3 k per second
of line swept (odd and even k counted; only odd k cost work). One RTX 4090.

## The frozen shapes

| shape | window | fingerprint (frozen 2026-11-11, engine v3) |
|---|---|---|
| **SCORE** | [3·10^12 + 1, + 2^23 of k): one window at the height that runs for days at engine v3's rate, from the campaign's cursor (a(36)'s median is k = 2.0·10^12, 31 hours in; a(37)'s 5.4·10^12, five days) | count 96, checksum 12884934779942494085505 |
| SCORE_1E12 | [10^12 + 1, + 2^23 of k): engine v2's headline (the day-long height at v2's rate), kept so the ledger compares engines on one shape | count 98, checksum 4294978698595606490122 |
| SCORE_3E11 | [3·10^11 + 1, + 2^23 of k): the round-0 headline shape | count 98, checksum 1288500965751632109998 |
| SCORE_OPEN | [10^8 + 1, + 4·2^23 of k): four windows in the opening band, above the literature's bound a(12) ≤ 99539591 | count 406, checksum 221705018271837759 |
| SCORE_1E14 | [10^14 + 1, + 2^23 of k): past engine v3's ceiling, where every path engine v4 added is in force (16-byte form keys, characters of primes past 5.6·10^6 on the fly, three primes past 251 in RHO_LARGE); frozen 2026-11-12, engine v4 | count 116, checksum 429496743674342754768367 |

A fingerprint is, per window, every survivor of the rule at the census
floor 7.5 as k·2^32 + T (T = 3H(4k − 1), the exact count), two digests of
the counts the sparse count finished, their number, and the number and
position sum of the k the prefilter left; the count is survivors plus
five per window (91 + 5, 93 + 5, 93 + 5, 386 + 20 and 111 + 5). Engine v4
reproduces the first four unchanged: below 2^46 it makes engine v3's
decisions and counts bit for bit (OPTIMIZATION_LOG.md 3.4).

**The shape change, reported apart from the engine change (Rule 4).** The
headline moved from 10^12 to 3·10^12 in the same change as the engine, so
both engines were run on all of these heights, paired and interleaved
(2026-11-11; engine v2's module rebuilt from a copy):

| window | engine v2 | engine v3 | ratio | survivors |
|---|---|---|---|---|
| [10^10 + 1, + 2^23) | 0.386 s | 0.137 s | 2.81 | v3's list inside v2's |
| [3·10^11 + 1, + 2^23) | 1.298 s | 0.316 s | 4.11 | 105 → 93, inside |
| [10^12 + 1, + 2^23) | 2.496 s | 0.461 s | **5.41** | 105 → 93, inside |
| [3·10^12 + 1, + 2^23) | 5.323 s | 0.714 s | **7.45** | 104 → 91, inside |

The survivor lists are engine v1's and v2's less the k the local Euler
factors prove to have C below the floor (the survivor-only xor of the
10^12 list was 4294974074527840453330 under v1, v2 and v3 before those
factors, and is 4294978774605041675611 with them). Every removed k was
classified by the host: 143 removals on 13 windows from k = 3·10^5 to
3·10^12, the largest C 7.45085, the census bins identical on every
window (OPTIMIZATION_LOG.md 2.3). The engine-v2 fingerprints (count 108,
checksum 4294982210140497519528 at 10^12; 108, 1288506849089138728912 at
3·10^11; 460, 14137509344695254 at 10^8) are retired with that engine.

**How the expectation was established.** A second full tabulation of
these windows by the CPU engine is out of reach (a forms sieve costs
O(k) per window: 5·10^10 at 3·10^11). What stands behind the fingerprints:

- the survivor lists are engine v1's, whose own freeze rested on a second
  device layout, on 120 sampled analytic class numbers and on the gates
  below, less the removals classified as above;
- gate P6: the production stream equals the survivor rule applied to
  EVERY counter (the three-squares tabulation, kept in the engine as `h3`)
  on five windows from 10^8 to the ceiling, 1,098 survivors, and every
  count the sparse count finished equals the full tabulation's;
- gate P7: the sparse count (reduced forms by leading coefficient) equals
  the three-squares count on every counter of seven windows from k = 1 to
  the ceiling and 26 neighbourhoods of constructed discriminants —
  16,592 discriminants;
- gate P5: the prefilter's decision equals the CPU reference's (Python
  integers, textbook composition, dictionaries) bit for bit on 4,736 k
  from 2.6·10^5 to the ceiling and 16 neighbourhoods of constructed
  conductors at two floors;
- gate S9: every k the local Euler factors remove from the universal
  rule's survivors is below the floor by the host's rigorous interval;
- below 4·10^9 the CPU engine (reduced forms by a sieve) equals the GPU
  engine counter for counter on six populated windows and its survivors
  equal the production stream (gate P1); the analytic class number
  agrees with sampled counts to 10^14 (P3);
- SCORE_1E14 (engine v4): the whole window [10^14 + 1, + 2^23) was
  tabulated by three squares — every one of its 4,194,304 counters, 174 s
  of walk in two launches — and the production stream equals the rule on
  them (111 survivors), every count the sparse count finished equal to
  the tabulation's; gates P5–P8 carry the same comparisons at 9·10^13 and
  at constructed values of 4k − 1 with k ≈ 10^15, 10^16 and 10^18.

## SCORE ledger

| date | engine | SCORE (10^3 k/s at the headline) | at 10^12 | SCORE_3E11 | SCORE_OPEN (10^8) | gates | note |
|---|---|---|---|---|---|---|---|
| 2026-11-11 | v1, three squares, window 2^22 | — | 480 (paired run; not a score.py shape then) | 891 (first freeze); 975 at the start of round 1 | 44,489; 48,973 | 16 gates, 7 launcher drills and 8 repo drills green | round 0, headline 3·10^11. The ambient swing across the day is about 10% |
| 2026-11-11 | v2, class-group prefilter + flagged tabulation | 3,375 (headline 10^12) | 3,375 | 6,489 | 66,102 | 20 gates (S7, S8, P5, P6 new), 7 launcher drills and 8 repo drills green | round 1: 6.83× / 7.32× / 1.51× paired on the three shapes of the time; the cursor key is new and accepts v1's (identical line) |
| 2026-11-11 | **v3, local Euler factors + prefilter in the fundamental discriminant + sparse exact count** | **11,777** (headline 3·10^12) | 18,306 | 26,514 | 136,264 | 22 gates (S9, P7 new), 8 launcher drills (migration new) and 8 repo drills green | round 2, the Codex review tested: 5.41× / 7.45× paired at 10^12 / 3·10^12 (table above); the headline moves to 3·10^12; the cursor key is new (rule=p251-local) and accepts v1's and v2's (identical line, raw survivor count kept apart) |
| 2026-11-12 | **v4, ceiling 10^13 → 10^18 (arithmetic to 4k − 1 < 2^62); confirmations over a burst pool** | **11,921** (11,665 on v3 that morning) | 18,417 | 26,595 | 136,952 | 23 gates (P8 new; S0, P0, P3, P5–P7 extended), 10 launcher drills (confirmation, burst new) and 8 repo drills green | round 3: v3's decisions and counts bit for bit below 2^46 at v3's speed (1.004× / 1.006× paired at 3·10^12 / 10^13); SCORE_1E14 = **1,810** frozen past the old ceiling; the cursor key is new and accepts v3's whole (identical line and rule) |
| 2026-11-12 | **v4.1, membership searched to the known order m1 (not the bound); a float quotient in the reduction of forms** | **17,104** | 24,711 | 35,370 | 165,520 | 23 gates and every drill green (44 checks, 183 s); all five fingerprints reproduced unchanged | round 4, after an Nsight Compute profile of every kernel: v4's decisions bit for bit, 1.318× / 1.408–1.500× paired at 3·10^12 / 7.4·10^12 (the medians of a(36) and a(37) from the cursor), 1.35× at 10^14, 1.14× at 10^8; SCORE_1E14 = **2,600**. score.py keeps the best of three runs, so the SCORE moved more than the paired medians (1.43× against 1.32–1.35×); the paired ratios are the claim. The cursor key is v4's, unchanged (identical line) |

## The rate law, measured (engine v3, 2026-11-11)

Three consecutive production windows at each height (two at the last
two), census floor 7.5:

| k | s per window | k/s | prefilter | sparse count | k counted | v2 s per window |
|---|---|---|---|---|---|---|
| 10^8 | 0.062 | 1.36·10^8 | 0.060 s | 0.002 s | 0.054% | 0.127 |
| 10^9 | 0.090 | 9.33·10^7 | 0.089 | 0.002 | 0.076% | 0.216 |
| 10^10 | 0.139 | 6.05·10^7 | 0.134 | 0.004 | 0.097% | 0.383 |
| 10^11 | 0.239 | 3.51·10^7 | 0.230 | 0.009 | 0.114% | 0.809 |
| 3·10^11 | 0.317 | 2.64·10^7 | 0.301 | 0.015 | 0.123% | 1.300 |
| 10^12 | 0.478 | 1.76·10^7 | 0.439 | 0.038 | 0.126% | 2.530 |
| 3·10^12 | 0.726 | 1.16·10^7 | 0.651 | 0.073 | 0.130% | 5.380 |
| 9.9·10^12 | 1.192 | 7.04·10^6 | 1.039 | 0.149 | 0.137% | 13.59 |
| 3·10^13 (v4) | 2.147 | 3.91·10^6 | 1.813 | 0.334 | 0.140% | |
| 10^14 (v4) | 4.660 | 1.80·10^6 | 3.945 | 0.715 | 0.147% | |
| 3·10^14 (v4) | 8.093 | 1.04·10^6 | 6.490 | 1.603 | 0.148% | |
| 10^15 (v4) | 14.758 | 5.68·10^5 | 11.174 | 3.584 | 0.154% | |

(The v2 column is its own table's, measured in another sitting; the
paired ratios are the table above.  The v4 rows, 2026-11-12, are past
engine v3's ceiling: three consecutive windows at 3·10^13 and 10^14, two
above, median; engine v4 measured 1.185 s at 9.9·10^12 in the same
sitting.  From 10^14 the form table is keyed in 16 bytes (0.76× on the
window where it was forced at 3·10^12) and the giant-step table is full,
so the prefilter goes like k^0.5.) The prefilter grows like k^0.25 and
is nine tenths of the window; the sparse count of the 0.13% it leaves
grows like k^0.5. The local exponent of the window time is 0.16 at 10^9,
0.24 at 10^11, 0.37 at 10^12 and 0.42 at 3·10^12; engine v2's was 0.69
at 10^12 and 0.78 at 3·10^12, which is why the advantage grows with the
height (11× at the ceiling).

## The rate law of engine v4.1 (2026-11-12)

Each point is engine v4's divided by the paired v4 / v4.1 ratio measured
at that height in one sitting (v4 rebuilt from its source beside v4.1;
interleaved whole windows, streams compared on every run: four rounds to
3·10^13, two above), so the law keeps v4's calibration. v4's own windows
that sitting were within 2% of its points below 3·10^14 (0.717 s at
3·10^12, 1.181 at 9.9·10^12).

| k | v4 s per window | ratio | v4.1 s per window | k/s |
|---|---|---|---|---|
| 10^8 | 0.062 | 1.152 | 0.054 | 1.55·10^8 |
| 10^9 | 0.090 | 1.168 | 0.077 | 1.09·10^8 |
| 10^10 | 0.139 | 1.160 | 0.120 | 6.99·10^7 |
| 10^11 | 0.239 | 1.267 | 0.189 | 4.44·10^7 |
| 3·10^11 | 0.317 | 1.275 | 0.249 | 3.37·10^7 |
| 10^12 | 0.478 | 1.273 | 0.376 | 2.23·10^7 |
| 3·10^12 | 0.726 | 1.347 | 0.539 | 1.56·10^7 |
| 9.9·10^12 | 1.192 | 1.437 | 0.830 | 1.01·10^7 |
| 3·10^13 | 2.147 | 1.456 | 1.475 | 5.69·10^6 |
| 10^14 | 4.660 | 1.319 | 3.533 | 2.37·10^6 |
| 3·10^14 | 8.093 | 1.293 | 6.260 | 1.34·10^6 |
| 10^15 | 14.758 | 1.226 | 12.036 | 6.97·10^5 |

`hlc_model.RATE_POINTS` carries the v4.1 column. The gain peaks near
10^13, where the membership launches were the largest share of v4's
window, and falls above it as the first pass of the prefilter (which v4.1
changes only by its quotient) grows like k^0.5.

## Wall clock at the measured law

`hlc_model.clock_seconds` integrates the table above as a power of k
between its points; the model's clocks and the heartbeat's ETA use it.

| swept to k | clock, v4.1 (v4; v2) | what is there (the medians as the model put them at round 4, from a(33) and the cursor 8.03·10^11) |
|---|---|---|
| 10^8 | 0.6 s (0.6 s; 1.2 s) | |
| 10^9 | 8.0 s (9.2 s; 21 s) | |
| 10^10 | 2.0 min (2.3 min; 6.1 min) | |
| 10^11 | 31 min (39 min; 2.0 h) | |
| 3·10^11 | 2.0 h (2.5 h) | |
| 8.03·10^11 | 7.1 h | the cursor at round 4 (a(33) found; 22 new terms) |
| 10^12 | 9.4 h (12 h; 2.3 days) | a(34)'s median 1.02·10^12 |
| 1.66·10^12 | 18 h | a(35)'s median |
| 3·10^12 | 1.7 days (2.2 days) | the SCORE shape |
| 3.19·10^12 | 1.8 days | a(36)'s median: the first day-long term from the cursor (37 h) |
| 3.31·10^12 | 1.9 days | **a(34) found**, 2026-11-14, at the law's 99.97th percentile |
| 4.15·10^12 | 2.6 days | **the pause**, 2026-11-14 (23 new terms; 62.8 h of the owner's campaign clock, on engines v2 to v4.1); a(35)'s median from here 4.51·10^12, 7.3 h on (RESULTS.md) |
| 7.42·10^12 | 5.7 days | a(37)'s median (5.4 days from the cursor) |
| 7.51·10^12 | 5.8 days | Fung and Williams' k = 7514981191031, C = 9.67581: the bound a(35) ≤ it |
| 10^13 | 8.5 days (11.7; 107) | engine v3's ceiling |
| 5.3·10^13 | 100 days (143) | the form table's wide keys from here |
| 10^14 | 288 days (396) | SCORE_1E14 |
| 10^15 | 29 years (37) | |
| 10^18 (ceiling) | ~10^6 years | engine v4's ceiling: 4k − 1 < 2^62 |

Campaign loop against device time, through `launch.Campaign` itself over
30 windows (classification against a standing record of C = 9.32896,
health sampling on, the run's one-time costs included): wall/device =
**1.057 at 10^12 and 1.077 at 3·10^12** (1.01 at 10^12 under v2). Host
classification of ~90 survivors a window is 4.3% and 3.6% of the wall
clock: the device got five to seven times faster and the host did not.
Overlapping it with the next window is priced in OPTIMIZATION_LOG.md 2.11.

**That measurement missed the campaign's real host cost**, because it is
an average over 30 windows and the cost was in the tail: one survivor in
~450 windows fell through to a 30-digit analytic evaluation (four minutes
at k = 10^10, forty at 10^12), about seven times the device time at the
cursor's height, found in the owner's first v3 run (OPTIMIZATION_LOG.md
2.13). Counted after the fix, over 900 windows at the cursor and 400 at
10^12: host classification is 8.7 ms a window (6.1% of device) and 14.3 ms
(3.2%), and the analytic route is reached about once in 900,000 windows,
0.2–0.6% of device time to the ceiling.
