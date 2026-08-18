# evidence/

Verified finds land here, one JSON per k, named
`ladder_hit_run<n>_k<k>.json`, plus a rolling `ladder_discoveries.json`
and a `ladder_nearmiss.jsonl` census of runs at or above 7.

**Nothing is here yet: the campaign has been built and gated, not run.**

Each file is meant to be checkable by anyone with a bignum library and no
trust in this codebase. The shape:

```json
{
 "k": 3776600100,
 "run": 7,
 "values_prime_m": [1, 2, 3, 4, 5, 6, 7],
 "k_factorization": {"2": 2, "3": 2, "5": 2, "7": 1, "11": 1, "13": 1, ...},
 "breaker_m": 8,
 "breaker_factor": 11,
 "certificates_bls75": {"1": {"2": 3, "3": 2, ...}, "2": {...}, ...}
}
```

- `values_prime_m` — the m for which m*k^2+1 is claimed prime.
- `k_factorization` — the complete factorization of k, which is what
  makes N-1 = m*k^2 fully factored and the certificates possible.
- `breaker_m` / `breaker_factor` — the value that ends the run and a
  nontrivial factor of it. One multiplication checks the claim.
- `certificates_bls75` — for each m, a witness a_p for every prime
  p | N-1, proving N = m*k^2+1 prime by Brillhart-Lehmer-Selfridge
  Theorem 1: a_p^(N-1) == 1 (mod N) and gcd(a_p^((N-1)/p) - 1, N) == 1.
  Every p is far below huntlib's deterministic Miller-Rabin bound, so
  each is certified prime outright and the proof is complete.

To re-verify a file without this repository, in any bignum system:
factor nothing, trust nothing, and check the three conditions above.
