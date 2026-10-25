# Benchmarks — cyclotomic-ladders

> **Authorship disclaimer:** every line of code and documentation in this
> project was authored by **Claude (Anthropic's AI)** at the repository
> owner's direction.

`python score.py` prints a SCORE only when every gate is green and all
frozen benchmark shapes reproduce their work fingerprint (survivor count
and xor of the surviving terms). The rate is line of the term per second —
x/s on both entries — divided by 10⁶. The shapes are score.py's: the
headline at A070737's day-long filter n = 13 (CLAUDE.md 3b), the opening
n = 11 and the promotion n = 12, the five day-long indices of A072942, and
three anchors with no Fermat stage (a two-level and a one-level wheel that
must return the identical fingerprint over the same window, and a filter
with many survivors per unit of line). Each campaign shape is 16 launches
of the segment at the shape's height, at a launch decomposition and width
PINNED with the fingerprint (score.py's SHAPE_TCHUNK), so a later planner
cannot move the workload (Codex CYL-008). A shape's rate includes the
unpipelined first launch of its sweep, so it reads 5–15% under a
steady-state A/B at the same filter; the paired ratios in
OPTIMIZATION_LOG.md are the engine's record (OPTIMIZATION.md Rule 4).

## The ledger

| date | engine | SCORE | S11 | S12 | D60 | D72 | D84 | D90 | D96 | note |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-23 | v1, planner p1 (round 0) | 12.24×10¹² | 0.666×10¹² | 7.33×10¹² | 442×10¹² | 621×10¹² | 23.2×10¹² | 7.67×10¹² | 30.6×10¹² | the engine as inherited (plain aligned window, 168 registers, 3 blocks a SM); one reading per shape (16 launches, no gate battery) with the plan's decomposition of that day: SCORE at 128 periods and tchunk 18304, S12 at 256 periods, D90 at tchunk 27392 — three workloads that differ from the v2 shapes' |
| 2026-10-23 | v2, planner p2 (round 1) | **16,558,034,426,419** | 920,181,695,660 | 8,518,254,378,634 | 549,136,360,704,145 | 742,727,456,177,251 | 27,502,202,085,217 | 9,763,941,622,095 | 35,285,387,855,349 | `python score.py`, exit 0, 30 gates green, every fingerprint reproduced (medians of 3 runs after a warm one); anchors SCORE2L 2,415,950, SCORE1L 14,293,192, SCORE6 3,348,760. The halved window pattern on the pairs layout, the packed x0 and offset table, the Fermat stage by degree, the last tail round generated, every constant re-swept here; SCORE and S12 at 160 periods, SCORE and D90 at the launch size the tail-queue guard leaves |
| 2026-10-24 | v2, planner p3 (round 2) | **16,735,726,507,455** | 737,939,466,560 | 8,118,498,514,728 | 560,244,694,956,896 | 770,621,681,296,689 | 29,390,588,226,680 | 9,625,868,378,403 | 38,441,921,595,321 | `python score.py`, exit 0, 30 gates green, every fingerprint reproduced (the last of four batteries this round, 16.68–16.74×10¹² on the headline); anchors SCORE2L 2,270,762, SCORE1L 12,325,575, SCORE6 2,782,488; `launch.py --selftest` 57/57 green. D60, D72, D84 and D96 now stand at the MEASURED wheels (OPTIMIZATION_LOG.md round 2; new workloads, frozen after the exact CPU parity there), and the p2 workloads of the same indices are kept as D60p2 509,522,570,859,895, D72p2 728,896,817,319,275, D84p2 27,416,324,873,171 and D96p2 35,394,861,358,232 (the same fingerprints as the row above). The rate of every launch-denominated shape now counts the EXACT candidates of its launches, so a shape whose first 16 launches hold a partial first-level chunk reads lower than in the row above by that fraction and not by any engine change: about 0.8 at S11, 0.92 at D60p2, 0.97 at D72p2 (the engine is the same v2; ±3% of ambient on top) |
| 2026-10-25 | v2, planner p3 (the pause battery) | **16,162,789,126,690** | 678,962,715,483 | 7,293,986,470,910 | 514,187,644,571,382 | 734,402,377,568,073 | 28,213,275,637,241 | 9,567,944,011,660 | 38,518,768,822,582 | `python score.py`, exit 0, 30 gates green, every fingerprint reproduced, on the code exactly as in the row above (no engine or planner change since; this is the SCORE of the pause commit): anchors SCORE2L 2,156,268, SCORE1L 10,672,173, SCORE6 2,603,381; p2 workloads D60p2 502,671,137,688,816, D72p2 739,852,521,319,456, D84p2 27,097,575,406,488, D96p2 34,562,963,526,914; `launch.py --selftest` 57/57 green in 255 s. The headline reads 0.966 of the row above on the same engine — the ambient spread this file warns of, one reading against a median of three |

Round 1's shapes as score.py read them (x/s, the SCORE column times
10⁶), the v1 reading of the same shape, and the paired steady-state ratio
of the round's A/B at the same filter where one was taken (the record,
OPTIMIZATION.md Rule 4: a shape pays its first unpipelined launch, and
three of them changed workload with the plan):

| shape | v2 (score.py) | v1 reading, same shape | ratio | steady-state paired ratio (round 1) |
|---|---|---|---|---|
| SCORE (A070737 n = 13) | 1.656×10¹⁹ | 1.224×10¹⁹ at 128 periods | 1.35 (a changed workload) | **1.31** (1.80 against 1.38×10¹⁹, prof.py) |
| S11 (n = 11) | 9.20×10¹⁷ | 6.66×10¹⁷ | 1.38 | 1.8 (1.02 against 0.56×10¹⁸, rates.py) |
| S12 (n = 12) | 8.52×10¹⁸ | 7.33×10¹⁸ at 256 periods | 1.16 (a changed workload) | 1.28 |
| D60 (A072942 n = 60) | 5.49×10²⁰ | 4.42×10²⁰ | 1.24 | 1.23–1.37 |
| D72 (n = 72) | 7.43×10²⁰ | 6.21×10²⁰ | 1.20 | 1.31 |
| D84 (n = 84) | 2.75×10¹⁹ | 2.32×10¹⁹ | 1.18 | 1.27 |
| D90 (n = 90) | 9.76×10¹⁸ | 7.67×10¹⁸ at tchunk 27392 | 1.27 (a changed workload) | 1.35 |
| D96 (n = 96) | 3.53×10¹⁹ | 3.06×10¹⁹ | 1.15 | 1.25 |

Round 2's shapes (planner p3, 2026-10-24): the measured wheel of each
index against its p2 wheel in the same battery (both read with the exact
candidate count, the first launch of each unpipelined), and the paired
steady-state ratio of round 2's A/B at x = 3 / at the model's median (the
record):

| shape | p3 wheel (score.py) | p2 wheel, same battery | ratio | paired ratio (round 2) |
|---|---|---|---|---|
| D60 (A072942 n = 60) | 5.60×10²⁰ | 5.10×10²⁰ (D60p2) | 1.10 | **1.093 / 1.073** |
| D72 (n = 72) | 7.71×10²⁰ | 7.29×10²⁰ (D72p2) | 1.06 | **1.060 / 1.070** |
| D84 (n = 84) | 2.94×10¹⁹ | 2.74×10¹⁹ (D84p2) | 1.07 | **1.071 / 1.042** |
| D96 (n = 96) | 3.84×10¹⁹ | 3.54×10¹⁹ (D96p2) | 1.09 | **1.099 / 1.074** |

(A shape's single reading moves ±5% with the unpipelined first launch
and the ambient clock — the batteries of this round read the D96 pair at
1.09, 1.11 and 1.14; the paired ratios are the record.)

## The frozen fingerprints

score.py's `FROZEN` holds them, one (count, xor) per campaign shape, with
`SHAPE_TCHUNK` the (tchunk, nu, pb) each was frozen at, and the anchors' in
`SHAPES`. Frozen 2026-10-23 on engine v2 / planner p2, after G9 pinned the
engine's stream to the CPU engine's on populated windows and every round-1
A/B arm returned the identical stream. The v1 fingerprints of the shapes
whose workload the plan did not move are the same integers (S11 13412,
D60 5447, D72 6622, D84 3916, D96 7056 survivors); where the plan moved
(SCORE: 128 → 160 periods, 22690 survivors over one third-level residue
on v1 against 1530 over 16 launches now; S12; D90) the v1 fingerprint
belongs to a different workload and is not kept. A changed fingerprint is
a changed stream: an engine that does not reproduce them does not ship
(CLAUDE.md rule 3).

Planner p3 (2026-10-24, round 2) moved D60, D72, D84 and D96 to the
measured wheels, so those labels now carry NEW workloads — 5500, 3668,
3143 and 6383 survivors over 16 launches at tchunk 105728, 90880, 48000
and 3200 — frozen after the exact parity of each wheel's campaign engine
against the CPU engine (408–863 launches at the production depth, the
survivors of a 2×10⁷-t window equal launch for launch) and the CPU
re-derivation of every survivor the round's A/Bs emitted; the p2 workloads
keep their 5447, 6622, 3916 and 7056 as the explicit shapes D60p2, D72p2,
D84p2 and D96p2, which name the p2 wheels outright so that no later plan
can move them. One engine reproduces both wheels' streams over the same
line.

## Wall clock at the measured rates (engine v2)

The campaign engine's rate at each filter (rates.py, six launches after
two unpipelined, round 1's 5g table) against the model's median from the
filter's floor (model_results.json):

| term | from | median | x/s | clock to the median | Q1 … P90 |
|---|---|---|---|---|---|
| A070737 a(11) | a(10) = 1.35×10¹⁶ | 3.6×10¹⁹ | 1.0×10¹⁸ | under a minute | 11 s … 3 min |
| A070737 a(12) | a(11)'s median | 3.1×10²² | 9.2×10¹⁸ | 55 min | 17 min … 4.4 h |
| A070737 a(13) | a(12)'s median | 1.6×10²⁵ | 1.79×10¹⁹ | **10.3 days** | 3.3 d … 49 d |
| A072942 a(66) | 3 | 2.0×10¹⁶ | 5.7×10¹⁶ | 0.4 s | … 2 s |
| A072942 a(78) | 3 | 3.1×10¹⁵ | 7.1×10¹⁵ | 0.4 s | … 2 s |
| A072942 a(88) | 3 | 5.5×10¹⁶ | 6.7×10¹⁶ | 0.8 s | … 4 s |
| A072942 a(48) | 3 | 6.9×10¹⁷ | 1.9×10¹⁷ | 4 s | … 18 s |
| A072942 a(80) | 3 | 2.1×10²⁰ | 8.2×10¹⁷ | 4 min | 1.3 min … 20 min |
| A072942 a(60) | 3 | 3.4×10²⁵ | 6.0×10²⁰ (p3 wheel; 5.5×10²⁰ on p2's in the same A/B) | **16 h** | 5 h … 3 d |
| A072942 a(72) | 3 | 1.6×10²⁶ | 8.4×10²⁰ (p3 wheel; 8.1×10²⁰ on p2's) | **2.2 days** | 15 h … 10 d |
| A072942 a(84) | 3 | 1.8×10²⁵ | 3.1×10¹⁹ (p3; 3.0×10¹⁹) | **6.7 days** | 2 d … 29 d |
| A072942 a(96) | 3 | 3.4×10²⁵ | 4.1×10¹⁹ (p3; 3.8×10¹⁹) | **9.5 days** | 3 d … 45 d |
| A072942 a(90) | 3 | 1.0×10²⁵ | 1.04×10¹⁹ | **11 days** | 3.3 d … 52 d |

(The p3 rates at 60, 72, 84 and 96 are round 2's A/B medians at x = 3 —
5.98, 8.23, 0.312 and 0.415 ×10²⁰ — where the campaign spends its first
hours; at the model's median the measured wheels read 1.07, 1.07, 1.04 and
1.07 of the p2 wheels, so the days above are the first hours' rate and the
later days are a few percent slower on both wheels. The segments at 84 and
96 are now 2 h instead of 10 and at 60 a quarter of an hour, so a find
there is confirmed within that of being passed.)

The A072942 openings close in seconds to minutes, which is why TARGETS
runs them first; its campaign's clock is the five day-long indices, 31
days of medians together, and A070737's is a(13). Absolute rates on this
desktop move up to ~10% between processes (n = 60 read 5.5–6.1×10²⁰ x/s
in one afternoon), so the ratios in OPTIMIZATION_LOG.md are the record
and these clocks are ±10%.

Realized (RESULTS.md, 2026-10-23 to 10-25): the n = 60 campaign averaged
5.9×10²⁰ x/s over 31.5 h and 6.7×10²⁵ of line, between the two wheels'
prices as its line was split between them; A070737's n = 12 line ran at
7.8×10¹⁸ x/s over its 35 minutes (the first launch unpipelined, the
promotion and a(11)'s certificates inside the clock) against the 9.2×10¹⁸
above. a(12) came in 35 minutes against the 55 above and a(60) in 31.5 h
against the 16, both inside their quantile bands.
