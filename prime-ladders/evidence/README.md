# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`A084700_a<n>_<k>.json` or `A084701_a<n>_<k>.json`, plus a rolling ledger
per family (`a084700_discoveries.json`, `a084701_discoveries.json`).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present:** eleven first occurrences. Five of A084700 — four from the
campaign of 2026-09-02, `A084700_a14_24581646307811670.json`,
`A084700_a15_1183192161007235610.json`,
`A084700_a16_161515890673488267840.json`,
`A084700_a17_2446970377116913184460.json`, and one from the campaign of
2026-09-03, `A084700_a18_416266897501398851227320.json` — with the
ledger `a084700_discoveries.json` that lists all five. Six of A084701,
all from the campaign of 2026-09-03, which ran from `k = 10⁶` to the
family's proof ceiling: `A084701_a12_43708752888360.json`,
`A084701_a13_2276961234558570.json`,
`A084701_a14_165784683394437030.json` (which settles `a(14)` **and**
`a(15)`, below), `A084701_a16_16739777598441148020.json`,
`A084701_a17_9050934616476845605590.json` and
`A084701_a18_23562434281685500120920.json` — with the ledger
`a084701_discoveries.json` that lists all six.

Because the conditions of both sequences nest, one `k` can settle several
terms at once. A find is evidenced **once**, under the first term it
settles, with a `settles` field listing all of them — a run of 16 on
A084700 while a(14) is open would produce a single `A084700_a14_<k>.json`
recording `a(14)`, `a(15)` and `a(16)`. It happened on 2026-09-03: a run
of 15 at `k = 165,784,683,394,437,030` arrived while A084701's `a(14)`
was open, so `A084701_a14_165784683394437030.json` carries
`settles: [14, 15]` and there is no `a15` file for that family. Both
sequences show how often that happens at small `k` as well: A084700's
`a(4) = 6` settled four terms at once and A084701's `a(5) = 120` settled
three.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `k`, `sign` and `run` — the claim, which family it belongs to, and how
  far the run reaches;
- `values` — every `prime(i)·k + s` for `i = 1..run`, written out in full,
  so the primality claims can be re-tested directly;
- `certificates` — one per value, each **re-verified from scratch before
  it is written**. Under huntlib's deterministic Miller-Rabin bound
  (`3.317×10²⁴`) a certificate is that seven-base test itself
  (`deterministic-mr`), which is what the four A084700 files of
  2026-09-02 and all six A084701 files carry for every value — the
  largest A084701 value, `61·k − 1` of its `a(18)`, is `1.4×10²⁴`, under
  the bound. Past the bound an A084700 value carries a BLS75
  Theorem 1 certificate (`bls75-thm1`): the complete factorization of
  `N − 1 = prime(i)·k` into primes each under the bound, and a witness
  `a_p` per prime factor satisfying the two Pocklington conditions
  (huntlib.certificate). The `a(18)` file is the first to need it: its
  values from `i = 5` on exceed the bound, so it carries four
  `deterministic-mr` certificates and fourteen `bls75-thm1` ones, all on
  the one factorization of `k`. `certificates_verified`, `unproved` and
  `proof_routes` in the file say whether every value was proved and by
  which route;
- `stopper` — the value at `i = run+1`, which must be **composite**, with
  the rung prime and a factor exhibited. This is what bounds the claim to
  exactly `run` rather than more, and it is the one number a reader can
  check on a calculator;
- `verification` — the four legs the discovery protocol ran, each named;
- `least_claim` — the swept range from `K_START`, the wheel modulus, the
  sieve depth and the monotonicity floor `a(n) ≥ a(n-1)`, which together
  say why no smaller `k` qualifies;
- `engine` — the exact configuration key that produced it.

The published claim in [RESULTS.md](../RESULTS.md) is written only after
each file is re-verified from disk: the protocol re-run independently,
every value re-tested with sympy, and the stopper's factorization
re-multiplied.
