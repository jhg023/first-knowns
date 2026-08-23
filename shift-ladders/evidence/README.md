# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`A130003_a<n>_<m>.json` or `A110096_a<n>_<m>.json`, plus a rolling ledger
per family (`a130003_discoveries.json`, `a110096_discoveries.json`).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present: nothing yet.** No production sweep has been run. The engine and
the full gate battery are green and the campaign is the owner's to start.

Because the conditions of both sequences nest, one `m` can settle several
terms at once. A find is evidenced **once**, under the first term it
settles, with a `settles` field listing all of them — a run of 21 at
base 4 would produce a single `A130003_a19_<m>.json` recording `a(19)`,
`a(20)` and `a(21)`. Both sequences say how often that happens: A130003's
`a(10) = 4503` settled five terms at once, and A110096 repeats at six of
its sixteen indices.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `m`, `base` and `run` — the claim, which family it belongs to, and how
  far the run reaches;
- `values` — every `m + b^k` for `k = 1..run`, written out in full, so the
  primality claims can be re-tested directly;
- `certificates` — one per value. In this project's range these are
  deterministic Miller-Rabin results rather than probable-prime
  assertions: the offset `b^k` is additive and tiny against huntlib's
  `3.317×10²⁴` bound, so the enforced ceiling *is* that bound (gate G10);
- `stopper` — the value at `k = run+1`, which must be **composite**, with a
  factor exhibited. This is what bounds the claim to exactly `run` rather
  than more, and it is the one number a reader can check on a calculator;
- `verification` — the four legs the discovery protocol ran, each named;
- `least_claim` — the swept range, the wheel modulus, the sieve depth and
  the monotonicity floor `a(n) ≥ a(n-1)`, which together say why no smaller
  `m` qualifies;
- `engine` — the exact configuration key that produced it.

The published claim in [RESULTS.md](../RESULTS.md) is written only after
each file is re-verified from disk: the protocol re-run independently,
every value re-tested with sympy, and the stopper's factorization
re-multiplied.
