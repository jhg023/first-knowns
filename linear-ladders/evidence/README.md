# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`<family>_a<n>_<k>.json` (`A088250_a15_<k>.json`, `A125838_a15_<k>.json`,
…), plus a rolling ledger per family (`a088250_discoveries.json`, …).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present: 28 terms on 27 files**, with a ledger per family — the whole
of what this project found between 2026-09-03 and 2026-09-05, and the
frontier of all seven families.

| family | files | terms | found by |
|---|---|---|---|
| A088250 | 4 | `a(15)`–`a(18)` | the v2 campaign of 2026-09-03 (three) and its v4 leg of 2026-09-05 |
| A173750 | 3 | `a(16)`–`a(19)` | the 37-minute v2 campaign; one file settles `a(18)` and `a(19)` together (`settles = [18, 19]`) |
| A125838 | 5 | `a(15)`–`a(19)` | the 17-minute v2 campaign (four) and the 4.2-hour v4 leg |
| A125839 | 5 | `a(16)`–`a(20)` | the 15-minute v2 campaign (three) and the 1.3-hour v4 leg (two) |
| A164325 | 3 | `a(16)`–`a(18)` | the one-hour v2 campaign |
| A164326 | 4 | `a(15)`–`a(18)` | the 14-minute v2 campaign (two) and the 7.5-hour v3 resume of 2026-09-04 |
| A088651 | 3 | `a(16)`–`a(18)` | the 12-minute v2 campaign, the v3 resume of 2026-09-04, the v4 leg of 2026-09-05 |

Every A088250 and A088651 run is exact (the stopper at the next
multiplier is composite), so each of those files also settles A202778 or
A202779 at its own index, and A088250's settle A071576 at half their
value.

The 443 certificates in these files divide by where the value sits
against huntlib's deterministic Miller–Rabin bound: **263** are the
seven-base test itself (`deterministic-mr`), **59** are BLS75 Theorem 1
on `N − 1` (A088250's `a(17)` and `a(18)`, A164325's `a(17)` and
`a(18)`), and **121** are BLS75 Theorem 15 on `N + 1` — the −1 route,
which arrived with v3 on 2026-09-04 and carried A164326's `a(17)` and
`a(18)`, A088651's `a(17)` and `a(18)`, A125838's `a(19)` and A125839's
`a(19)` and `a(20)`. Six files (A088250 `a(18)`, A164326 `a(18)`,
A088651 `a(18)`, A125838 `a(19)`, A125839 `a(19)` and `a(20)`) have no
deterministic certificate in them at all: every value is past the bound.
No factor of any `k` here needed a subproof. Every file was re-verified
from disk before [RESULTS.md](../RESULTS.md) was written.

Because the conditions of every family nest, one `k` can settle several
terms at once. A find is evidenced **once**, under the first term it
settles, with a `settles` field listing all of them — a run of 17 on
A088250 while a(15) is open would produce a single `A088250_a15_<k>.json`
recording `a(15)`, `a(16)` and `a(17)`. The published tables show how
often that happens: A088250's `a(7) = a(8)`, A173750's
`a(12) = a(13) = a(14)`, A164325's `a(13) = a(14)`.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `sequence`, `forms`, `sign`, `k` and `run` — the claim, which family it
  belongs to, and how far the run reaches;
- `values` and `multipliers` — every `m·k + s` for the family's
  multipliers up to the run, written out in full, so the primality claims
  can be re-tested directly;
- `certificates` — one per value, each **re-verified from scratch before
  it is written**. Under huntlib's deterministic Miller-Rabin bound
  (`3.317×10²⁴`) a certificate is that seven-base test itself
  (`deterministic-mr`). Past the bound a `+1` value carries a BLS75
  Theorem 1 certificate (`bls75-thm1`): the complete factorization of
  `N − 1 = m·k` (the multiplier's own small factors folded in) and a
  witness per prime factor satisfying the two Pocklington conditions. A
  `−1` value past the bound (v3, 2026-09-04) carries a BLS75 Theorem 15
  certificate (`bls75-thm15`): the complete factorization of
  `N + 1 = m·k`, one discriminant `D` with Jacobi `(D/N) = −1`, and per
  prime `q` of it a Lucas sequence `(P, Q)` with `P² − 4Q = D`,
  `N | U_{N+1}` and `gcd(U_{(N+1)/q}, N) = 1`. On either route a prime
  factor above the bound is admitted only with a `subproofs` entry of
  its own — the same kinds of certificate one level down, so the tree's
  leaves are all deterministic tests (huntlib.certificate).
  `certificates_verified`, `unproved` and `proof_routes` say whether
  every value was proved and by which route;
- `stopper` — the value at the next multiplier, which must be
  **composite**, with the multiplier and a factor exhibited. This is what
  bounds the claim to exactly `run` rather than more, and it is the one
  number a reader can check on a calculator. The factor comes from a
  bounded effort (trial division, rho, 200 ECM curves; the full search
  only under `10³⁰`); a stopper that keeps its factors from that would
  be recorded with `factor: null`, composite by the strong test alone —
  a failed Miller-Rabin is a proof of compositeness;
- `verification` — the four legs the discovery protocol ran, each named;
- `also_settles` — what the find settles in the derived entries: for
  A088250, `A202778(run) = k` (the exact-run version, at the last index
  settled only; any rider index stays open there and is listed) and
  `A071576(n) = k/2` for every settled `n ≥ 3`; for A088651,
  `A202779(run) = k`;
- `least_claim` — the swept range from `K_START`, the wheel modulus and
  unit, the sieve depth and the monotonicity floor `a(n) ≥ a(n−1)`, which
  together say why no smaller `k` qualifies;
- `engine` — the exact configuration key that produced it.

The published claim in [RESULTS.md](../RESULTS.md) is written only after
each file is re-verified from disk: the protocol re-run independently,
every value re-tested with sympy, and the stopper's factorization
re-multiplied.
