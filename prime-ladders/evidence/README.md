# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`A084700_a<n>_<k>.json` or `A084701_a<n>_<k>.json`, plus a rolling ledger
per family (`a084700_discoveries.json`, `a084701_discoveries.json`).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present:** four A084700 first occurrences from the campaign of
2026-09-02 — `A084700_a14_24581646307811670.json`,
`A084700_a15_1183192161007235610.json`,
`A084700_a16_161515890673488267840.json`,
`A084700_a17_2446970377116913184460.json` — and the ledger
`a084700_discoveries.json` that lists them. Nothing yet for A084701, whose
campaign has not been started; its first file will be
`A084701_a12_<k>.json`.

Because the conditions of both sequences nest, one `k` can settle several
terms at once. A find is evidenced **once**, under the first term it
settles, with a `settles` field listing all of them — a run of 16 on
A084700 while a(14) is open would produce a single `A084700_a14_<k>.json`
recording `a(14)`, `a(15)` and `a(16)`. Both sequences show how often that
happens at small `k`: A084700's `a(4) = 6` settled four terms at once and
A084701's `a(5) = 120` settled three.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `k`, `sign` and `run` — the claim, which family it belongs to, and how
  far the run reaches;
- `values` — every `prime(i)·k + s` for `i = 1..run`, written out in full,
  so the primality claims can be re-tested directly;
- `certificates` — one per value, each **re-verified from scratch before
  it is written**. Under huntlib's deterministic Miller-Rabin bound
  (`3.317×10²⁴`) a certificate is that seven-base test itself
  (`deterministic-mr`), which is what all four present files carry. Past
  the bound — from `a(18)` on, where `61·k + 1` exceeds it — an A084700
  value carries a BLS75 Theorem 1 certificate (`bls75-thm1`): the
  complete factorization of `N − 1 = prime(i)·k` into primes each under
  the bound, and a witness `a_p` per prime factor satisfying the two
  Pocklington conditions (huntlib.certificate). `certificates_verified`,
  `unproved` and `proof_routes` in the file say whether every value was
  proved and by which route;
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
