# RESULTS — linear-ladders (A088250 and its cluster)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

**Notation.** This page writes every family as `r·k ± 1` — term `k`, index
`r`. A173750, A125838, A125839, A164325 and A164326 call the term **m** in
the OEIS and use k for the index, and their evidence files follow the OEIS
(README.md, "Notation"). Either way the integer in each heading below is
the term, and the file's `oeis_terms` says which index it goes to.

## Verified finds

All three below come from the single A088250 campaign of 2026-09-03: the
v2 engine with no flags, from `k = 10⁶` to the family's ceiling in 1.26 h
of wall clock (started 17:59, stopped 19:15 at the last whole wheel period
under `3.317×10²⁴`). Each evidence file was re-verified from disk before
this page was written: every value re-tested with sympy's BPSW, the run
re-derived from the bare definition (`lladder_reference.run_length`), the
stopper's factor re-multiplied, every certificate re-verified by
`huntlib.certificate.verify`, the derived claims re-derived, and the
least-claim basis read back. Model figures are from `lladder_model`, each
scored from the frontier that was known when the search for that term
began.

### A088250 a(15) = 1,555,360,041,314,493,173,760 — 2026-09-03, 18:00

- **run 15**: `r·k + 1` is prime for `r = 1..15`; the 15th value is
  `15·k + 1 = 23,330,400,619,717,397,606,401`.
- **stopper**: `16·k + 1 = 24,885,760,661,031,890,780,161 = 19 ×
  1,309,776,876,896,415,304,219`, so the run is exactly 15.
- **certificates**: all 15 values under the deterministic Miller–Rabin
  bound (`k` is under the proof crossing `k_proof(15) = 2.21×10²³`), all
  `deterministic-mr`, all re-verified.
- **also settles**: `A202778(15) = 1,555,360,041,314,493,173,760` (the run
  is exact) and `A071576(15) = 777,680,020,657,246,586,880`.
- **model**: from `a(14)`, median `1.98×10²⁰`, P90 `9.69×10²⁰`; the find
  is at `k / median = 7.9`, `E = 3.24` — beyond the P90, the latest of the
  three against its model.
- **when**: 65 s into the campaign, at the close of period 0, exactly as
  the README's first-lines paragraph predicted.
- `k = 2¹² · 3 · 5 · 7 · 11 · 13 · 17 · 1213 · 1226410699`.
- evidence: `evidence/A088250_a15_1555360041314493173760.json`

### A088250 a(16) = 87,117,680,854,368,555,070,680 — 2026-09-03, 18:10

- **run 16**: `r·k + 1` prime for `r = 1..16`; the 16th value is
  `16·k + 1 = 1,393,882,893,669,896,881,130,881`.
- **stopper**: `17·k + 1 = 1,481,000,574,524,265,436,201,561 = 9199 ×
  160,995,822,863,818,397,239`.
- **certificates**: 16 `deterministic-mr` (`k` under the crossing
  `k_proof(16) = 2.07×10²³`), all re-verified.
- **also settles**: `A202778(16) = k` and
  `A071576(16) = 43,558,840,427,184,277,535,340`.
- **model**: from `a(15)`, median `2.83×10²²`, P90 `1.37×10²³`;
  `k / median = 3.1`, `E = 1.65`.
- **when**: 11 min in.
- `k = 2³ · 3² · 5 · 7 · 11² · 13 · 17 · 19 · 67 · 52957 · 19176809`.
- evidence: `evidence/A088250_a16_87117680854368555070680.json`

### A088250 a(17) = 1,048,124,771,278,912,649,231,910 — 2026-09-03, 18:49

- **run 17**: `r·k + 1` prime for `r = 1..17`; the 17th value is
  `17·k + 1 = 17,818,121,111,741,515,036,942,471`.
- **stopper**: `18·k + 1 = 18,866,245,883,020,427,686,174,381 = 23 ×
  820,271,560,131,322,942,877,147`.
- **certificates**: `k` is **past the proof crossing** `k_proof(17) =
  1.95×10²³`, so the classification that found it was a strong
  probable-prime chain and the discovery is proved by certificate: the
  three values under the bound (`r = 1, 2, 3`) by `deterministic-mr`, the
  other fourteen by **BLS75 Theorem 1** on `N − 1 = r·k`, `k` factored
  once, every prime factor under the bound. All 17 re-verified from
  scratch, twice: by the launcher before the file was written and from
  disk for this page. The first find in this repository's linear-ladder
  cluster to need the certificate route.
- **also settles**: `A202778(17) = k` and
  `A071576(17) = 524,062,385,639,456,324,615,955`.
- **model**: from `a(16)`, median `1.98×10²⁴`, Q1 `6.95×10²³`;
  `k / median = 0.53`, `E = 0.41` — early.
- **when**: 50 min in.
- `k = 2 · 3² · 5 · 7 · 11 · 13 · 17² · 19 · 71 · 3593 · 8305568963`.
- evidence: `evidence/A088250_a17_1048124771278912649231910.json`

Across the three finds the model's `E` averages 1.77 and `k / median`
runs 7.9, 3.1, 0.53 (geometric mean 2.3): the same "intensity right,
first occurrence late" pattern the repository's other ladder projects
recorded, one draw at a time.

### A bound: A088250 a(18) > 3,316,761,604,016,016,802,395,750

After `a(17)` the campaign promoted its filter to `n = 18` and swept on to
the last whole wheel period under the engine ceiling, `k =
3,316,761,604,016,016,802,395,750 = 1725 × 1.92×10²¹`, classifying every
survivor and finding no run of 18. So **no `k < 3.3168×10²⁴` has
`r·k + 1` prime for all `r = 1..18`**, the first bound of any kind on
A088250 at an open index. The claim is sound above the proof crossing
too: past `k_proof(18) = 1.84×10²³` the Miller-Rabin chain is a
probable-prime test, and a composite that passed it could only *lengthen*
a run, never hide one — a true run of 18 would have passed every test and
been claimed. The model, from `a(17)`, had put `a(18)` under the ceiling
with 2.1% and puts its median at `2.2×10²⁶`, 66× the ceiling; reaching it
needs the ceiling raised (a certificate that recurses into the factors of
`k`; priced in [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)), not more
sweeping.

Each find is a **first occurrence**: every `k` from `K_START = 10⁶` to the
find swept and every survivor classified in `k` order, and below `K_START`
the claim rests on monotonicity (`a(14) = 1.14×10¹⁹`). The least-claim
basis is written into every evidence file: `swept_from`, `swept_to`, the
wheel period `W = 1,922,760,350,154,212,639,070` (the product of the
primes to 59, the unit included), the unit 30030, the sieve depth 65536
and the monotone floor, under the engine key
`a088250-v2-u30030-p137-p247-p359-q265536-seg32`.

## A125838: four terms and a bound — 2026-09-03, 19:28–19:46

The second campaign, `--family A125838` with no flags, ran 17.2 minutes
from `k = 10⁶` to the family's ceiling (the proof crossing of its current
filter, `3.317×10²⁴ / 19 = 1.746×10²³` at `n = 19`) and found four terms.
A125838 is a −1 family (`r·k − 1` for `r = 2..n`), so every value stays
under the deterministic bound and every certificate is the deterministic Miller-Rabin test
itself; each file was re-verified from disk exactly as A088250's were.

### A125838 a(15) = 45,187,548,280,664,790 — 19:32

- **run 15**: `r·k − 1` prime for `r = 2..15`; `15·k − 1 =
  677,813,224,209,971,849`. **stopper** `16·k − 1 =
  723,000,772,490,636,639 = 17 × 42,529,457,205,331,567`.
- 14 certificates, all `deterministic-mr`, re-verified.
- **This is the integer the literature holds as A125839's `a(15)`**
  (Giovanni Resta, 2017): the `r = 3..15` ladder's least term also has
  `2·k − 1 = 90,375,096,561,329,579` prime, so it is A125838's `a(15)` as
  well — 5.6× A125838's published `a(14)`, and far below the model's Q1
  (`k / median = 0.02`, `E = 0.04`). Found at the close of period 0,
  3.5 min in, together with `a(16)`.
- `k = 2 · 3 · 5 · 7² · 11 · 13 · 83 · 1747 · 1482499`.
- evidence: `evidence/A125838_a15_45187548280664790.json`

### A125838 a(16) = 436,409,209,028,729,276,340 — 19:32

- **run 16**: `16·k − 1 = 6,982,547,344,459,668,421,439`. **stopper**
  `17·k − 1 = 7,418,956,553,488,397,697,779 = 31 ×
  239,321,179,144,787,022,509`.
- 15 `deterministic-mr` certificates, re-verified.
- **model**: from `a(15)`, median `1.72×10²⁰`; `k / median = 2.5`,
  `E = 1.32`. Inside period 0 like `a(15)`, so narrated with it.
- `k = 2² · 3 · 5 · 7 · 11 · 13 · 17 · 427424740973467`.
- evidence: `evidence/A125838_a16_436409209028729276340.json`

### A125838 a(17) = 44,387,933,133,290,055,609,300 — 19:42

- **run 17**: `17·k − 1 = 754,594,863,265,930,945,358,099`. **stopper**
  `18·k − 1 = 798,982,796,399,221,000,967,399 = 941 ×
  849,078,423,378,555,792,739`.
- 16 `deterministic-mr` certificates, re-verified.
- **model**: from `a(16)`, median `1.08×10²²`; `k / median = 4.1`,
  `E = 1.99`. 13.7 min in.
- `k = 2² · 3 · 5² · 7 · 11² · 13 · 17 · 19 · 29 · 41 · 117659 · 297377`.
- evidence: `evidence/A125838_a17_44387933133290055609300.json`

### A125838 a(18) = 74,882,388,347,598,051,560,340 — 19:43

- **run 18**: `18·k − 1 = 1,347,882,990,256,764,928,086,119`. **stopper**
  `19·k − 1 = 1,422,765,378,604,363,979,646,459 = 233 ×
  6,106,289,178,559,497,766,723`.
- 17 `deterministic-mr` certificates, re-verified.
- **model**: from `a(17)`, median `1.99×10²⁴`; `k / median = 0.04`,
  `E = 0.02` — only 1.7× `a(17)`, and 2.5× under the `n = 18` ceiling of
  `1.84×10²³` that the pre-run model had given it 13% of clearing. 15 min
  in.
- `k = 2² · 3³ · 5 · 7 · 11 · 13 · 17 · 19 · 47 · 1093 · 8348939387`.
- evidence: `evidence/A125838_a18_74882388347598051560340.json`

Across the four, `E` averages 0.84 and `k / median` runs 0.02, 2.5, 4.1,
0.04. None settles a derived entry (A125838 has none), but **each is an
upper bound on A125839 at the same index**: the `r = 3..n` conditions are
a subset of the `r = 2..n` ones, so `A125839(16) ≤ 436,409,209,028,729,276,340`,
`A125839(17) ≤ 44,387,933,133,290,055,609,300` and `A125839(18) ≤
74,882,388,347,598,051,560,340` — what the A125839 campaign will find at
or below.

### A bound: A125838 a(19) > 173,048,431,513,879,137,516,300

After `a(18)` the filter moved to `n = 19` and the sweep continued to the
last whole period under that filter's ceiling (`1.746×10²³`), period 90,
finding no run of 19. So no `k < 1.7305×10²³` has `r·k − 1` prime for all
`r = 2..19`. Every classification on a −1 family is a proof (its values
never leave the deterministic zone), so the bound rests on nothing
probabilistic. The model had given `a(19)` 0.4% under this ceiling from
`a(18)` and puts its median at `8.5×10²⁵`; lifting the ceiling needs an
N+1 certificate route ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)).

## A125839: three terms and a bound — 2026-09-03, 19:55–20:10

The third campaign, `--family A125839` (`r·k − 1` for `r = 3..n`), 15
minutes from `k = 10⁶` to the same ceiling as A125838's (`1.746×10²³` at
`n = 19`). Its conditions are a subset of A125838's, so A125838's terms
bounded these from above before the campaign started, and each landed
under its bound. All certificates are the deterministic test; each file
was re-verified from disk.

### A125839 a(16) = 14,423,013,361,403,116,470 — 19:58

- **run 16**: `r·k − 1` prime for `r = 3..16`; `16·k − 1 =
  230,768,213,782,449,863,519`. **stopper** `17·k − 1 =
  245,191,227,143,852,979,989 = 31 × 7,909,394,423,995,257,419`.
- 14 `deterministic-mr` certificates, re-verified.
- **model**: from the published `a(15)`, median `2.67×10¹⁸`;
  `k / median = 5.4`, `E = 2.30`. Bound from A125838: `≤ 4.36×10²⁰`.
  Inside period 0, narrated at its close 3.4 min in, together with
  `a(17)`.
- `k = 2 · 3² · 5 · 7 · 11 · 13 · 29569 · 5414305807`.
- evidence: `evidence/A125839_a16_14423013361403116470.json`

### A125839 a(17) = 771,355,748,787,892,768,500 — 19:58

- **run 17**: `17·k − 1 = 13,113,047,729,394,177,064,499`. **stopper**
  `18·k − 1 = 13,884,403,478,182,069,832,999 = 17 ×
  816,729,616,363,651,166,647`.
- 15 `deterministic-mr` certificates, re-verified.
- **model**: from `a(16)`, median `1.43×10²⁰`; `k / median = 5.4`,
  `E = 2.61`. Bound from A125838: `≤ 4.44×10²²`. Inside period 0.
- `k = 2² · 3 · 5³ · 7 · 11 · 13 · 19 · 31 · 872195997311`.
- evidence: `evidence/A125839_a17_771355748787892768500.json`

### A125839 a(18) = 6,530,891,065,478,723,143,200 — 19:59

- **run 18**: `18·k − 1 = 117,556,039,178,617,016,577,599`. **stopper**
  `19·k − 1 = 124,086,930,244,095,739,720,799 = 17 ×
  7,299,231,190,829,161,160,047`.
- 16 `deterministic-mr` certificates, re-verified.
- **model**: from `a(17)`, median `1.23×10²²`; `k / median = 0.53`,
  `E = 0.41`. Bound from A125838: `≤ 7.49×10²²`. 4.7 min in.
- `k = 2⁵ · 3 · 5² · 7 · 11² · 13 · 23 · 31 · 79 · 439 · 9994321`.
- evidence: `evidence/A125839_a18_6530891065478723143200.json`

`E` averages 1.77 over the three; `k / median` 5.4, 5.4, 0.53.

### A bound: A125839 a(19) > 173,048,431,513,879,137,516,300

The sweep continued at `n = 19` to period 90, the last whole period under
that filter's ceiling, and found no run of 19: no `k < 1.7305×10²³` has
`r·k − 1` prime for all `r = 3..19`. Every decision on this family is a
proof. The model had given `a(19)` 16% under the ceiling from `a(18)`
and puts its median at `1.1×10²⁴`, six times the ceiling.

## A173750: four terms on three integers, and a bound — 2026-09-03, 20:23–21:00

The fourth campaign, `--family A173750` (`r·k + 1` for `r = 2..n`, a +1
family), 37 minutes from `k = 10⁶` to the +1 ceiling `3.317×10²⁴`. Every
value stayed under the deterministic bound (the largest, `19·k + 1 =
2.8×10²⁴`, just under it), so every certificate is the deterministic Miller-Rabin test;
each file was re-verified from disk.

### A173750 a(16) = 828,196,248,070,762,801,230 — 20:24

- **run 16**: `r·k + 1` prime for `r = 2..16`; `16·k + 1 =
  13,251,139,969,132,204,819,681`. **stopper** `17·k + 1 =
  14,079,336,217,202,967,620,911 = 419 × 33,602,234,408,598,968,069`.
- 15 `deterministic-mr` certificates, re-verified.
- **model**: from the published `a(15)`, median `1.94×10²⁰`;
  `k / median = 4.3`, `E = 1.99`. Found 65 s in, at the close of period 0.
- `k = 2 · 3 · 5 · 7 · 11 · 13 · 17 · 41 · 173 · 228717315661`.
- evidence: `evidence/A173750_a16_828196248070762801230.json`

### A173750 a(17) = 67,335,095,107,785,754,679,430 — 20:39

- **run 17**: `17·k + 1 = 1,144,696,616,832,357,829,550,311`. **stopper**
  `18·k + 1 = 1,212,031,711,940,143,584,229,741 = 19 ×
  63,791,142,733,691,767,591,039`.
- 16 `deterministic-mr` certificates, re-verified.
- **model**: from `a(16)`, median `1.18×10²²`; `k / median = 5.7`,
  `E = 2.65`. 15.4 min in.
- `k = 2 · 3 · 5 · 7 · 11 · 13 · 17 · 32029 · 41729 · 98686073`.
- evidence: `evidence/A173750_a17_67335095107785754679430.json`

### A173750 a(18) = a(19) = 147,316,106,448,079,863,444,150 — 20:42

- **run 19, found while `a(18)` was open**: `r·k + 1` is prime for every
  `r = 2..19`, so this one `k` settles two terms at once — a **rider**,
  as this family's published `a(12) = a(13) = a(14)` are. `19·k + 1 =
  2,799,006,022,513,517,405,438,851`, the largest value any campaign here
  has certified by the deterministic test (the bound is `3.317×10²⁴`).
  **stopper** `20·k + 1 = 2,946,322,128,961,597,268,883,001 = 19 ×
  155,069,585,734,820,908,888,579`.
- 18 `deterministic-mr` certificates, re-verified. Evidenced once, under
  `a(18)`, with `settles = [18, 19]`.
- **model**: from `a(17)`, `a(18)`'s median `2.06×10²⁴`; `k / median =
  0.07`, `E = 0.05` — very early, and it carried `a(19)` with it. 19.7 min
  in.
- `k = 2 · 3 · 5² · 7 · 11 · 13 · 17 · 37 · 1559819157504709`.
- evidence: `evidence/A173750_a18_147316106448079863444150.json`

`E` averages 1.56 over the three searched terms (the rider is not
scored: it was never searched for); `k / median` 4.3, 5.7, 0.07.

### A bound: A173750 a(20) > 3,316,761,604,016,016,802,395,750

The filter moved to `n = 20` and the sweep ran on to the last whole
period under the +1 ceiling, finding no run of 20: no `k < 3.3168×10²⁴`
has `r·k + 1` prime for all `r = 2..20`. Above the proof crossing
`k_proof(20) = 1.66×10²³` the classification is a probable-prime chain,
which can only lengthen a run, never hide one, so the bound stands. The
model had given `a(20)` 0.2% under the ceiling from `a(19)` and puts its
median at `1.3×10²⁸`.

## A164326: two terms and a bound — 2026-09-03, 22:27–22:41

The fifth campaign, `--family A164326` (`(2r−1)·k − 1` for `r = 1..n`,
the odd multipliers, a −1 family), 14 minutes from `k = 10⁶` to the
lowest ceiling of the seven: the proof crossing for its largest
multiplier, `3.317×10²⁴ / 33 = 1.005×10²³` at `n = 17`. Every
certificate is the deterministic test; each file was re-verified from
disk.

### A164326 a(15) = 392,547,927,582,515,694,990 — 22:29

- **run 15**: `(2r−1)·k − 1` prime for `r = 1..15`; the 15th value is
  `29·k − 1 = 11,383,889,899,892,955,154,709`. **stopper** `31·k − 1 =
  12,168,985,755,057,986,544,689 = 19 × 640,472,934,476,736,133,931`.
- 15 `deterministic-mr` certificates, re-verified.
- **model**: from the published `a(14)`, median `6.24×10¹⁹`;
  `k / median = 6.3`, `E = 2.46`. Found 145 s in, at the close of
  period 0.
- `k = 2 · 3 · 5 · 7 · 11² · 13 · 59 · 285841 · 70464137`.
- evidence: `evidence/A164326_a15_392547927582515694990.json`

### A164326 a(16) = 10,214,000,995,018,156,616,280 — 22:33

- **run 16**: `31·k − 1 = 316,634,030,845,562,855,104,679`. **stopper**
  `33·k − 1 = 337,062,032,835,599,168,337,239 = 23 ×
  14,654,870,992,852,137,753,793`.
- 16 `deterministic-mr` certificates, re-verified.
- **model**: from `a(15)`, median `6.12×10²¹`; `k / median = 1.7`,
  `E = 1.04`. 6.4 min in.
- `k = 2³ · 3 · 5 · 7 · 11 · 13 · 17 · 769 · 6504371094253`.
- evidence: `evidence/A164326_a16_10214000995018156616280.json`

`E` averages 1.75 over the two; `k / median` 6.3, 1.7.

### A bound: A164326 a(17) > 99,983,538,208,019,057,231,640

At `n = 17` the sweep ran to period 52, the last whole period under
`1.005×10²³`, and found no run of 17: no `k < 9.998×10²²` has
`(2r−1)·k − 1` prime for all `r = 1..17`. Every decision on this family
is a proof. The model had given `a(17)` 12.5% under the ceiling from
`a(16)` and puts its median at `8.3×10²³`, eight times the ceiling.

## A164325: three terms and a bound — 2026-09-03, 22:49–23:49

The sixth campaign, `--family A164325` (`(2r−1)·k + 1` for `r = 1..n`,
the odd multipliers, a +1 family), one hour from `k = 10⁶` to the +1
ceiling `3.317×10²⁴`. Two of its three terms sit past the proof crossing
and are proved by certificate; each file was re-verified from disk.

### A164325 a(16) = 1,284,243,585,711,408,422,100 — 22:49

- **run 16**: `(2r−1)·k + 1` prime for `r = 1..16`; the 16th value is
  `31·k + 1 = 39,811,551,157,053,661,085,101`. **stopper** `33·k + 1 =
  42,380,038,328,476,477,929,301 = 59 × 718,305,734,380,957,253,039`.
- 16 `deterministic-mr` certificates, re-verified.
- **model**: from the published `a(15)`, median `4.91×10²¹`;
  `k / median = 0.26`, `E = 0.27`. Found 49 s in, at the close of
  period 0.
- `k = 2² · 3⁵ · 5² · 7 · 11 · 13 · 17 · 19 · 163457379389`.
- evidence: `evidence/A164325_a16_1284243585711408422100.json`

### A164325 a(17) = 317,674,273,854,740,299,136,640 — 23:17

- **run 17**: `33·k + 1 = 10,483,251,037,206,429,871,509,121`. **stopper**
  `35·k + 1 = 11,118,599,584,915,910,469,782,401 = 53 ×
  209,784,897,828,602,084,335,517`.
- **certificates**: `k` is **past the proof crossing** `k_proof(17) =
  1.005×10²³`: the five values under the bound (`r = 1..5`) by
  `deterministic-mr`, the other twelve by **BLS75 Theorem 1** on
  `N − 1 = (2r−1)·k`, all 17 re-verified from scratch.
- **model**: from `a(16)`, median `7.84×10²³`; `k / median = 0.40`,
  `E = 0.37`. 28.3 min in.
- `k = 2⁷ · 3² · 5 · 7 · 11 · 13 · 17 · 19 · 73 · 691 · 6007 · 562943`.
- evidence: `evidence/A164325_a17_317674273854740299136640.json`

### A164325 a(18) = 511,721,589,397,871,969,516,400 — 23:23

- **run 18**: `35·k + 1 = 17,910,255,628,925,518,933,074,001`. **stopper**
  `37·k + 1 = 18,933,698,807,721,262,872,106,801 = 19 ×
  996,510,463,564,276,993,268,779`.
- **certificates**: past the crossing `k_proof(18) = 9.48×10²²`; three
  values by `deterministic-mr`, fifteen by BLS75 Theorem 1, all
  re-verified.
- **model**: from `a(17)`, median `6.39×10²⁵`; `k / median = 0.01`,
  `E = 0.01` — only 1.6× `a(17)`, and the pre-run model had given `a(18)`
  9% of clearing the ceiling at all. 34.4 min in.
- `k = 2⁴ · 3 · 5² · 7² · 11 · 13 · 17 · 71 · 7457 · 6761592029`.
- evidence: `evidence/A164325_a18_511721589397871969516400.json`

`E` averages 0.21 over the three; `k / median` 0.26, 0.40, 0.01 — all
three early, against the 4–8× lateness of the −1 odd family's `a(15)`
an hour before. One draw at a time, as ever.

### A bound: A164325 a(19) > 3,316,761,604,016,016,802,395,750

The filter moved to `n = 19` and the sweep ran to the last whole period
under the +1 ceiling with no run of 19: no `k < 3.3168×10²⁴` has
`(2r−1)·k + 1` prime for all `r = 1..19`. Above the crossing the
probable-prime chain can only lengthen a run, never hide one, so the
bound stands. The model, from `a(18)`, had `a(19)` 0.2% under the ceiling
and puts its median at `7.9×10²⁷`.

## A088651: one term and a bound — 2026-09-04, 00:06–00:18

The seventh and last campaign, `--family A088651` (`r·k − 1` for
`r = 1..n`, A088250's multipliers with the other sign; A202779 is its
exact-run version), 12 minutes from `k = 10⁶` to the crossing at
`n = 17`, `3.317×10²⁴ / 17 = 1.951×10²³`, at unit 510510 (17 is forced
from its opening). Every certificate is the deterministic test; the file
was re-verified from disk.

### A088651 a(16) = 43,263,866,546,732,976,414,270 — 00:12

- **run 16**: `r·k − 1` prime for `r = 1..16`; the 16th value is
  `16·k − 1 = 692,221,864,747,727,622,628,319`. **stopper** `17·k − 1 =
  735,485,731,294,460,599,042,589 = 31 × 23,725,346,170,789,051,582,019`.
- 16 `deterministic-mr` certificates, re-verified.
- **also settles**: `A202779(16) = 43,263,866,546,732,976,414,270` (the
  run is exact).
- **model**: from Jens Kruse Andersen's `a(15)`, median `2.34×10²²`;
  `k / median = 1.85`, `E = 1.07`. Found 5.3 min in, at the close of
  period 22.
- `k = 2 · 3 · 5 · 7 · 11 · 13 · 17 · 19 · 29 · 5869 · 26206279483`.
- evidence: `evidence/A088651_a16_43263866546732976414270.json`

### A bound: A088651 a(17) > 194,198,795,365,575,476,546,070

The filter moved to `n = 17` and the sweep ran to period 101, the last
whole period under `1.951×10²³`, with no run of 17: no `k < 1.942×10²³`
has `r·k − 1` prime for all `r = 1..17`. Every decision on this family
is a proof. The model had given `a(17)` 9.6% under this ceiling from
`a(16)` and puts its median at `1.9×10²⁴` — under the deterministic
bound `3.317×10²⁴`, which is where an N+1 certificate route would let
the sweep go (below).

## A164326 under the v3 ceiling: two terms and a bound — 2026-09-04, 01:29–09:02

The eighth campaign and the first under v3's `10⁴⁰` ceiling:
`--family A164326` with no flags, resumed from the family's v2 cursor
(period 52, `k = 9.998×10²²`, its old ceiling) at `n = 17` and stopped by
hand 7.5 hours later at `n = 19`. Every value it certified lies past the
deterministic bound, so these are the **first discoveries proved by the
N+1 route**: `N + 1 = (2r−1)·k` factored once per find, BLS75 Theorem 15
with a Lucas sequence per prime. Each file was re-verified from disk
exactly as the earlier ones were, subproof machinery included (neither
needed one: every prime factor of both `k` is under the bound).

### A164326 a(17) = 2,071,342,181,735,785,633,264,590 — 04:13

- **run 17**: `(2r−1)·k − 1` prime for `r = 1..17`; the 17th value is
  `33·k − 1 = 68,354,291,997,280,925,897,731,469`. **stopper** `35·k − 1 =
  72,496,976,360,752,497,164,260,649 = 3,997,749,779 ×
  18,134,445,717,832,531`.
- **certificates**: `k` is 20× past the proof crossing `k_proof(17) =
  1.005×10²³` (the v2 ceiling this family stopped at). One value under
  the bound (`r = 1`) by `deterministic-mr`; the other sixteen by
  **BLS75 Theorem 15** on `N + 1 = (2r−1)·k` factored completely, each
  with its own Lucas sequence and one shared discriminant, all 17
  re-verified from scratch by the launcher and again from disk.
- **model**: from the v2 bound `9.998×10²²`, median `1.05e+24`;
  `k / median = 1.97`, `E = 1.22`. From `a(16)` the pre-run model had
  put `a(17)` under the old ceiling with 12.5%; from the bound it put it
  under `3.317×10²⁴` with 83% and it landed at 2.07×10²⁴.
- **when**: 2.73 h in, at a campaign rate of `2.0×10²⁰ k/s` over the
  `n = 17` phase.
- `k = 2 · 3 · 5 · 7 · 11 · 13 · 17 · 113 · 35,906,175,756,150,593`.
- evidence: `evidence/A164326_a17_2071342181735785633264590.json`

### A164326 a(18) = 9,606,289,803,039,023,735,440,800 — 08:06

- **run 18**: `35·k − 1 = 336,220,143,106,365,830,740,427,999`. **stopper**
  `37·k − 1 = 355,432,722,712,443,878,211,309,599 = 19 ×
  18,706,985,405,918,098,853,226,821`.
- **certificates**: every value past the bound (`k_proof(18) =
  9.48×10²²`); all 18 by BLS75 Theorem 15, all re-verified.
- **model**: from `a(17)`, median `7e+25`; `k / median = 0.14`,
  `E = 0.12` — early, only 4.6× `a(17)`. 6.6 h in, at `5.4×10²⁰ k/s`
  over the `n = 18` phase.
- `k = 2⁵ · 3² · 5² · 7³ · 11 · 13 · 17 · 32,803 · 48,778,736,311`.
- evidence: `evidence/A164326_a18_9606289803039023735440800.json`

`E` averages 0.67 over the two; `k / median` 1.97, 0.14. Over the
family's four searched terms it is 1.23.

### A bound: A164326 a(19) > 16,049,280,642,737,212,898,317,290

The filter moved to `n = 19` and the sweep ran 56 minutes more at
`1.9×10²¹ k/s`, to period 8,346, where the campaign was stopped by hand:
no `k < 1.6049×10²⁵` has `(2r−1)·k − 1` prime for all `r = 1..19`. Above
the crossing the classification is a probable-prime chain, which can only
lengthen a run, never hide one, so the bound stands. The model, from
`a(18)`, had given `a(19)` 0.3% under this cursor and puts its
median at `8.01e+27`; the campaign resumes from here.

## A088651 under the v3 ceiling: a(17) — 2026-09-04

The ninth campaign, `--family A088651` with no flags, resumed from the
family's v2 cursor (period 101, `k = 1.942×10²³` — the crossing at
`n = 17` its twelve-minute v2 run had stopped at) and was left running
through 2026-09-04. It found `a(17)` at 10:29 and then swept on at
`n = 18` to `1.388×10²⁶`, where the v4 engine took the cursor over the
next day. The find is past the deterministic bound on every value but
one, so it is proved by the **N+1 route**, and it was re-verified from
disk exactly as the earlier files were.

### A088651 a(17) = 1,834,211,334,301,046,929,508,280 — 2026-09-04, 10:29

- **run 17**: `r·k − 1` prime for `r = 1..17`; the 17th value is
  `17·k − 1 = 31,181,592,683,117,797,801,640,759`.
- **stopper**: `18·k − 1 = 33,015,804,017,418,844,731,149,039 = 19 ×
  1,737,673,895,653,623,406,902,581`.
- **certificates**: `k` is 9.4× past the proof crossing `k_proof(17) =
  1.951×10²³` (the v2 ceiling this family stopped at). One value under
  the bound (`r = 1`) by `deterministic-mr`; the other sixteen by
  **BLS75 Theorem 15** on `N + 1 = r·k` factored completely, each with
  its own Lucas sequence and one shared discriminant. All 17 re-verified
  from scratch by the launcher and again from disk.
- **also settles**: `A202779(17) = 1,834,211,334,301,046,929,508,280`
  (the run is exact).
- **model**: from `a(16)`, median `1.86×10²⁴`; `k / median = 0.99`,
  `E = 0.69`. From the v2 bound it is `k / median = 0.83`, `E = 0.59`;
  the pre-run model had given `a(17)` 9.6% of sitting under the old
  ceiling, and it landed 9.4× above it.
- `k = 2³ · 3 · 5 · 7 · 11 · 13 · 17 · 331,213 · 2,711,925,492,389`.
- evidence: `evidence/A088651_a17_1834211334301046929508280.json`

## The v4 legs: five more terms, and every bound moved — 2026-09-05

The window sieve went into service on 2026-09-05 (README.md, "The
mathematics of the engine"; [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md)
v4) and all seven campaigns were resumed on it in turn, each from its own
cursor with no flags, for about six and a half hours of device between
them. Four of the seven paid: A088651 and A088250 one term each,
A125838 one and A125839 two. The three that did not — A173750, A164325
and A164326 — were each given a handful of segments (25 to 70 seconds)
and moved their bounds a little. Every value of all five finds lies past
the deterministic bound, so all 89 certificates are BLS75 — Theorem 1 on
`N − 1` for A088250, Theorem 15 on `N + 1` for the three −1 families —
and each file was re-verified from disk before this page was written.

### A088651 a(18) = 152,058,443,198,637,095,680,139,580 — 14:38

- **run 18**: `r·k − 1` prime for `r = 1..18`; the 18th value is
  `18·k − 1 = 2,737,051,977,575,467,722,242,512,439`, the largest
  integer this project has certified.
- **stopper**: `19·k − 1 = 2,889,110,420,774,104,817,922,652,019 = 29 ×
  99,624,497,268,072,579,928,367,311`.
- **certificates**: every value past the bound; all 18 by **BLS75
  Theorem 15**, all re-verified. No factor of `k` needed a subproof.
- **also settles**: `A202779(18) = 152,058,443,198,637,095,680,139,580`.
- **model**: from `a(17)`, median `2.21×10²⁶`; `k / median = 0.69`,
  `E = 0.53`.
- **when**: the leg picked the cursor up at `1.388×10²⁶`, where the v3
  campaign had left it, and ran about 51 minutes — the 32 from the
  `a(18)` banner to the checkpoint are on the clock at
  `3.13×10²² k/s` over the `n = 19` phase, against `2.91×10²²`
  calibrated.
- `k = 2² · 3 · 5 · 7 · 11 · 13 · 17 · 19 · 6,579,899 · 1,191,251,504,809`.
- evidence: `evidence/A088651_a18_152058443198637095680139580.json`

### A088250 a(18) = 11,260,441,017,037,317,719,293,680 — 15:20

- **run 18**: `r·k + 1` prime for `r = 1..18`; the 18th value is
  `18·k + 1 = 202,687,938,306,671,718,947,286,241`.
- **stopper**: `19·k + 1 = 213,948,379,323,709,036,666,579,921 = 29 ×
  7,377,530,321,507,208,160,916,549`.
- **certificates**: every value past the bound (`k_proof(18) =
  1.84×10²³`); all 18 by **BLS75 Theorem 1** on `N − 1 = r·k`, `k`
  factored once, every prime factor under the bound, all re-verified.
  The first A088250 find with no deterministic certificate in it.
- **also settles**: `A202778(18) = k` and `A071576(18) =
  5,630,220,508,518,658,859,646,840`.
- **model**: from `a(17)`, median `2.18×10²⁶`; `k / median = 0.052`,
  `E = 0.07` — the earliest draw in the project. The pre-run model had
  given `a(18)` 4% of lying under the v2 ceiling; it lies 3.4× above it,
  which is nine minutes of v4 sweep.
- **when**: 9.2 minutes into the leg, which swept `3.3168×10²⁴` to
  `1.1438×10²⁵` at `1.44×10²² k/s` over the `n = 18` phase against
  `1.385×10²²` calibrated.
- `k = 2⁴ · 3 · 5 · 7 · 11 · 13² · 17 · 19 · 37 · 16,729 · 41,579 ·
  433,729`.
- evidence: `evidence/A088250_a18_11260441017037317719293680.json`

### A125838 a(19) = 112,258,928,035,903,409,184,283,860 — 19:44

- **run 19**: `r·k − 1` prime for `r = 2..19`; the 19th value is
  `19·k − 1 = 2,132,919,632,682,164,774,501,393,339`.
- **stopper**: `20·k − 1 = 2,245,178,560,718,068,183,685,677,199 = 19 ×
  118,167,292,669,372,009,667,667,221`.
- **certificates**: every value past the bound; all 18 by BLS75
  Theorem 15, all re-verified — the family's first non-deterministic
  file.
- **model**: from `a(18)`, median `8.52×10²⁵`; `k / median = 1.32`,
  `E = 0.84`.
- **when**: 4.16 h into the leg, the longest of the seven, which swept
  `1.7305×10²³` to `1.1240×10²⁶` at `7.5×10²¹ k/s` over the `n = 19`
  phase against `6.97×10²¹` calibrated.
- **it bounds A125839 at the same index**, as every A125838 term does:
  `A125839(19) ≤ 1.1226×10²⁶`, and the value found three hours later
  came in 39× under it.
- `k = 2² · 3 · 5 · 7² · 11 · 13 · 17 · 23 · 29 · 23,548,473,925,778,447`.
- evidence: `evidence/A125838_a19_112258928035903409184283860.json`

### A125839 a(19) = 2,894,601,427,937,540,670,809,460 — 22:06

- **run 19**: `r·k − 1` prime for `r = 3..19`; the 19th value is
  `19·k − 1 = 54,997,427,130,813,272,745,379,739`.
- **stopper**: `20·k − 1 = 57,892,028,558,750,813,416,189,199 = 19 ×
  3,046,948,871,513,200,706,115,221`.
- 17 BLS75 Theorem 15 certificates, all past the bound, all re-verified.
- **model**: from `a(18)`, median `1.11×10²⁴`; `k / median = 2.6`,
  `E = 1.38`. Bound from A125838's `a(19)`: `≤ 1.12×10²⁶`.
- **when**: 20 minutes into the leg, over an `n = 19` phase at
  `2.24×10²¹ k/s` against `2.286×10²¹` calibrated.
- `k = 2² · 3 · 5 · 7 · 11² · 13 · 17 · 421 · 9,743 · 62,832,890,531`.
- evidence: `evidence/A125839_a19_2894601427937540670809460.json`

### A125839 a(20) = 19,653,405,164,609,436,282,292,230 — 22:43

- **run 20**: `20·k − 1 = 393,068,103,292,188,725,645,844,599`.
- **stopper**: `21·k − 1 = 412,721,508,456,798,161,928,136,829 = 193 ×
  2,138,453,411,693,254,725,016,253`.
- 18 BLS75 Theorem 15 certificates, all re-verified.
- **model**: from `a(19)`, median `1.01×10²⁶`; `k / median = 0.20`,
  `E = 0.18` — early, only 6.8× `a(19)`.
- **when**: 37 minutes after `a(19)`, over an `n = 20` phase at
  `7.6×10²¹ k/s`. The filter then promoted to `n = 21`, where the prime
  19 is forced for a `3..n` family (the closed-form thresholds in
  [README.md](README.md#the-mathematics-of-the-engine)) and the rate
  jumped 4× to `3.2×10²²`.
- `k = 2 · 3 · 5 · 7 · 11 · 13 · 17 · 19 · 29 · 103,567 · 674,622,091,469`.
- evidence: `evidence/A125839_a20_19653405164609436282292230.json`

Across the five v4 finds `E` averages 0.60 and `k / median` runs 0.69,
0.052, 1.32, 2.6, 0.20 — the same one-draw-at-a-time scatter, with a
draw at a twentieth of its median (A088250's `a(18)`) and one at 2.6
times it (A125839's `a(19)`) landing seven hours apart on the same
engine.

### The bounds after the v4 legs

Each leg stopped at a segment boundary, so each family's coverage claim
is the last whole segment it swept. Every classification above each
family's proof crossing is a seven-base strong probable-prime chain, and
the searched-empty claim is sound there for the reason every section
above gives: a composite that passes the chain can only *lengthen* a
run, never hide one, so a true run of `n` would have passed every test,
been claimed, and then been proved by certificate.

| family | open next | searched empty below | at filter | the term it follows |
|---|---|---|---|---|
| A088250 | a(19) | **`1.1438×10²⁵`** | n = 19 | a(18), found 9 min earlier |
| A173750 | a(20) | **`4.5473×10²⁴`** | n = 20 | a(18) = a(19) |
| A125838 | a(20) | **`1.1240×10²⁶`** | n = 20 | a(19) |
| A125839 | a(21) | **`5.9486×10²⁵`** | n = 21 | a(20) |
| A164325 | a(19) | **`4.3012×10²⁴`** | n = 19 | a(18) |
| A164326 | a(19) | **`1.6541×10²⁵`** | n = 19 | a(18) |
| A088651 | a(19) | **`2.1310×10²⁶`** | n = 19 | a(18) |

In full: no `k < 11,438,501,323,067,410,989,827,430` has `r·k + 1` prime
for all `r = 1..19`; none under `4,547,328,228,114,712,891,400,550` for
`r = 2..20`; none under `112,400,724,549,314,962,454,754,060` has
`r·k − 1` prime for all `r = 2..20`, none under
`59,486,359,713,071,030,627,547,660` for `r = 3..21`, and none under
`213,107,220,648,992,003,638,684,380` for `r = 1..19`; and no
`k < 4,301,214,903,294,973,673,599,590` (respectively
`16,541,507,292,376,691,333,919,210`) has `(2r−1)·k + 1` (respectively
`(2r−1)·k − 1`) prime for all `r = 1..19`.

## The census

Counts per run length from each checkpoint, as printed in every
`[STATUS]` line (the finds themselves are included at their run lengths):

    A088250   8: 11478  9: 4124  10: 1512  11: 528  12: 177  13: 79
              14: 30  15: 4  16: 1  17: 1  18: 1     near 8    survivors 66,977,219
    A125838   8: 189204  9: 64256  10: 21508  11: 7337  12: 2565  13: 872
              14: 300  15: 118  16: 21  17: 7  18: 3  19: 1
                                                     near 42   survivors 593,087,062
    A125839   8: 299717  9: 105746  10: 37490  11: 13232  12: 4890  13: 1717
              14: 570  15: 242  16: 106  17: 13  18: 5  19: 1  20: 1
                                                     near 43   survivors 245,943,799
    A173750   8: 19737  9: 7284  10: 2777  11: 1089  12: 356  13: 132
              14: 45  15: 18  16: 5  17: 1  19: 1     near 5    survivors 30,702,076
    A164326   8: 25218  9: 8849  10: 3063  11: 1109  12: 361  13: 116
              14: 50  15: 10  16: 6  17: 1  18: 1     near 7    survivors 172,082,499
    A164325   8: 3760  9: 1334  10: 474  11: 170  12: 61  13: 23
              14: 8  15: 4  16: 2  17: 1  18: 1       near 1    survivors 20,804,547
    A088651   8: 42051  9: 13643  10: 4600  11: 1504  12: 444  13: 165
              14: 47  15: 15  16: 4  17: 2  18: 1     near 5    survivors 443,352,040

A value that reached the settled frontier and no further while a term was
open is a `[NEAR]` line; everything shorter is a count and nothing else.
1.57 billion survivors were classified across the seven campaigns, and
every one of them is in exactly one of these counts. Within a family the
shape is the model's — each extra rung costs a factor of about 2.7–3.0
at these heights, on every one of the seven — which is the check the
census exists for: the intensity is right even where a first occurrence
lands early or late.

## The campaigns against their benchmarks (the rule 5g acceptance test)

From the evidence timestamps and the checkpoints, per filter. A088250:

| filter | line swept | wall clock | campaign rate | benchmark ([BENCHMARKS.md](BENCHMARKS.md)) |
|---|---|---|---|---|
| n = 15 (period 0) | `1.92×10²¹` | 65 s, pool sizing included | `3.0×10¹⁹ k/s` | `3.07×10¹⁹` |
| n = 16 | `8.5×10²²` | 10.1 min | `1.4×10²⁰` | `1.38×10²⁰` |
| n = 17 | `9.6×10²³` | 39.2 min | `4.1×10²⁰` | `3.99×10²⁰` |
| n = 18 | `2.27×10²⁴` | 25.4 min | `1.49×10²¹` | `1.45×10²¹` |

Every phase ran at its benchmark's rate with no flags; the whole campaign
took 1.26 h against the 2.5 h budgeted at the medians, because `a(17)`
landed at half its median and the remaining line was swept at the n = 18
rate. A125838 (its `a(15)` and `a(16)` both lie in period 0, so the
filter went straight from 15 to 17 at that period's close):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 15 (period 0) | `1.92×10²¹` | 210 s, pool sizing included | `9.2×10¹⁸ k/s` | `8.4×10¹⁸` (`SCOREM`) |
| n = 17 | `4.42×10²²` | 10.2 min | `7.2×10¹⁹` | `6.5×10¹⁹` (paired, below) |
| n = 18 | `2.88×10²²` | 73 s | `4.0×10²⁰` | `3.99×10²⁰` (`SCORE17`) |
| n = 19 | `9.8×10²²` | 136 s | `7.2×10²⁰` | `7.2×10²⁰` (half of A088250's n = 18) |

A125839 (`a(16)` and `a(17)` both in period 0, so the filter went from
16 to 18 at its close):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 16 (period 0) | `1.92×10²¹` | 3.4 min, pool sizing included | `9.4×10¹⁸ k/s` | `8.4×10¹⁸` (`SCOREM`) |
| n = 18 | `5.77×10²¹` | 82 s | `7.0×10¹⁹` | `6.5×10¹⁹` (paired) |
| n = 19 | `1.65×10²³` | 10.3 min | `2.7×10²⁰` | `2.4×10²⁰` (paired) |

A173750 (a +1 family whose rungs start at 2, so its wheel lags A088250's
by one filter the same way):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 16 (period 0) | `1.92×10²¹` | 65 s, pool sizing included | `3.0×10¹⁹ k/s` | `3.07×10¹⁹` (`SCORE`) |
| n = 17 | `6.73×10²²` | 15.4 min | `7.3×10¹⁹` | `6.5×10¹⁹` (paired, as A125839's n = 18) |
| n = 18 | `7.88×10²²` | 194 s | `4.1×10²⁰` | `3.99×10²⁰` (`SCORE17`) |
| n = 20 | `3.17×10²⁴` | 17.4 min | `3.0×10²¹` | `2.8×10²¹` (A088250 n = 19, Measurement 7) |

A164326 (the odd multipliers, a −1 family):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 15 (period 0) | `1.92×10²¹` | 145 s, pool sizing included | `1.3×10¹⁹ k/s` | `1.25×10¹⁹` (Measurement 7) |
| n = 16 | `9.6×10²¹` | 236 s | `4.1×10¹⁹` | `3.75×10¹⁹` (Measurement 7, on the +1 twin) |
| n = 17 | `8.84×10²²` | 454 s | `1.95×10²⁰` | `1.82×10²⁰` (paired against A088250's n = 17: 0.49×) |

A164325 (the odd multipliers, a +1 family):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 16 (period 0) | `1.92×10²¹` | 49 s, pool sizing included | `3.9×10¹⁹ k/s` | `3.75×10¹⁹` (Measurement 7) |
| n = 17 | `3.17×10²³` | 27.5 min | `1.93×10²⁰` | `1.82×10²⁰` (paired) |
| n = 18 | `1.94×10²³` | 368 s | `5.3×10²⁰` | `4.9×10²⁰` (paired) |
| n = 19 | `2.80×10²⁴` | 25.7 min | `1.82×10²¹` | `1.8×10²¹` (paired, OPTIMIZATION_LOG.md) |

A088651 (A088250's multipliers, unit 510510):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 16 | `4.42×10²²` | 320 s, pool sizing included | `1.38×10²⁰ k/s` | `1.44×10²⁰` (Measurement 7) |
| n = 17 | `1.50×10²³` | 383 s | `3.9×10²⁰` | `3.75×10²⁰` (paired: 1.01× of A088250's n = 17) |

A164326 again, resumed under v3 (2026-09-04, 01:29–09:02, 7.54 h; the
phases from the evidence timestamps and the checkpoint):

| filter | line swept | wall clock | campaign rate | the engine at that filter |
|---|---|---|---|---|
| n = 17 (from the v2 cursor) | `1.97×10²⁴` | 2.73 h | `2.0×10²⁰ k/s` | `1.85×10²⁰` (v3 harness) / `1.95×10²⁰` (the v2 campaign) |
| n = 18 | `7.54×10²⁴` | 3.88 h | `5.4×10²⁰` | `4.9–5.3×10²⁰` (A164325's n = 18, paired) |
| n = 19 | `6.44×10²⁴` | 56 min | `1.9×10²¹` | `1.8×10²¹` (A164325's n = 19, paired) |

And the **v4 legs of 2026-09-05**, each from its own cursor with no
flags, against the rate the same checkpoint calibrated to before the leg
ran (OPTIMIZATION_LOG.md v4, Measurement 5 — the acceptance test of
CLAUDE.md 5g, now run on a resumed campaign that went on to find
something):

| family, filter | line swept | wall clock | campaign rate | calibrated beforehand |
|---|---|---|---|---|
| A088651 n = 19 (after `a(18)`) | `6.105×10²⁵` | 32.5 min | `3.13×10²² k/s` | `2.91×10²²` (measured after the leg) |
| A088250 n = 18 | `7.94×10²⁴` | 9.2 min | `1.44×10²²` | `1.385×10²²` |
| A125838 n = 19 | `1.1209×10²⁶` | 4.16 h | `7.49×10²¹` | `6.97×10²¹` |
| A125839 n = 19 | `2.72×10²⁴` | 20.3 min | `2.24×10²¹` | `2.286×10²¹` |
| A125839 n = 20 | `1.676×10²⁵` | 36.8 min | `7.58×10²¹` | — (one filter on from the calibration) |
| A125839 n = 21 | `3.983×10²⁵` | 21.0 min | `3.15×10²²` | `2.89×10²²` (measured after the leg) |

Every one is inside 10% of the engine's rate for its filter, on both
sides of the line — the calibration is a one-second sample and the
campaign figure a whole phase. The three legs that found nothing
(A173750, A164325, A164326) were 25 to 70 seconds each, two to five
segments, and are too short for a rate to mean anything; their bounds
moved by exactly the segments they swept. A125839's leg is the one to
read for the promotion behaviour: three filters in 78 minutes, the rate
rising 2.24×10²¹ → 7.6×10²¹ → 3.16×10²² as `a(19)` and `a(20)` landed
and the prime 19 became forced at `n = 21`.

Every phase of all eight v2/v3 campaigns and all seven v4 legs ran at
the engine's rate for its filter. The rates on the `2..n` and `3..n` families' later filters are **not** the
A088250 rates at the same form count, and reading them as such first
looked like a 0.5× slowdown; a paired engine check
([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md), "What the campaigns
measured") showed the kernels identical and the wheel twice as dense. A
family whose rungs start at 2 or 3 forces each small prime one or two
filters later than the `1..n` family does (the thresholds in
[README.md](README.md#the-mathematics-of-the-engine)): at A125838's
`n = 17` the prime 17 is not yet forced and keeps two residues in the
wheel where A088250's `n = 16` keeps one, so there are twice the
candidates per unit of line at the same kernel rate. The same holds at
A125838's `n = 19` (the prime 19) and A125839's `n = 18` and `n = 19`
(17 and 19). The odd families have the same property from `n = 17` on
for a different reason: their multipliers `1, 3, …, 2n − 1` cover only 16
nonzero residues modulo 19, 23, 29 and 31 at `n = 17` where `1..17`
cover all 17, so their first wheel level holds `81,900` residues to
A088250's `40,320` and their rate there is 0.49× of A088250's (paired,
same kernel). The v1 log's "the density is a function of the form count
and nothing else" is true only between filters in the same forcing
state, and BENCHMARKS.md's sibling table now says so.

## What is open now

**The cluster has been swept to a common frontier, and the project is
PAUSED there.** Sixteen campaign legs over three days took all seven
families from the 2017 literature to a frontier of this project's own,
28 terms in all, and every one of the next terms now sits above a
searched-empty bound that this project put there. What changed at the
end is not the engine but the *price*: the seven open terms have medians
between `8×10²⁷` and `1.4×10²⁸`, five days of device each at the v4
rates below, and none of them is worth a night any more.

| family | frontier (all this project's) | open next | searched empty below | resumes at | rate there | median from the bound |
|---|---|---|---|---|---|---|
| A088250 | **a(18) = 11,260,441,017,037,317,719,293,680** | a(19) | `1.1438×10²⁵` | n = 19 | `2.88×10²² k/s` | `1.2×10²⁸` |
| A173750 | **a(18) = a(19) = 147,316,106,448,079,863,444,150** | a(20) | `4.5473×10²⁴` | n = 20 | `2.90×10²²` | `1.3×10²⁸` |
| A125838 | **a(19) = 112,258,928,035,903,409,184,283,860** | a(20) | `1.1240×10²⁶` | n = 20 | `2.90×10²²` | `1.3×10²⁸` |
| A125839 | **a(20) = 19,653,405,164,609,436,282,292,230** | a(21) | `5.9486×10²⁵` | n = 21 | `2.89×10²²` | `1.4×10²⁸` |
| A164325 | **a(18) = 511,721,589,397,871,969,516,400** | a(19) | `4.3012×10²⁴` | n = 19 | `1.84×10²²` | `8.0×10²⁷` |
| A164326 | **a(18) = 9,606,289,803,039,023,735,440,800** | a(19) | `1.6541×10²⁵` | n = 19 | `1.83×10²²` | `8.1×10²⁷` |
| A088651 | **a(18) = 152,058,443,198,637,095,680,139,580** | a(19) | `2.1310×10²⁶` | n = 19 | `2.91×10²²` | `1.3×10²⁸` |

The rates are each family's own next launches, calibrated on its real
checkpoint after the campaigns stopped (about a second of device each,
nothing recorded; OPTIMIZATION_LOG.md v4, Measurement 6). Every one is a
pool of 1 and about 13,100 survivors a second: the filters are deep
enough now that the host is idle and the device is the whole cost.

**Why the cluster stops here rather than at a wall.** Nothing is in the
way. The ceiling is `10⁴⁰` and the deepest bound is `2.1×10²⁶`, fourteen
orders of magnitude under it; the certificate route works on both signs
and every one of the last five finds used it; the engine is at 2.2–2.5
`×10¹²` candidates a second and its own bottleneck is load latency, not
arithmetic. What has changed is the odds. From each bound, at the rate
of the filter it resumes at, the model puts the next term under a
nine-hour sweep with probability **9–11% for every one of the seven** —
0.09 to 0.11 expected terms a night, against the 1.1 a night that
A164326, A125839 and A088651 were worth two days ago and delivered on.
The cheap terms are gone; the next one anywhere in the cluster is a
five-day run at the median, and about three weeks of device would be a
fair budget for one term (read the medians as floors: this project's own
finds landed at 0.01× to 7.9× them).

**What a resumed campaign would need.** Nothing new to be correct — every
campaign resumes from its checkpoint with `python launch.py --family
<name>` and continues under the same ceiling, at the rates above, with
its census and finds intact. To be *worth* resuming it would want
another engine factor of the size v4 delivered, and the log prices the
leftovers ([OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v4): the load
chain the sieve is bound by, and the tail rounds that are now the
larger share at these filters. A 10× would put a term a night back on
the table.

**The bounds hold above the crossing, on both signs.** Every family now
sweeps past its proof crossing, where the classification is a seven-base
strong probable-prime chain. The searched-empty claim is sound there for
the reason the sections above give: a composite that passes the chain
can only *lengthen* a run, never hide one, so a true run of `n` would
have passed every test and been claimed — and then proved by certificate
(BLS75 Theorem 1 on `N − 1 = m·k` for the +1 families, Theorem 15 on
`N + 1 = m·k` for the −1 ones, `k` factored once, subproofs for any
factor past the bound, every proof re-verified before the evidence file
is written). The census above the crossing is a count of probable-prime
runs; the `[NEAR]` line is a health check on the cheap legs; only a
discovery is certified. Where each campaign stands is read with
`python launch.py --status --family <name>`, which touches nothing.

## What the twenty-eight terms cost, and what they scored

| | v2 (2026-09-03/04) | v3 (2026-09-04) | v4 (2026-09-05) | all |
|---|---|---|---|---|
| campaigns | 7 | 2 | 7 | 16 legs |
| device | 3.8 h | ~34 h | ~6.5 h | ~44 h |
| terms | 20 | 3 | 5 | **28** (on 27 files) |
| certificates | 302 (261 `deterministic-mr`, 41 BLS75 thm 1) | 52 (2, 50 thm 15) | 89 (0; 18 thm 1, 71 thm 15) | 443 |

The v3 figure is the two overnight resumes (A164326's 7.54 h, timed, and
A088651's, inferred from its checkpoint's cumulative 27.5 h less the legs
that are timed). Every term above was scored against the frontier it
followed, and over the 27 searched ones (the A173750 rider is not scored:
it was never searched for) `E` averages **1.08**, against the `Exp(1)`
mean of 1 the model would have if its intensity were exactly right — the
same answer G11 gets on the 46 published terms (0.86), from a completely
disjoint set of draws. `k / median` over the same 27 runs **0.008 to
7.9**, geometric mean 0.75: the intensity is right and the individual
draws are noisy over three orders of magnitude, exactly as the census
says. That is the whole claim the odds model makes, and it is the reason
the nine-hour probabilities above are worth acting on — and the reason
each is a floor, not a schedule.
