# hl-records

> **Authorship disclaimer:** None of this code was written by me — it was
> entirely authored by **Claude (Anthropic's AI)** at my direction.
> **Codex (OpenAI)** contributed an independent static mathematical and
> optimization review on 2026-11-11, recorded in
> [codex-reviews](codex-reviews/README.md); that review changed no code and
> used no GPU.

A GPU hunt for new terms of [A331940](https://oeis.org/A331940): "Addends
k > 0 such that the polynomial x^2 + x + k produces a record of its
Hardy-Littlewood Constant." Eleven terms are known (…, 239621, 247757) and
the entry is tagged `more,hard` with the bound a(12) > 3·10^6. The engine
here proves "C(k) is not a record" for every k it passes — for all but
about one k in a thousand from a lower bound of the class number of the
discriminant 1 − 4k obtained in a class group, for the rest from the class
number itself, counted — so each new term comes with an unconditional
least-k claim. **Standing result ([RESULTS.md](RESULTS.md)): a(12) through
a(34) — twenty-three new terms, the first advance on the entry since its
eleven terms of 2020 — found and verified 2026-11-11 to 2026-11-14**, from
a(12) = 49840601 (C = 8.25096) to a(34) = 3314787117221 (C = 9.67330).
Three of them are discriminants Fung and Williams tabulated in 1990 —
a(17) = 160834691, a(20) = 398878547 and a(32) = 21425625701 — now proved
to be the least k with their C. `evidence/b331940.txt` is the b-file,
n = 1..34.

**Status: PAUSED — open to others** — built and validated 2026-11-11,
hunted by the owner from 2026-11-11 to 2026-11-14 (62.8 hours of campaign
clock), paused 2026-11-14 with every odd k < 4,149,500,444,673 swept and
a(35) open above it. a(35) ≤ 7514981191031, a value of Fung and Williams'
with C = 9.67581 above a(34)'s, about 3.2 days of sweep from the pause;
the model's median for a(35) is 4.5·10^12, though its tail now runs heavy
and the term is probably later ("The model", below). A fresh start sweeps
from k = 1 back to the pause in about 2.6 days at engine v4.1's rate on an
RTX 4090, rediscovering every term on the way.

**Engines.** Engine v3 (2026-11-11, after the Codex review) runs 5.4× engine v2
at k = 10^12 and 7.5× at 3·10^12, with the same census. Engine v4
(2026-11-12) raises the ceiling from k = 10^13 to 10^18 — every product
fits 64 bits for 4k − 1 < 2^62, and below 2^46 it makes engine v3's
decisions bit for bit at v3's speed — and splits a find's confirmations
over a short-lived pool: ~35 s at k = 2·10^10 where one process took six
minutes with the sweep waiting. Engine v4.1 (2026-11-12, after an Nsight
Compute profile of every kernel) makes v4's decisions bit for bit, 1.35×
faster at 3·10^12 and 1.44× at 10^13: the membership test of bound (3)
searches only as far as the order it already knows, and a float quotient
replaces a 64-bit division in the reduction of forms.

## The problem

For odd k the Bateman–Horn (Hardy–Littlewood Conjecture F) constant of
x^2 + x + k is the product over all primes p of (1 − ν(p)/p)/(1 − 1/p),
ν(p) the number of roots of x^2 + x + k modulo p. The prime 2 contributes
2, an odd prime contributes 1 − (D|p)/(p − 1) with D = 1 − 4k, so

    C(k) = 2 · prod over odd p of (1 − (D|p)/(p − 1)),

and C(k) = 0 for even k (the polynomial is always even). This is the C of
the entry's table: C(41) = 6.63955 = 2 × A221712. The entry lists the
record-setters 1, 11, 17, 41, 21377, 27941, 41537, 55661, 115721, 239621,
247757 (Pfoertner, 2020) and "a(12) > 3·10^6" (Pfoertner, January 2026).
It also notes Jacobson and Williams' k = 3399714628553118047 with
C = 10.73416, which bounds a(12) from above.

**A much smaller upper bound is in the literature.** Fung and Williams
(Math. Comp. 55, 1990), tabulated in Jacobson's 1995 thesis (Table 6.1),
give D = −398158363, that is k = 99539591, with their C(D) = 4.1579113.
This project recomputes C(99539591) = 8.3158226 > 8.24741 = C(247757), so
**a(12) ≤ 99539591** (gate S4 reproduces fifteen of their values to all 7
published decimals; one row of the thesis table has transposed digits and
one a misprinted discriminant, both noted in `hlc_search.py`). Their
further values bound the later records the same way: C = 8.5432 at
k = 160834691, 8.7234 at 398878547, 8.8650 at 1016793977, 9.2194 at
17959429571 and 9.4146 at 21425625701.

**Why a record is a least-k statement.** a(12) is the least k > 247757
with C(k) > C(247757), and each find moves the threshold to its own C. So
every k the hunt passes needs a proof that C(k) does not beat the standing
record. That proof is the whole design problem, because the product for C
converges only conditionally: no finite set of primes bounds it.

**What "function of the fundamental discriminant" means at a conductor.**
Write 4k − 1 = d·f² with d squarefree. A prime p dividing f has one root
of x^2 + x + k, so its local factor is 1, whatever the character of the
fundamental discriminant −d says there; the Belabas–Cohen script the entry
uses does the same (it divides the fundamental product by the local
factors at the primes of f). So C(k) can exceed the constant of its
fundamental discriminant: k = 68501 has 4k − 1 = 163·41² and
C = C(41)·40/39 = 6.8098. Non-fundamental k are therefore swept like any
other, with the right local factors.

## The mathematics of the engine

**1. The exact evaluation of one k.** Dividing the product by
L(1, χ) = prod (1 − (D|p)/p)^−1 leaves an absolutely convergent product,
and Dirichlet's class number formula gives L(1, χ) exactly from the class
number h(1 − 4k) (reduced primitive forms; w = 6 for k = 1, else 2):

    C(k) = 2w·sqrt(4k − 1) / (3π·h(1 − 4k)) · E(k),
    E(k) = prod over odd p not dividing 4k − 1 of e_p,
    e_p = 1 − 1/(p − 1)²  if (D|p) = +1,   1/(1 − 1/p²)  if (D|p) = −1.

Truncating E at the primes ≤ P costs a factor inside [e^(−t), e^t] with
t = 1.0001·(1 + 3/P)·(P(2) − the sum of 1/p² over p ≤ P), P(2) =
0.45224742… the sum of 1/p² over all primes (the prime zeta value): every
|log e_p| past 199 is at most 1.0001/(p − 1)². That is about 1/(P ln P);
with P = 2^20 the interval for C is 1.3·10^−7 wide, relatively, and with
2^28 4·10^−10. (Until 2026-11-11 the bound was 1/(3(P − 8)), the sum over
every integer ±1 mod 6, five times looser; OPTIMIZATION_LOG.md 2.13.) Cohen's method
(below) gives 30+ digits by a road that never touches h.

**2. The rigorous prune: C(k) above a threshold R forces a small class
number, and class numbers can be counted.** E(k) ≤ π²/8, so for k > 1

    C(k) > R   ⟹   h(1 − 4k) < π·sqrt(4k − 1) / (6R).

(Engine v3 sharpens this with the factors it knows: dividing each e_p at
the primes p ≤ 251 by its largest value 1/(1 − 1/p²) leaves 1 for an
inert p, 1 − 1/p² for p | 4k − 1 and 1 − 2/(p(p − 1)) for a split p, so
E(k) ≤ (π²/8)·Q(k) with Q the product of those ratios, and the bound on h
is multiplied by Q — by 2/3 already when 3 splits. Still no GRH and no
truncated product: every omitted ratio is at most 1. The Codex review's
HLC-001.)

The handoff's proposal — count reduced forms with small leading
coefficient as a lower bound for h, periodically in k — is **correct but
does not prune**: the forms with leading coefficient ≤ L number about
0.61·L(1, χ)·L, the bound to beat is 0.064·sqrt(4k − 1) at R = 8.25, so a
typical k needs L ≈ 0.2·sqrt(k) and a k near a record needs every form.
There is no fixed cutoff; the count needed grows like sqrt(k) per k, and
small split primes alone give only polylogarithmically many forms. What
that leaves is counting ALL of them, and for the discriminants here there
is a better way to count than forms:

**Gauss's three-squares theorem.** An integer ≡ 3 (mod 8) — and 4k − 1
is one for every odd k — has 24·H representations as a sum of three
squares, H its Hurwitz class number, and all three squares are odd. So
the number of ways to write 4k − 1 as a sum of three odd squares, taken
in non-increasing order and weighted 6, 3 or 1 by how many of the three
are equal, is exactly 3·H(4k − 1). The GPU engine can tabulate this for
2^23 consecutive k at a time: one thread per largest square and block of
middle squares walks the smallest squares whose sum lands in the window,
one atomic add per representation into a 16 MiB table that stays inside
the device's L2 cache. (Engine v1 did this for every k, and the gates,
the discovery recount and the opening band still do; engine v2 did it for
the k section 2a leaves, through a bitmap; engine v3 counts those k by
reduced forms instead — section 2b.) H determines
h(1 − 4k) exactly (H(d·f²) = h'(−d)·prod over p^e ∥ f of
(1 + (p − χ(p))(p^e − 1)/(p − 1)), and h(−d·f²) = h(−d)·prod p^(e−1)(p − χ(p))),
and without factoring gives h(1 − 4k) ≥ H(4k − 1)·prod over p | f of
(1 − 1/p).

**The survivor rule.** The device keeps k only if
3H(4k − 1)·ρ·2F < π·sqrt(4k − 1)·Q(k), with F = min(7.5, the standing
record) and ρ a lower bound of that last product (exact for conductor
primes up to 251, a proved 0.9923 for the at most two larger ones below
the ceiling). Every k it drops has C(k) ≤ F **unconditionally** — no
GRH, no truncated product. About 22 in a million odd k survive at
F = 7.5 (25 before Q: the k Q removes all have C below the floor, so the
census is the same); the host turns each survivor's count into the exact
h(1 − 4k) (the division by the conductor's factor must come out exact —
an integrity check on every survivor) and an interval for C, refined
through P = 199, 9973, 2^20, 2^22, 2^24, 2^26 and 2^28 only as far as the
decision needs (94% are settled at 199; the 30-digit analytic route that
remains past 2^28 is reached about once in 900,000 windows).

**2a. Most k never need their count: the class-group prefilter (engine
v2; in the fundamental discriminant since v3).** Write 4k − 1 = d·f² with
d squarefree. For d > 3 the rule's own quantity is exactly
3H(4k − 1) = 3·h(−d)·S(f), S(f) a known product over the primes of the
conductor f, and the rule is monotone in it, so k is dropped as soon as
ANY proved lower bound of h(−d) makes 3·bound·S(f) reach the threshold —
and a lower bound costs far less than the count. (The Codex review's
HLC-002: engine v2 worked in the larger group of −(4k − 1) and recovered
only part of S(f).) The classes of primitive forms of discriminant −d
form a finite abelian group G of order h(−d); with t the number of
distinct primes dividing d, genus theory says G has exactly 2^(t−1)
elements of order at most 2. Three bounds, each proved in
`hlc_search.py` and each a statement about one k:

1. a class of order m gives h ≥ m·2^(t−2) (the cyclic group it generates
   meets the 2^(t−1) elements of order ≤ 2 in at most two);
2. its square has order m' = m or m/2 and lies among the squares, so
   h ≥ 2^(t−1)·m';
3. if no power below the e-th of a second class's square lies in the
   subgroup generated by the first one's, then h ≥ 2^(t−1)·m'·e.

The classes used are those of the forms with a small prime that splits
for −d as leading coefficient. An order is established by baby steps and
giant steps: about 0.7·d^(1/4) compositions of forms per k (some 120
general ones and 590 multiplications by a prime form at k = 3·10^11)
against 0.13·sqrt(4k − 1) increments for the count — 200 times fewer
operations at that height, and they run in registers. Bound (3)'s test
that a power of the second class's square lies outside the first class's
squares is a discrete logarithm in the cyclic group the first class
generates, whose order m is by then known exactly, so its baby steps and
giant steps cover exponents below m, not below the bound being proved
(engine v4.1; v4 searched to the bound, and that stage took 3.4–4.8×
longer).
The factorization must be exact for the bounds to bite, so each 4k − 1
is trial-divided to its cube root and its cofactor tested (a square goes
to f; a base-2 strong probable prime, or a product of two primes, to d);
an undercounted t only weakens a bound.

At k = 10^12 the prefilter decides 99.87% of the odd k. The remaining
0.13% — every k whose class number really is small, and the k whose group
needs more than two generators — are counted exactly (2b); they are the
only k whose count the device knows, and they include every survivor.
**The survivor stream is identical to counting everything** (gate P6
compares the two on five windows to the ceiling), and a k dropped by the
prefilter is dropped by a proof about its own class group, not by a
property of its residue class: no wheel has been introduced.

**2b. The k the prefilter leaves are counted by leading coefficient
(engine v3; the Codex review's HLC-003).** A reduced form (a, b, c) of
discriminant 1 − 4k has odd a ≤ sqrt((4k − 1)/3), and for each a its b
are the square roots of 1 − 4k modulo a, each taken as its odd
representative in (−a, a]; the form is reduced when c ≥ a. Below
a = sqrt(4k − 1)/2 that condition holds for every root, so those a
contribute exactly 3·N(a), N(a) the number of roots — multiplicative in
a, read from one Legendre symbol per prime. That part never computes a
root, and every prefix of it is a lower bound of the count: the device
drops k as soon as a prefix reaches the rule, which it does for 99% of
the k it is handed, after about half of the range. For the rest (the
survivors, about a hundred a window) the band above sqrt(4k − 1)/2 is
counted root by root (Tonelli–Shanks, Hensel lifting, the Chinese
remainder theorem). One k per block of threads; at k = 10^12 it costs
about 7 µs a k against 1.9 s a window for the walk it replaced, which
visited every representation in the window to find the 0.3% it needed.
Gate P7 pins it to the three-squares count on 16,592 discriminants up to
the ceiling.

**3. No wheel.** Every known term from 41 on has k ≡ 2 (mod 3), and a
restriction to (D|3) = −1 alone would remove 77% of the work. It is not
used, because it is not provable: with (D|3) = +1, a record needs
L(1, χ) < 0.133, and the only unconditional lower bounds for L(1, χ) are
far too weak (the bound h ≥ the number of forms with leading coefficient
a power of 3 settles it only for 4k − 1 below about 4·10^4). Under GRH the
restriction looks provable from explicit bounds for L(1, χ)
(Lamzouri, Li and Soundararajan, 2015, sharpened by the known sign at 3),
and the same for 5 and 7; that would make every least-k claim conditional
on GRH and is **the owner's decision, not taken here** (OPTIMIZATION_LOG.md
prices it). Every odd k is swept.

**4. What is proved, and what the claim rests on.** A term a(n) found by
this campaign is claimed least on: Gauss's theorem and the class number
formula (classical); the bound E ≤ (π²/8)·Q and the Hurwitz relations
(elementary; `hlc_search.py` states them); composition of forms and genus
theory (Gauss), for the k dropped on a lower bound; the reduction theory
of binary quadratic forms, for the k counted by leading coefficient; and
the engine having computed correctly, which the gates police: the CPU
engine counts reduced forms by a sieve and must agree with the
three-squares count counter for counter; the device's count by leading
coefficient must agree with the three-squares count on every counter of
windows to the ceiling; the oracle counts forms from the definition; the
composition law is checked against its definition and the genus count
against an enumeration on 870 discriminants; the device's prefilter must
make the reference's decision bit for bit, and its stream must equal the
rule applied to every counter; every k the factors Q remove is
classified below the floor by the host; an analytic class number (a theta
series, no forms and no squares) checks sampled counts at every height
and, every 20 seconds of a campaign, one random k — alternately a counted
k and a k the prefilter or a partial count dropped.

**The discovery protocol** (three confirmations, any disagreement halts):
1. the engine's exact h(1 − 4k) and the rigorous interval for C, strictly
   above the standing record's;
2. Cohen's route (Belabas and Cohen's method, in mpmath/MPFR): C to 34
   digits from L(1, χ) and L(j, χ), j ≤ 10, by the approximate functional
   equation, with the tail of E summed through log ζ and log L — no class
   number enters, and w·sqrt(d)·L(1, χ)/(2π) must be the engine's class
   number to 20 decimals;
3. a second class-number algorithm: direct enumeration of the reduced
   primitive forms (for every k ≤ 10^12; above that it costs hours and
   the record says it was skipped), plus the device's recount at another
   alignment (to k ≈ 2.25·10^15, where the three-squares walk's counters
   end; above it the record says the recount was skipped and leg 2's
   analytic class number checks the count).

Measured on one core: the analytic leg is ~220 µs a term of its
approximate functional equation, ~sqrt(4k) terms — 25 s at k = 10^8, 76 s
at 10^9, ~6 minutes at a(32) = 21425625701, 40 at 10^12 — two thirds of it
in MPFR's incomplete gamma and erfc; the enumeration takes 0.8 s at 10^9
and 15 s at 1.8·10^10 and grows like k. **Both are sums**, so the launcher
splits them into chunks over a short-lived pool of processes (one per 20 s
of their measured cost, at most 12: per-process efficiency 0.97 at 8 and
0.95 at 12, 0.85 at 16) while this process does the device recount: about
35 s at a(32)'s height, 3.5 minutes at 10^12. Each chunk sums its terms
in exact fixed point, so the 34 digits do not depend on the number of
processes (a(12)'s published value is reproduced digit for digit by one
and by four). `--verify-workers N` caps the pool (1 = one process). The
sweep waits while a find is confirmed, and the heartbeat says how long;
Ctrl+C terminates the pool at once.

The evidence file records k under the entry's letter, C to 34 digits with
its error bound, the margin over the previous record, and the least-k
basis.

**Adaptations of the repo conventions** (this is neither a prime hunt nor
an exact count):

| convention | here |
|---|---|
| frontier | the number of terms settled; the threshold is the last term's C |
| `[DISCOVERY]` | a new record, a(n), verified 3-way, evidenced once |
| `[NEAR]` | C within 1% below the standing record; count re-derived analytically, not evidenced |
| census | counts of C per bin of 0.25 from 7.5, in every `[STATUS]` (`census 7.50:1137 7.75:414 8.00:128 …`) |
| canaries | a(1)..a(11) rediscovered in order from k = 1; no record in (247757, 3·10^6]; Fung and Williams' ten k between 1.5·10^7 and 2.2·10^10 met with their published C |
| parity | four pairs. Counts: CPU (reduced forms by a sieve, plain division and %) against GPU (three squares), every counter and every survivor on six populated windows to k = 4·10^9, and sampled analytic class numbers to 10^14; GPU against GPU, the count by leading coefficient (Barrett products, roots by Tonelli–Shanks) against three squares, every counter on eight windows to 6·10^13, and against 3h(−d)S(f) where 4k − 1 = d·f² was constructed (k ≈ 10^15 and 10^16). Prefilter: the CPU reference (Python integers, the textbook composition, dictionaries) against the device (wrapping 64-bit products, inverses modulo 2^64, a hashed table of giant steps), the decision bit for bit on seven windows to 9·10^13, constructed conductors, and constructed 4k − 1 at k ≈ 10^18. Stream: the production path against the survivor rule on every counter, six windows to 9·10^13 and a whole window at 10^14 (the SCORE_1E14 freeze) |
| ceiling | k = 10^18 (engine v4): 4k − 1 < 2^62 keeps every product of the prefilter and the sparse count in 64 bits, with the form table keyed in 16 bytes from k ≈ 5.3·10^13 and the characters of primes past 5.6·10^6 computed on the fly from k ≈ 2.3·10^13. No campaign meets it: at engine v4.1's rate the sweep reaches 10^13 in 8.5 days, 10^14 in about 290 and 10^15 in about 30 years (the rate goes like k^−0.5 up there). Engine v3's ceiling was 10^13, from its 2^46 arithmetic |
| host pool | one worker, for the sampled recounts (2% duty); classification is inline (2% of wall at 3·10^11, 1% at 10^12); a find's confirmations (and the rare 30-digit resolve) get a pool of their own for their minute or so, up to 12 processes, ramped and gone when they finish |
| rungs | quartiles of the next four open terms from the model, rebuilt on each find |

## The model

For odd k the residue of 1 − 4k modulo an odd prime is uniform, so the
model takes C as the random Euler product 2·prod (1 − ε_p/(p − 1)) with
independent ε_p = ±1 with probability (p − 1)/(2p) each and 0 with
probability 1/p — the model Granville and Soundararajan proved for the
distribution of L(1, χ). Its law is computed by exact convolution, not
simulated. **Validation, on what it did not help find:** over the 1.5·10^6
odd k ≤ 3·10^6 the counts of C above 6.0 / 6.5 / 7.0 / 7.25 / 7.5 / 7.75 /
8.0 are 2912 / 810 / 153 / 63 / 28 / 7 / 4 against 2831 / 783 / 165 / 67 /
24 / 8.0 / 2.3 modelled, and the seven known records after 41 sit at model
quantiles 0.98, 0.37, 0.25, 0.21, 0.44, 0.33, 0.02 given their
predecessors.

Records are then a walk: the next record is the first k with C above the
standing one (rate P(C > record)/2 per unit of k), its value drawn from
the tail, with the literature's k as anchors. **Predictions, stated before
any run** (`model_results.json`; clocks at engine v2's measured rate law,
BENCHMARKS.md — the quantiles do not depend on the engine and are
unchanged from the first statement):

| term | Q1 | median | Q3 | P90 | clock to the median |
|---|---|---|---|---|---|
| a(12) | 4.5·10^6 | 6.6·10^6 | 1.0·10^7 | 1.5·10^7 | < 1 s |
| a(13) | 1.1·10^7 | 1.7·10^7 | 3.0·10^7 | 6.0·10^7 | < 1 s |
| a(14) | 2.3·10^7 | 4.2·10^7 | 9.9·10^7 | 3.0·10^8 | < 1 s |
| a(15) | 5.0·10^7 | 1.1·10^8 | 3.4·10^8 | 1.3·10^9 | 1 s |
| a(17) | 2.5·10^8 | 7.9·10^8 | 3.6·10^9 | 1.8·10^10 | 16 s |
| a(19) | 1.3·10^9 | 5.7·10^9 | 2.1·10^10 | 2.0·10^11 | 3 min |
| a(21) | 7.1·10^9 | 2.5·10^10 | 2.8·10^11 | 2.4·10^12 | 20 min |
| a(22) | 1.7·10^10 | 9.6·10^10 | 8.4·10^11 | 7.9·10^12 | 1.9 h |
| a(23) | 2.7·10^10 | 2.7·10^11 | 2.6·10^12 | — | 7.9 h |
| a(24) | 8.9·10^10 | 7.2·10^11 | 7.7·10^12 | — | 1.4 days |
| a(25) | 2.3·10^11 | 1.9·10^12 | — | — | 6.3 days |

The model expects 8 new terms below 10^10 (6 minutes; 5 to 12 at the
10% and 90% points), 11 below 10^11 (2 hours) and 13 below 10^12 (2.3
days). a(12) is almost certainly far below the literature's 99539591.
**The term whose median clock first exceeds a day is a(24)**, at
k ≈ 7.2·10^11 (it was a(23) at engine v1's rate); the campaign's clock is
spent between 5·10^11 and 3·10^12, the SCORE shape sits at 10^12, and
that is where optimization measurements are taken.

**What happened, and the model from the cursor.** The first campaign
found 19 terms below 1.14·10^10 where the table expected 8: the model's
tail is thin at large C (over the 6.28·10^9 odd k swept, 731 / 165 / 25
values of C above 8.5 / 8.75 / 9.0 against 517 / 93 / 14 modelled), so it
places terms late. Conditioned on the checkpoint (a(30) = 11410046357,
C = 9.32896, swept to 1.26·10^10), at engine v3's rate:

| term | Q1 | median | Q3 | clock to the median |
|---|---|---|---|---|
| a(31) | 1.7·10^10 | 2.1·10^10 (the literature's bound) | — | 3 min |
| a(32) | 2.1·10^10 | 3.9·10^10 | 7.1·10^10 | 9 min |
| a(33) | 5.9·10^10 | 1.1·10^11 | 2.2·10^11 | 40 min |
| a(34) | 1.4·10^11 | 2.8·10^11 | 7.6·10^11 | 2.3 h |
| a(35) | 3.1·10^11 | 7.5·10^11 | 2.5·10^12 | 8.2 h |
| a(36) | 7.0·10^11 | 2.0·10^12 | 8.2·10^12 | 31 h |
| a(37) | 1.6·10^12 | 5.4·10^12 | — | 5.0 days |

**The term whose median clock first exceeds a day is now a(36)**, at
k ≈ 2.0·10^12; the clock to 10^13 is 11.7 days and is spent above 10^12,
the SCORE shape sits at 3·10^12, and that is where the next round is
measured. (a(31)..a(33) have since been found, at 21072785801,
21425625701 and 26853927251; the table above is the model as it stood at
a(30), and its re-fit is owed. Past 10^13, engine v4.1's measured rate
law puts 10^14 about 290 days in: SCORE_1E14 is frozen there.)

**From the cursor at round 4** (a(33) = 26853927251, C = 9.62408, swept to
8.03·10^11), at engine v4.1's rate:

| term | Q1 | median | Q3 | clock to the median |
|---|---|---|---|---|
| a(34) | 8.9·10^11 | 1.02·10^12 | 1.24·10^12 | 2.6 h |
| a(35) | 1.26·10^12 | 1.66·10^12 | 2.43·10^12 | 11 h |
| a(36) | 2.03·10^12 | 3.19·10^12 | 6.72·10^12 | 37 h |
| a(37) | 3.66·10^12 | 7.42·10^12 | 2.18·10^13 | 5.4 days |

a(36) is still the first term whose median clock exceeds a day (48 hours
at engine v4's rate), so 3·10^12 stays the SCORE shape, and a(37), at
7.4·10^12, is the next height measured (OPTIMIZATION_LOG.md round 4). The
model has run early so far, so these clocks are likely long.

**It did not: a(34) came late, and the far tail is now heavy.** a(34) =
3314787117221 (C = 9.67330) fell at the 99.97th percentile of the law
above, conditioned on a(33) and that cursor. Over all 2.07·10^12 odd k
below the pause, the census matches the model to 2% in the bins from 7.5
to 8.5 and then falls away from it: 0.94, 0.85, 0.67, 0.44 and 0.24 of the
modelled counts in the bins 8.50–8.75 through 9.50–9.75 (11 values of C in
the last bin against 45 modelled; RESULTS.md, "The census"). At
6.28·10^9 the same comparison had gone the other way (25 values above 9.0
against 14). The random Euler product is the law of L(1, χ) at a fixed
height only so far into its tail, and the census says where that stops
being true here: the model's re-fit to the census is owed before its
clocks are trusted past 9.5.

**At the pause** (a(34) = 3314787117221, C = 9.67330, swept to
4.15·10^12), the model as it stands, at engine v4.1's rate:

| term | Q1 | median | Q3 | P90 | clock to the median |
|---|---|---|---|---|---|
| a(35) | 4.30·10^12 | 4.51·10^12 | 4.89·10^12 | 5.37·10^12 | 7.3 h |
| a(36) | 4.92·10^12 | 5.60·10^12 | 6.92·10^12 | 9.94·10^12 | 1.3 days |
| a(37) | 6.24·10^12 | 8.21·10^12 | 1.42·10^13 | 3.53·10^13 | 3.9 days |

Its tail rate at C = 9.67330 is 3.8·10^−12 a k; the census's last bin
says the true rate there is about a quarter of that, which would put
a(35)'s median at 5.6·10^12, about 31 hours from the pause, and a(36)
and a(37) correspondingly further out.

## Running it

Requirements: Python 3 with NumPy, SymPy, mpmath, CuPy and a CUDA GPU
(developed on an RTX 4090); gmpy2 if present speeds the 34-digit leg
thirty-fold. `huntlib` is imported from the repository root.

```
python launch.py --selftest   # the gate battery; must end ALL GREEN (~3 min)
python score.py               # gates x the five frozen benchmark shapes (~4 min)
python launch.py --status     # reads the checkpoint, writes nothing
python launch.py              # THE HUNT -- the owner's command
```

The hunt runs until Ctrl+C or the ceiling; `--to K` and
`--stop-on-discovery` are opt-in stops; `--gpu-yield-ms N` and `--gentle`
trade a few percent for a quieter machine; `--verify-workers N` caps the
processes a find's confirmations use. It holds about 170 MiB of VRAM at
the cursor (the counters, 112 MiB of baby-step tables for the
prefilter's 57,344 resident threads, and 14 MiB of prime tables for the
sparse count, which grow with the height: 0.1–0.2 GiB at 10^15), plus a
224 MiB wide table once k passes 5.3·10^13, and one below-normal-priority
worker process.

## Trust

Built to [CONVENTIONS.md](../CONVENTIONS.md). Project-specific:

- **Proved unconditionally:** the normalization (all eleven table rows to
  5 decimals; A221712 to 40 digits); the survivor rule; the four bounds of
  the prefilter; that every k the device drops has C ≤ the floor, given a
  correct count or a correct order.
- **Gated, not proved:** that the device counts and composes correctly.
  The gates are listed above. The frozen fingerprints' survivor lists
  above k = 4·10^9 rest on the three-squares tabulation (engine v1
  counted everything, and v2 and v3 reproduce its list less the k the
  local factors prove below the floor), cross-checked by the count by
  leading coefficient, a second window layout, sampled analytic class
  numbers and the literature canaries (BENCHMARKS.md), because a second
  full tabulation at those heights costs O(k) per window on a CPU. The
  prefilter is pinned from both sides at those heights: its decision to
  the reference, its stream to the full tabulation.
- **Not done:** the levers of the round-4 profile (OPTIMIZATION_LOG.md
  4.5): the first pass of the prefilter is now about 69% of the window
  at 8 active lanes of 32 and bound by its tables' cache footprint, so a
  smaller table is the next lever, then the membership launches' layout
  (one job a thread, ~10%) and the sparse count's factor lookups (~12%);
  a cheaper wide form table (0.76× on the window from k ≈ 5.3·10^13, about
  100 days of sweep away; OPTIMIZATION_LOG.md 3.6 prices the options); a
  recorded no-flags acceptance test of engine v4.1 (the owner's v4.1 run
  from 8.03·10^11 to the pause found a(34), but its first `[STATUS]` lines
  are not recorded here); the model's re-fit to the census.
- **Above the walk** (k > 2.25·10^15, decades away): no full three-squares
  tabulation exists to check a window against, so the counts there rest
  on the arithmetic bounds of `hlc_gpu.py`'s header, on gate P8's
  constructed 4k − 1 with known class numbers, and on the analytic class
  number of every find.
- **Independent Codex review (2026-11-11):**
  [analysis and finding ledger](codex-reviews/README.md). Implemented and
  validated the same day as engine v3: the local Euler factors (HLC-001),
  the descent to the fundamental discriminant (HLC-002), the sparse exact
  count (HLC-003) and the validation contract (HLC-006); the squared-base
  order (HLC-004) measured and declined; published class numbers
  (HLC-005) and the confirmation enumerator deferred
  (OPTIMIZATION_LOG.md round 2).
- **Conditional on nothing.** The GRH-conditional wheel is an option the
  owner has not taken.
- Literature: Fung and Williams, Math. Comp. 55 (1990); Jacobson, master's
  thesis, Manitoba (1995); Jacobson and Williams, Math. Comp. 72 (2003);
  Cohen, "High precision computation of Hardy-Littlewood constants";
  Conrad, "Hardy-Littlewood constants" (2003); Granville and Soundararajan,
  GAFA 13 (2003).
