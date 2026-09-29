# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`A089761_a<n>_<k>.json`, plus the rolling ledger
`a089761_discoveries.json`. Nothing else does: the campaign's census
(every shorter run, and every later value that reaches the frontier) is
counted in the checkpoint and shown in each 30-second `[STATUS]` line,
never written here (CONVENTIONS.md, "The census is counted, not
narrated").

**Present:** `A089761_a16_15737271507027492.json`,
`A089761_a17_125811821444034258.json` and
`A089761_a18_109927810420106024208.json` — a(16), a(17) and a(18)
(RESULTS.md) — and the ledger holding the same three records.

Because the conditions of A089761 nest, one `k` can settle several terms at
once. A find is evidenced **once**, under the first term it settles, with a
`settles` field listing all of them — a run of 18 would produce a single
`A089761_a16_<k>.json` recording `a(16)`, `a(17)` and `a(18)`.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `sequence`, `forms` (`k*i^2 + 1, i = 1..n`, A089761's own letters) and
  `oeis_terms` — the header every record opens with; `oeis_terms` is
  literally what to submit, `{"18": k}` reading "a(18) = k";
- `k` and `run` — the claim, and how far the run reaches;
- `values` — every `k·i²+1` for `i = 1..run`, written out in full, so the
  primality claims can be re-tested directly;
- `certificates` — one per value. In this project's range these are
  deterministic Miller-Rabin results rather than probable-prime
  assertions: the enforced ceiling, `k < (3.317×10²⁴ − 1)/n²`, keeps every
  `k·i²+1` under huntlib's `3.317×10²⁴` deterministic bound (gate G10);
- `stopper` — the value at `i = run+1`, which must be **composite**, with a
  factor exhibited. This is what bounds the claim to exactly `run` rather
  than more, and it is the one number a reader can check on a calculator;
- `verification` — the four legs the discovery protocol ran, each named;
- `least_claim` — the swept range, the wheel modulus, the sieve depth and
  the monotonicity floor `a(n) ≥ a(n-1)`, which together say why no smaller
  `k` qualifies;
- `engine` — the exact configuration key that produced it.

The published claim in [RESULTS.md](../RESULTS.md) is written only after
each file is re-verified from disk: the protocol re-run independently,
every value re-tested with sympy, and the stopper's factorization
re-multiplied.
