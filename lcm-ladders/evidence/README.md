# evidence — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

One JSON per verified **first occurrence**, plus a ledger per family. Census
values are counts in the checkpoint and in the `[STATUS]` line, never files
(CONVENTIONS.md, "The census is counted, not narrated").

Empty until a hunt has run.

## What a file will contain

* `N` — the published term, and `x`, `filter_n`, `L`: N = L(n)·x, the form
  the sweep found it in.
* `run`, `settles` — the largest r with L(r) | N and N/i + s prime for every
  i ≤ r, and the indices this one integer settles. One N can settle several
  consecutive terms; it is evidenced once, under the first.
* `values`, `multipliers` — every N/i + s of the run, and the L(run)/i it
  came from, so a reader can recompute each with one division.
* `verification` — the three independent legs (huntlib's Miller-Rabin chain,
  sympy's BPSW on the run *length*, and a from-scratch re-sieve by the CPU
  engine at a different depth) plus the stopper.
* `stopper` — what bounds the claim to exactly `run`: either a factor
  witness for the composite N/(run+1) + s, or the fact that run+1 does not
  divide N at all, which is the stronger stop and needs no witness.
* `certificates` — a re-verified primality certificate per value.
  Below the deterministic Miller-Rabin bound (3.317e24) that is the
  seven-base test, which IS the proof there. Above it every value is proved
  from ONE factorization of x: (N/i + s) − s = N/i, and N = L(n)·x with L(n)
  n-smooth, so BLS75 Theorem 1 on V − 1 (A074200) or Theorem 15, the N+1
  Lucas test, on V + 1 (A078502) covers the whole run. A prime factor of x
  past the bound carries a subproof of its own, and the certificate is a
  finite tree whose leaves are deterministic tests. `certificates_verified`
  says every proof in the file was re-checked from scratch before it was
  written; `unproved` lists any index that has none.
* `also_settles` — what the find gives the rider entry: A093554(n) = N − 1
  for A078502 and A093553(n) = N + 1 for A074200, at every index the find
  settles. Sloane's comment on each says so and `lcml_reference`'s G2d
  re-derives it from the bare definition.
* `least_claim` — the sweep behind "least": the filter, the x it started
  from (the previous term re-denominated: a(n) ≥ a(n−1) because the
  conditions nest in N), the wheel period, the sieve depth and the unit.
