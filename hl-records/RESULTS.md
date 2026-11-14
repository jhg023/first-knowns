# RESULTS — hl-records (A331940)

> **Authorship disclaimer:** As with the rest of this project, this
> document and the code it describes were authored by **Claude
> (Anthropic's AI)** at the repository owner's direction.

## Verified finds

**Twenty-three terms: a(12) through a(34) of A331940**, the addends k
for which x^2 + x + k sets a new record of its Hardy-Littlewood constant
C. They are the first advance on the entry since Hugo Pfoertner's eleven
terms of 2020 (the entry's last word, January 2026, was a(12) > 3·10^6).
All were found by the owner's runs of `python launch.py`, no flags,
between 2026-11-11 and 2026-11-14 — 62.8 hours of campaign clock in all,
on four engine versions — and each was confirmed three ways before it was
written (README.md, "The discovery protocol"). Times are the ledger's,
local; the engine is the one named by the cursor key in the evidence
(`least_claim.engine`).

| n | a(n) = k | C | h(1 − 4k) | h enumerated (leg 3) | found | engine |
|---|---|---|---|---|---|---|
| 12 | 49,840,601 | 8.2509610031 | 894 | 894 | 11-11 18:50 | v2 |
| 13 | 80,144,501 | 8.2520894065 | 1,134 | 1,134 | 11-11 18:51 | v2 |
| 14 | 87,759,167 | 8.3053234408 | 1,178 | 1,178 | 11-11 18:51 | v2 |
| 15 | 94,014,647 | 8.3953330598 | 1,207 | 1,207 | 11-11 18:51 | v2 |
| 16 | 138,337,217 | 8.3953678635 | 1,464 | 1,464 | 11-11 18:52 | v2 |
| 17 | 160,834,691 | 8.5432038883 | 1,552 | 1,552 | 11-11 18:52 | v2 |
| 18 | 246,576,371 | 8.6172462039 | 1,905 | 1,905 | 11-11 18:53 | v2 |
| 19 | 390,033,857 | 8.7201512539 | 2,368 | 2,368 | 11-11 18:54 | v2 |
| 20 | 398,878,547 | 8.7233587165 | 2,394 | 2,394 | 11-11 18:55 | v2 |
| 21 | 482,535,941 | 8.7493976833 | 2,624 | 2,624 | 11-11 18:56 | v2 |
| 22 | 606,622,397 | 8.8048745934 | 2,925 | 2,925 | 11-11 18:57 | v2 |
| 23 | 640,552,931 | 8.8933154181 | 2,976 | 2,976 | 11-11 18:58 | v2 |
| 24 | 757,566,701 | 8.9027217371 | 3,232 | 3,232 | 11-11 19:01 | v2 |
| 25 | 854,032,997 | 9.0494400073 | 3,377 | 3,377 | 11-11 19:02 | v2 |
| 26 | 1,616,420,411 | 9.0833096250 | 4,628 | 4,628 | 11-11 19:06 | v2 |
| 27 | 1,655,941,871 | 9.1399340172 | 4,656 | 4,656 | 11-11 19:08 | v2 |
| 28 | 3,860,549,081 | 9.2054033017 | 7,058 | 7,058 | 11-11 19:15 | v2 |
| 29 | 5,384,581,877 | 9.3254822264 | 8,226 | 8,226 | 11-11 19:23 | v2 |
| 30 | 11,410,046,357 | 9.3289637764 | 11,971 | 11,971 | 11-11 19:44 | v2 |
| 31 | 21,072,785,801 | 9.3317190847 | 16,264 | 16,264 | 11-12 00:22 | v3 |
| 32 | 21,425,625,701 | 9.4146087817 | 16,259 | 16,259 | 11-12 00:28 | v3 |
| 33 | 26,853,927,251 | 9.6240787290 | 17,808 | 17,808 | 11-12 00:37 | v3 |
| 34 | 3,314,787,117,221 | 9.6733023409 | 196,924 | skipped by the campaign (k > 10^12); 196,924 in the read-back below | 11-14 00:08 | v4.1 (v4's key) |

C is rounded here to 10 decimals; each evidence file carries it to 34
digits with its error bound, and `C_table` rounds it to the 5 decimals the
entry's own table prints. Every 4k − 1 in the table is squarefree, so
every 1 − 4k is a fundamental discriminant and h(1 − 4k) is the class
number of its field. The evidence is `evidence/hlc_record_a<n>_k<k>.json`
for each row, with the ledger `evidence/hlc_discoveries.json`; the b-file
`evidence/b331940.txt` lists a(1)..a(34) in the OEIS's `n a(n)` format.

**Each find carries three confirmations** (README.md, "The discovery
protocol"): (1) the engine's exact h(1 − 4k) and a rigorous interval for C
through the primes to 2^20, strictly above the standing record's
interval; (2) Cohen's route, C to 34 digits from L(1, χ) and L(j, χ) by the
approximate functional equation with no class number in it, inside leg
1's interval, and the analytic class number w·sqrt(d)·L(1, χ)/(2π) equal
to leg 1's h to 20 decimals or better (a(34)'s is 1.3·10^−41 from an
integer); (3) a second class-number algorithm:
direct enumeration of the reduced forms for every k ≤ 10^12, which is
a(12)..a(33), plus the device's recount of the three-squares total at
another window alignment for all 23. a(34) is the only find above 10^12,
so its leg 3 is the alignment recount alone, with leg 2's analytic class
number as the independent check — and the read-back below enumerates its
forms after all.

**Three of the finds were in the literature.** Fung and Williams (Math.
Comp. 55, 1990), tabulated in Jacobson's 1995 thesis, list discriminants
with large C; three of them are now terms: −643338763 is k = 160834691,
a(17); −1595514187 is k = 398878547, a(20); and −85702502803 is
k = 21425625701, a(32) — the value the model used as an anchor, an upper
bound for the next record from a(30). Three more of theirs are not
records: k = 99539591 (C = 8.31582), which bounded a(12) before the
campaign, lies above a(15) = 94014647 with its larger C; C(1016793977) =
8.8650 is beaten by a(25) and C(17959429571) = 9.2194 by a(29).

### The read-back from disk (2026-11-14)

Every file was re-verified after the pause by a harness that shares
nothing with the launcher or either engine — plain Python integers, sympy
only to factor, its own sieve of primes:

- **h(1 − 4k) enumerated for all 23 finds**, a(34) included, from the
  definition: for each odd b ≤ sqrt((4k − 1)/3), every divisor a of
  (b² + 4k − 1)/4 with b ≤ a ≤ c gives the reduced form (a, ±b, c), one of
  the two when a = b or a = c, primitive forms only. All 23 equal the
  evidence's h (and legs 2 and 3); a(34)'s 196,924 took 260 s on one core,
  a(33)'s 20 s.
- **C recomputed from that h** by the class number formula and the
  absolutely convergent product E(k) to the primes below 10^7 (relative
  tail allowance 9.3·10^−9), summed as logarithms with `math.fsum`. Every
  C agrees with the evidence's 34-digit value to 1.1·10^−11 relative or
  better, and the harness's own interval clears the previous record's C
  at every step — the closest is a(16) over a(15), by 3.5·10^−5.
- **The harness itself was checked on the published table first:** all
  eleven known terms, a(1)..a(11), give the entry's C to its 5 decimals
  from the enumerated h (22, 24, 29, 33, 46, 66, 63 from a(5) on).
- **The files:** each record's `sequence`, `forms` ("x^2 + x + k"), `k`,
  `oeis_terms` {n: k}, `index` and `settles` against its file name; k odd;
  the indices 12..34 continuing the entry's list in the OEIS export of
  2026-10-26, none already there; `C_table` the 5-decimal rounding of `C`;
  `previous_record.k` the term before; `margin_over_previous` equal to C
  less the upper end of the previous record's interval; `least_claim`
  sweeping from k = 1 to the term itself; 4k − 1 squarefree exactly when
  the record names no conductor; each ledger row equal to its file but
  for the ledger's own `label` (DISCOVERY) and `t`; and
  `huntlib.evidence.gate_names` over the directory: 46 records (23 files,
  23 ledger rows) carry the integer under the entry's letter k.

**23 files, 0 failures.**

### The least-claim basis

Each file's `least_claim` reads: every odd k below the term was taken in
order by the engine from k = 1 and either dropped by the survivor rule — a
proved lower bound of its class number, from its class group or from the
counted class number itself, puts C ≤ the floor, which is at most the
standing record — or classified exactly on the host from its counted
class number and found not to exceed the standing record; even k has
C = 0. It is conditional on nothing: Gauss's three-squares theorem, the
class number formula, composition of forms and genus theory, and the
reduction theory of forms (README.md, section 4, and the gates that police
the engine). a(1)..a(11) were rediscovered in order by the campaign as
canaries. The line was swept by four engines, each pinned to its
predecessor by the gates and the frozen fingerprints (v3's local Euler
factors remove survivors that are all below the floor, so its stream is
v2's less those, with the census unchanged), and each later cursor key
accepting the earlier one's coverage whole:

| line | engine (cursor key) | terms found |
|---|---|---|
| k = 1 to 12,557,746,177 | v2 (`v2-classgroup-three-squares`, `rule=p251`) | a(12)..a(30) |
| to 29,905,387,521 | v3 (`v3-classgroup-sparse-count`, `rule=p251-local`) | a(31)..a(33) |
| to 8.03·10^11 | v4 (`v4-classgroup-sparse-count-wide`) | — |
| to 4,149,500,444,673 (the pause) | v4.1 (v4's key: same line, stream and rule) | a(34) |

The 155,006 survivors counted under v2's rule before the local Euler
factors (HLC-001) are kept apart in the checkpoint
(`survivors_by_rule`); the k they include and v3's rule removes are all
classified below the floor (gate S9), so the census is unaffected.

### What was verified while building (2026-11-11)

These are validations of published values, not discoveries.

- **The eleven known terms.** The oracle, exhaustively over odd k ≤ 3·10^5,
  finds exactly a(1)..a(11) = 1, 11, 17, 41, 21377, 27941, 41537, 55661,
  115721, 239621, 247757 as the records of C, with every C equal to the
  entry's table to its 5 decimals. The class numbers h(1 − 4k) of the
  last seven are 22, 24, 29, 33, 46, 66, 63.
- **C(247757) to 30 digits** (Cohen's route, no class number):
  8.24741345236759360963578660603, with w·sqrt(d)·L(1, χ)/(2π) = 63 to 20
  decimals and 63 reduced forms enumerated.
- **C(41)/2 against A221712:** agreement to 40 digits.
- **A tighter published upper bound for a(12).** Fung and Williams' (1990)
  discriminant −398158363 is k = 99539591; this project computes
  h(1 − 4k) = 1254 and C = 8.3158226 > C(247757), reproducing their
  4.1579113 = C/2. So a(12) ≤ 99539591 was known before the campaign.
  Fourteen further values of theirs between k = 27941 and k = 21425625701
  are reproduced to 7 decimals (`hlc_search.py`, gate S4), and three more
  at k = 4.1·10^12, 7.5·10^12 and 9.3·10^12 were checked once by the
  analytic class number (h = 223574, 296475, 328170; C/2 = 4.7524812,
  4.8379057, 4.8634109 as published).
- **Two misprints in the source table** (Jacobson's thesis, Table 6.1):
  the row printed D = −88507 is −85507 (k = 21377), and the row
  D = −60408307 printed with C(D) = 4.0501092 is 4.0510921 (h = 501).

## The census

Counts of C per bin of 0.25 from 7.5 over every odd k < 4,149,500,444,673
(2.07·10^12 values), from the checkpoint at the pause, against the
model's law over the same k:

| C in | seen | modelled | seen / modelled |
|---|---|---|---|
| 7.50–7.75 | 22,597,072 | 22,667,133 | 1.00 |
| 7.75–8.00 | 7,816,082 | 7,839,206 | 1.00 |
| 8.00–8.25 | 2,369,063 | 2,382,350 | 0.99 |
| 8.25–8.50 | 613,844 | 626,441 | 0.98 |
| 8.50–8.75 | 131,659 | 140,085 | 0.94 |
| 8.75–9.00 | 22,208 | 26,127 | 0.85 |
| 9.00–9.25 | 2,663 | 3,976 | 0.67 |
| 9.25–9.50 | 213 | 482 | 0.44 |
| 9.50–9.75 | 11 | 45 | 0.24 |

43,373,581 survivors in all; 30 `[NEAR]` values (C within 1% below the
standing record), verified and not evidenced; 10,288 health checks (an
analytic class number for a random k every 20 seconds, alternately a
counted k and a k the prefilter or a partial count dropped — a failure
raises an `[ALARM]` that halts the campaign, and it ran on to the owner's
stop). a(33) and a(34) are two of the 11 values in the last bin; nothing
above 9.75 was seen, where the model expects 3.3.

## The finds against the model

The predictions stated before any run (`model_results.json`, README.md's
first table) were conditioned on a(11) and the entry's bound 3·10^6. The
first two finds came late and everything from a(17) to a(25) came far
early — the frozen Q1 of a(25) was 2.3·10^11, and it fell at 8.5·10^8:

| term | found at | frozen Q1 / median / Q3 | where |
|---|---|---|---|
| a(12) | 4.98·10^7 | 4.5·10^6 / 6.6·10^6 / 1.0·10^7 | past P90 (1.5·10^7) |
| a(13) | 8.01·10^7 | 1.1·10^7 / 1.7·10^7 / 3.0·10^7 | past P90 (6.0·10^7) |
| a(14) | 8.78·10^7 | 2.3·10^7 / 4.2·10^7 / 9.9·10^7 | median to Q3 |
| a(15) | 9.40·10^7 | 5.0·10^7 / 1.1·10^8 / 3.4·10^8 | Q1 to median |
| a(16) | 1.38·10^8 | 1.1·10^8 / 3.0·10^8 / 1.1·10^9 | Q1 to median |
| a(17)..a(25) | 1.61·10^8 .. 8.54·10^8 | Q1s 2.5·10^8 .. 2.3·10^11 | below Q1, every one |

Re-conditioned at a(30) (README.md's second table), a(31) came just below
its median (the literature's anchor), a(32) at about its Q1 and a(33)
below its Q1.
Re-conditioned at a(33) and the cursor 8.03·10^11 (the third table),
a(34) came at the law's 99.97th percentile: its median was 1.02·10^12
and it fell at 3.31·10^12. The census above says why the model swung:
its law matches the bulk of the distribution of C and overstates the far
tail at these heights (0.24 of the modelled count in the bin holding the
last two records), after understating it below 6.28·10^9 (25 values above
9.0 against 14 modelled). Its re-fit is owed before its clocks for a(35)
on are trusted; README.md, "The model", gives its table at the pause and
the correction the census suggests.

## Submission

Nothing is submitted from inside the pipeline (CLAUDE.md rule 5).
`evidence/b331940.txt` is the b-file for the owner to upload, n = 1..34:
one `n a(n)` pair per line, ASCII, no header, a(1)..a(11) the entry's
published terms and a(12)..a(34) the `oeis_terms` of the files here
(evidence/README.md).

## Final state

**PAUSED — open to others** (2026-11-14). Every odd k below
4,149,500,444,673 has been swept and settled; a(35) is open above that,
and **a(35) ≤ 7514981191031**: that k is one of Fung and Williams'
discriminants, with C = 9.6758115 > 9.67330 = C(a(34)) (h = 296475 by the
analytic class number, above), about 3.2 days of sweep from the pause at
engine v4.1's rate. The model's median for a(35) is 4.5·10^12, and about
5.6·10^12 with its tail scaled to the census (README.md, "The model").
The checkpoint is not part of the repository, so a fresh start begins at
k = 1 and reaches the pause in about 2.6 days at engine v4.1's measured
rate on an RTX 4090 (BENCHMARKS.md), rediscovering a(1)..a(34) as it goes.
