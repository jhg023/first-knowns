# evidence/

Verified FIRST OCCURRENCES land here — one JSON per discovery, named
`A130003_a<n>_<m>.json` or `A110096_a<n>_<k>.json` (the term, under each
entry's own letter), plus a rolling ledger per family
(`a130003_discoveries.json`, `a110096_discoveries.json`).
Nothing else does: the campaign's census (every shorter run, and every
later value that reaches the frontier) is counted in the checkpoint and
shown in each 30-second `[STATUS]` line, never written here
(CONVENTIONS.md, "The census is counted, not narrated").

**Present: six first occurrences**, from the campaigns of 2026-08-23 to
2026-09-01:

    A130003_a19_13268589982417023.json         a(19), base 4
    A130003_a20_6120156516528136867.json       a(20), base 4
    A130003_a21_285661075490357310517.json     a(21), base 4
    A110096_a17_305948728878647722725.json     a(17), base 2
    A110096_a18_760056834873121351995.json     a(18), base 2
    A110096_a19_564052872977379795315735.json  a(19), base 2

and the two ledgers. Nothing else: the campaigns have also classified more
than 140,000 values at run 8 or longer and 10 of those came within one
condition of an open term, and none of them is written here — they are
counts in the checkpoint and lines in the log, which is the whole rule.

Because the conditions of both sequences nest, one integer can settle
several terms at once. A find is evidenced **once**, under the first term
it settles, with a `settles` field listing all of them — a run of 24 at
base 4 would produce a single `A130003_a22_<m>.json` recording `a(22)`,
`a(23)` and `a(24)`. Both sequences say how often that happens among
their small terms: A130003's `a(10) = 4503` settled five terms at once,
and A110096 repeats at six of its sixteen indices. At the depths these
six were found it is far rarer — about 0.13 per find — and each
`settles` exactly one term
([RESULTS.md](../RESULTS.md#what-a-find-looked-like)).

Each file is meant to be checkable by anyone with a bignum library and no
trust in this repository. It carries:

- `sequence`, `forms`, the term and `oeis_terms` — the claim, in each
  entry's own letters: `m` in A130003's records, with `forms` =
  `4^k + m, k = 1..n` as its name writes it, and `k` in A110096's, with
  `forms` = `k + 2^i, i = 1..n` (its name gives no letters; these are the
  ones its own programs use). `oeis_terms` maps every index the find
  settles to that same integer — literally what to submit, and where;
- `base` and `run` — which family it belongs to, and how far the run
  reaches;
- `values` — every value of the forms up to the run (`4^k + m` for
  `k = 1..run` on A130003, `k + 2^i` for `i = 1..run` on A110096), written
  out in full, so the primality claims can be re-tested directly;
- `certificates` — one per value. In this project's range these are
  deterministic Miller-Rabin results rather than probable-prime
  assertions: the power of 4 or of 2 is additive and tiny against
  huntlib's `3.317×10²⁴` bound, so the enforced ceiling *is* that bound
  (gate G10);
- `stopper` — the value at the exponent one past the run (`stopper.k` on
  A130003, `stopper.i` on A110096), which must be **composite**, with a
  factor exhibited. This is what bounds the claim to exactly `run` rather
  than more, and it is the one number a reader can check on a calculator;
- `verification` — the four legs the discovery protocol ran, each named;
- `least_claim` — the swept range, the wheel modulus, the sieve depth and
  the monotonicity floor `a(n) ≥ a(n-1)`, which together say why no smaller
  integer qualifies;
- `engine` — the exact configuration key that produced it.

A110096's three records carried A130003's letters — the term as `"m"`,
the stopper's exponent as `"k"`, `forms` = `"2^k + m, k = 1..n"` — until
2026-09-29, when the names, and no value, were changed to the entry's own.

The published claim in [RESULTS.md](../RESULTS.md) is written only after
each file is re-verified from disk: the protocol re-run independently,
every value re-tested with sympy, and the stopper's factorization
re-multiplied.
