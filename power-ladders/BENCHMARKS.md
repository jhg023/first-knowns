# BENCHMARKS — power-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

`python score.py` prints a SCORE only when every gate is green and all
nine frozen shapes reproduce their fingerprints (survivor count + xor of
the surviving terms). The rate is line of the term per second — m/s on
A229626, A229630 and A229902, q/s on A229627 — divided by 10⁶. The six
campaign shapes run the DEVICE FERMAT STAGE on six conditions, so their
fingerprint is the stream the campaign classifies; the three anchors are the
sieve's stream.

## Frozen shapes

| label | family, filter | configuration | fingerprint |
|---|---|---|---|
| SCORE | A229626, n = 10 | unit 1, wheel {3..31 less 19, 29},{47,73},{89}, sieve 2¹³, 128 periods, 3 third-level residues of the segment holding a(9) | 2,695 / 7,609,207,792,066,970 |
| S229627 | A229627, n = 9 | 1 (mod 6), {5..23},{31,41},{47}, 256 periods, 16 residues (2 a launch) | 607 / 684,580,967,501,399 |
| S229630 | A229630, n = 9 | the semiprime wheel and its cofactor sieve (plan p3): {2..31 less 19, 29},{47},{73} in four branches, 128 periods, the whole segment above a(8) (4 + 4 + 2 + 1 launches) | 1,439 / 98,230,428,482,451 |
| S229630L | A229630, n = 11 | plan p3 at the live filter: {2..23},{31,41,47},{73,89}, 128 periods, period 643 (m = 5.567×10¹⁹), 16 + 32 + 1 + 1 launches | 1,448 / 1,935,969,150,529,959,824 |
| S229902 | A229902, n = 9 | 0 (mod 10), {3,7,11,13,17,23,43},{47}, 5,120 periods from a(8)'s | 1,440 / 109,687,303,892,984 |
| S229902L | A229902, n = 10 | 0 (mod 10), {3,7,..,23,43},{47,61},{83}, 2 residues | 1,081 / 11,208,449,253,174,586 |
| SCORE2L | A229626, n = 10 | x space, two-level (19],(31], sieve 2¹⁶, 24 periods from 600 | 455,547 / 118,758,903,108,175 |
| SCORE1L | A229626, n = 10 | x space, one-level to 19, the IDENTICAL window (24 × 20,677 periods) | 455,547 / 118,758,903,108,175 |
| SCORE6 | A229626, n = 6 | x space, one-level to 13, sieve 2¹², 40,000 periods from 3,330,003 | 234,204 / 3,906,727,894 |

S229627 was re-frozen once, in round 2 (OPTIMIZATION_LOG.md): Q3_GUARD
cuts A229627's launch to two third-level residues, so its shape moved from
15 residues (5 a launch; 567 / 2,405,446,072,873,901) to 16. S229630 was
re-frozen in round 5, when A229630's plan became the semiprime wheel. It
had been the v1 plan at 256 periods, 18 residues: 3,292 /
126,589,983,770,433. The new stream is the v1 plan's over the same
segment, filtered by `semi_wheel_ok` (2,899 of 10,276). Its unit is
launches of each branch, and its line is the candidates they hold over the
wheel's density. S229630L was added then, at the live filter (CLAUDE.md
3b). Both were re-frozen in round 6, when A229630's plan became the
cofactor sieve (p3). S229630 had been p2's 2,899 / 129,999,116,256,352
over the whole segment, and its new stream is that one filtered by
`semi_cofactor_ok`, value by value (1,439 of 2,899). S229630L had been 48 +
2 + 1 launches of p2's branches (1,858 / 13,980,745,673,987,437,778).
Every other fingerprint is the one frozen on engine v1's first build:
rounds 1–6 changed how the survivors are computed, never which, except
where a plan change re-froze a shape.

## Ledger

| date | engine | SCORE | S229627 | S229630 | S229902 | S229902L | note |
|---|---|---|---|---|---|---|---|
| 2026-10-15 | v1 as built (round 0) | 172,956,389 | 1,702,509,360 | 23,856,020 | 267,912,211 | 357,500,134 | 58/58 green |
| 2026-10-15 | v1, rounds 1–2 | 248,479,451 | 2,489,084,658 | 66,667,796 | 353,912,953 | 1,253,205,300 | Q3_GUARD, 64-prime rounds, generated tail, launch bound |
| 2026-10-15 | v1, rounds 1–3 | 220,732,526 | 2,182,164,908 | 58,986,476 | 313,311,995 | 1,128,512,619 | + fast R mod N (1.018 paired); this run ~10% low across every shape, the Fermat-free anchors included (SCORE2L 14.4 M against 15.5 M) — ambient, not the change |
| 2026-10-16 | v1, round 4 | 251,481,952 | 2,525,752,354 | 68,012,032 | 364,525,874 | 1,285,649,358 | Fermat limbs from the exact top value + census counted at the drain; every fingerprint reproduced, 58/58 green. These shapes are the openings, where neither change reaches (priced 0.2–0.6% and 0.3–2% at the day-long filters, unmeasured); the headline shape at the day-long filter is owed (OPTIMIZATION.md Rule 0a) |
| 2026-10-19 | v1, round 5: A229630 on plan p2 | 240,480,484 | 2,418,638,413 | 250,319,769 | 363,546,501 | 1,248,385,545 | the SEMIPRIME WHEEL. S229630 is re-frozen on it (a new shape, not comparable to the column above it). S229630L, new at the live filter n = 11: 2,196,302,061 (2.20×10¹⁵ m/s, inside the paired A/B's 2.10–2.29×10¹⁵). Every fingerprint reproduced, 61/61 green. This run was ambiently low: the anchors, on paths nothing touched, read SCORE2L 14.3 M, SCORE1L 20.3 M, SCORE6 14.5 k against 16.0 M, 26.5 M and 20.1 k the same day before the change |
| 2026-10-20 | v1, round 6: A229630 on plan p3 | 219,201,766 | 2,132,928,144 | 356,185,606 | 310,513,742 | 1,115,360,617 | the COFACTOR SIEVE. S229630 and S229630L re-frozen on it. S229630L: 2,343,788,628 (2.34×10¹⁵ m/s). Its ratio to round 5's reading (1.07) is not the engine's. The unit changed: four branch sweeps from the segment's start, each paying an unpipelined first launch. The paired steady-state A/B, 1.30, is the record (OPTIMIZATION_LOG.md round 6). Every fingerprint reproduced, 61/61 green. The anchors read SCORE2L 14.3 M, SCORE1L 24.6 M, SCORE6 18.4 k: an ambient-low run, which is also why SCORE and the other shapes nothing touched read 5–11% under round 5 |
| 2026-10-20 | v1, round 7: WINDOW_ALIGN = 2 | 217,869,003 | 2,166,112,918 | 355,279,033 | 313,544,373 | 1,077,432,409 | the plain window table read aligned, 64 bits at a time, chosen at the day-long filters (1.03–1.09 there, OPTIMIZATION_LOG.md round 7). S229630L 2,513,075,219 (1.07 on the round before). These shapes are the openings, where round 2 priced the read at 0.97–1.0: SCORE 0.99, S229902L 0.97. Every fingerprint reproduced, 61/61 green. Anchors SCORE2L 15.7 M, SCORE1L 25.2 M, SCORE6 17.7 k |

Rounds 1–3 against round 0 on the campaign shapes: 1.28–1.44x on SCORE,
1.28–1.46x on S229627, 2.5–2.8x on S229630, 1.17–1.32x on S229902 and
3.2–3.5x on S229902L (the range is the two runs). The paired measurements
behind each change are in OPTIMIZATION_LOG.md, and they — not this table —
are the record of what each change is worth.

## Wall clock at the measured rates

The campaign engine at every filter it opens at or promotes into, three
interleaved rounds each (OPTIMIZATION_LOG.md, "Measurements at every
filter"), and the clock to each open term's model median from its floor:

| family | filter | rate | values/s to the host | clock to the median |
|---|---|---|---|---|
| A229626 | 10 | 2.36×10¹⁴ m/s | 1,985 | 44 s |
| A229626 | 11 | 4.98×10¹⁴ m/s | 845 | 2.4 h |
| A229626 | 12 | 1.54×10¹⁵ m/s (aligned window read 1.032) | 239 | 19 days |
| A229627 | 9 | 2.68×10¹⁵ q/s | 992 | 5 s |
| A229627 | 10 | 8.46×10¹⁵ q/s | 278 | 14 min |
| A229627 | 11 | 1.67×10¹⁶ q/s | 62 | 2.3 days |
| A229630 | 9 | 6.60×10¹³ m/s (v1; the semiprime wheel not re-measured at a filter of seconds) | 4,239 | 8 s |
| A229630 | 10 | 1.27×10¹⁵ m/s (cofactor sieve, 1.09x the semiprime wheel there, itself 3.84x v1) | — | 4 min |
| A229630 | 11 | 3.1×10¹⁵ m/s (aligned window read 1.057 × cofactor sieve 1.30 × the semiprime wheel's 2.25×10¹⁵, itself 3.69x v1) | 220 | 11 h from the floor; ~25 h to a confirmed find from the live cursor |
| A229630 | 12 | 8.3×10¹⁵ m/s (aligned read 1.067 × cofactor sieve 1.28 × the semiprime wheel, itself 3.94x v1) | — | (the term after a(11)) |
| A229902 | 10 | 1.23×10¹⁵ m/s | 1,488 | 95 s |
| A229902 | 11 | 2.72×10¹⁵ m/s | 636 | 4.4 h |
| A229902 | 12 | 4.58×10¹⁵ m/s | 248 | 35 days |
