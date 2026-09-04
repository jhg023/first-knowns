# RESULTS — linear-ladders (A088250 and its cluster)

Verified finds, in discovery order, with the exact integers and the
verification each one survived.

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
too: past `k_proof(18) = 1.84×10²³` the seven-base chain is a
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
under the deterministic bound and every certificate is the seven-base test
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
2.8×10²⁴`, just under it), so every certificate is the seven-base test;
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

## The census

Counts per run length from each checkpoint, as printed in every
`[STATUS]` line (the finds themselves are included at their run lengths):

    A088250   8: 9269   9: 3424   10: 1251   11: 443   12: 146   13: 70
              14: 26   15: 4   16: 1   17: 1      near 8    survivors 47,258,905
    A125838   8: 41999  9: 16395  10: 6236  11: 2483  12: 976  13: 370
              14: 137  15: 75  16: 7  17: 1  18: 1   near 40   survivors 48,139,929
    A125839   8: 90682  9: 35465  10: 13724  11: 5392  12: 2182  13: 822
              14: 298  15: 155  16: 73  17: 6  18: 1   near 40   survivors 39,888,590
    A173750   8: 19573  9: 7222  10: 2754  11: 1081  12: 353  13: 131
              14: 45  15: 18  16: 5  17: 1  19: 1     near 5    survivors 30,123,710
    A164326   8: 5822  9: 2265  10: 825  11: 314  12: 98  13: 31
              14: 20  15: 6  16: 1                    near 5    survivors 18,909,254
    A164325   8: 3679  9: 1312  10: 465  11: 170  12: 61  13: 23
              14: 8  15: 4  16: 2  17: 1  18: 1       near 1    survivors 20,005,808
    A088651   8: 2714  9: 1002  10: 381  11: 134  12: 38  13: 17
              14: 6  15: 3  16: 1                     near 2    survivors 11,126,630

A value that reached the settled frontier and no further while a term was
open is a `[NEAR]` line; everything shorter is a count and nothing else.

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

Every phase of all seven campaigns ran at the engine's rate for its
filter. The rates on the `2..n` and `3..n` families' later filters are **not** the
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

Every family was swept to its v2 ceiling; the frontier of each is now
this project's, and the next term of each is open above a searched-empty
bound. **v3 (2026-09-04) raised every ceiling to `10⁴⁰`** — one number
for all seven families, from the measured cost of a certificate rather
than from where a test stops being a proof — and each campaign resumes
from its v2 cursor at the filter after its frontier:

| family | frontier | open next | bound (swept empty) | resumes at | rate | median from the bound |
|---|---|---|---|---|---|---|
| A088250 | **a(17) = 1,048,124,771,278,912,649,231,910 (this project, 2026-09-03)** | a(18) | > `3.3168×10²⁴` | n = 18 | `1.45×10²¹ k/s` | `2.2×10²⁶` |
| A125838 | **a(18) = 74,882,388,347,598,051,560,340 (this project, 2026-09-03)** | a(19) | > `1.7305×10²³` | n = 19 | `7.2×10²⁰` | `8.6×10²⁵` |
| A125839 | **a(18) = 6,530,891,065,478,723,143,200 (this project, 2026-09-03)** | a(19) | > `1.7305×10²³` | n = 19 | `2.4×10²⁰` | `1.5×10²⁴` |
| A173750 | **a(18) = a(19) = 147,316,106,448,079,863,444,150 (this project, 2026-09-03)** | a(20) | > `3.3168×10²⁴` | n = 20 | `3.0×10²¹` | `1.3×10²⁸` |
| A164326 | **a(16) = 10,214,000,995,018,156,616,280 (this project, 2026-09-03)** | a(17) | > `9.998×10²²` | n = 17 | `1.8×10²⁰` | `1.05×10²⁴` |
| A164325 | **a(18) = 511,721,589,397,871,969,516,400 (this project, 2026-09-03)** | a(19) | > `3.3168×10²⁴` | n = 19 | `1.8×10²¹` | `7.9×10²⁷` |
| A088651 | **a(16) = 43,263,866,546,732,976,414,270 (this project, 2026-09-04)** | a(17) | > `1.942×10²³` | n = 17 | `3.75×10²⁰` | `2.2×10²⁴` |

**Where a night's sweep pays.** From each family's bound, at the
measured rate of its resumed filter and of the filters it promotes into
(the rates above; [OPTIMIZATION_LOG.md](OPTIMIZATION_LOG.md) v3 for the
c = 20 ones), the model's expected number of terms in nine hours of
sweep is **1.1 for each of A164326, A125839 and A088651** — `P(a(17))
= 94%`, `P(a(19)) = 93%`, `P(a(17)) = 93%` respectively, with about a
one-in-five chance of the term after it landing in the same night — and
0.24 for A125838, 0.20 for A088250, 0.02 each for A173750 and A164325.
Read every figure as a floor: the twenty finds here landed anywhere from
0.01× to 7.9× their medians, with the model's `E` averaging 1.2 over the
eighteen searched terms. Where each campaign stands is read with
`python launch.py --status --family <name>`.

**The bounds hold above the crossing, on both signs.** Every −1
family's v2 sweep stayed under its crossing, so those bounds rest on
proofs alone; from here every family sweeps past its crossing, where the
classification is a seven-base strong probable-prime chain. The
searched-empty claim is sound there for the reason the +1 sections
already give: a composite that passes the chain can only *lengthen* a
run, never hide one, so a true run of `n` would have passed every test
and been claimed — and then proved by certificate (BLS75 Theorem 1 on
`N − 1 = m·k` for the +1 families, Theorem 15 on `N + 1 = m·k` for the
−1 ones, `k` factored once, subproofs for any factor past the bound,
every proof re-verified before the evidence file is written). The
census above the crossing is a count of probable-prime runs; the
`[NEAR]` line is a health check on the cheap legs; only a discovery is
certified.
