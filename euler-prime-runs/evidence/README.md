# evidence/

Verified FIRST OCCURRENCES land here -- one JSON per discovery, named
`euler_hit_run<n>_p<p>.json`, plus the rolling ledger
`euler_discoveries.json`. Nothing else does: the campaign's census (every
later run-17 or run-18 prime, the run-13..16 ladder) is counted in the
checkpoint and shown in each 30-second `[STATUS]` line, never written
here (CONVENTIONS.md, "The census is counted, not narrated"). The one
non-discovery kept is the Waldvogel-Leikauf run-21 value: it settled
a(21) when the sweep passed it, so it is a settled term with a record.

Present: a(17), a(18), a(19) and the a(21) settlement. Per-value census
files and the near-miss `.jsonl` written by earlier legs were retired on
2026-08-18; the git history before commit `3d01f95` has them, and
RESULTS.md carries their counts.

Each file is meant to be checkable by anyone with a bignum library and no
trust in this codebase. The shape:

```json
{
 "sequence": "A164926",
 "forms": "x^2 + x + p, x = 0..n-1 (composite at x = n)",
 "p": 3744101869688673856367,
 "oeis_terms": {"19": 3744101869688673856367},
 "settles": [19],
 "run": 19,
 "values_prime_x": [0, 1, 2, ..., 18],
 "breaker_x": 19,
 "breaker": 3744101869688673856747,
 "breaker_factor": 83
}
```

- `sequence`, `forms`, `p`, `oeis_terms` -- the four fields every evidence
  file in this repository opens with (CONVENTIONS.md "Naming in an
  evidence file"), in A164926's own letters: the term is the prime p, the
  polynomial's variable is x, and the index n is the length of the run.
  `p` is the integer to submit and `oeis_terms` says where it goes:
  `{"19": p}` reads "a(19) = p".
- `settles`, `run` -- the index this p settles and its run: x^2 + x + p is
  prime for exactly `run` consecutive x from 0, so `run` is that n.
- `values_prime_x` -- the x for which x^2 + x + p is claimed prime (a
  run of exactly `run` consecutive primes from x = 0).
- `breaker_x` / `breaker` / `breaker_factor` -- the value that ends the
  run and a nontrivial factor of it. One multiplication checks the claim
  that the run is EXACTLY `run` long.

To re-verify a file without this repository: test the `run` values for
primality with any trusted primality test, and check that
`breaker_factor` divides `breaker`.
