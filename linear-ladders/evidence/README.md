# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`<family>_a<n>_<k>.json` (`A088250_a15_<k>.json`, `A125838_a15_<k>.json`,
…), plus a rolling ledger per family (`a088250_discoveries.json`, …).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present:** nothing yet. This project was built on 2026-09-03 and no
campaign has been run; the first find of any family writes the first file
here, and [RESULTS.md](../RESULTS.md) is updated only after that file has
been re-verified from disk.

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
  `N − 1 = m·k` into primes each under the bound (the multiplier's own
  small factors folded in), and a witness per prime factor satisfying
  the two Pocklington conditions (huntlib.certificate). The `−1`
  families' ceilings keep every value under the bound, so every one of
  their certificates is the deterministic test. `certificates_verified`,
  `unproved` and `proof_routes` say whether every value was proved and by
  which route;
- `stopper` — the value at the next multiplier, which must be
  **composite**, with the multiplier and a factor exhibited. This is what
  bounds the claim to exactly `run` rather than more, and it is the one
  number a reader can check on a calculator;
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
