# evidence — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

One JSON per verified **first occurrence**, plus a ledger per family. Census
values are counts in the checkpoint and in the `[STATUS]` line, never files
(CONVENTIONS.md, "The census is counted, not narrated").

Eight files: six from the campaigns of 2026-09-06 — A078502's a(15), a(16),
a(17) and a(18) = a(19) (one file, `settles = [18, 19]`) and A074200's a(15)
and a(16) — and A074200's a(17) and a(18) from that campaign resumed on
2026-09-19 ([RESULTS.md](../RESULTS.md)).

## b-files

`b078502.txt` is the OEIS b-file for A078502, n = 1..19, ready to upload as
it stands: one `n a(n)` pair per line, no header. a(1)..a(14) are the
published terms; a(15)..a(19) are taken from the `oeis_terms` of the A078502
files here. It exists because an OEIS reviewer asked that the entry's data
stop at a(18) and the remaining term go in a b-file. It is derived from
the JSONs rather than being evidence in its own right, and the gates read
only `*.json`.

## What a file contains

* `sequence`, `forms`, the term, `oeis_terms` — the four fields every
  evidence file in this repository opens with (CONVENTIONS.md "Naming in an
  evidence file"). **The term is the field `N` in an A078502 file and the
  field `m` in an A074200 file**, because that is what each OEIS entry calls
  it; `oeis_terms` maps every index the find settles to the integer to
  submit, so `{"18": v, "19": v}` reads "a(18) and a(19) are both v".
* `x`, `filter_n`, `L` — the form the sweep found it in: the term is
  `L` = lcm(1..n) times `x`, the quotient of the term by lcm(1..n), with
  n = `filter_n`. `x` is the engine's variable and is never what gets
  submitted.
* `run`, `settles` — the largest n with (N − k)/k prime for every k = 1..n
  (A078502), or (m + k)/k prime for every k = 1..n (A074200), and the
  indices this one integer settles. One term can settle several consecutive
  indices; it is evidenced once, under the first.
* `values`, `multipliers` — every value of the run, keyed by k — N/k − 1 for
  A078502, m/k + 1 for A074200 — and the lcm(1..run)/k it came from, so a
  reader can recompute each with one division.
* `verification` — the three independent legs (huntlib's Miller-Rabin chain,
  sympy's BPSW on the run *length*, and a from-scratch re-sieve by the CPU
  engine at a different depth) plus the stopper.
* `stopper` — what bounds the claim to exactly `run`: either a factor
  witness for the composite value at k = run + 1 (N/k − 1 or m/k + 1), or
  the fact that run + 1 does not divide the term at all, which is the
  stronger stop and needs no witness. `stopper.i` is that k.
* `certificates` — a re-verified primality certificate per value.
  Below the deterministic Miller-Rabin bound (3.317e24) that is the
  deterministic Miller-Rabin test, which IS the proof there. Above it every value is proved
  from ONE factorization of the quotient `x`: the value plus one (A078502,
  N/k) or the value less one (A074200, m/k) is the term over k, and the
  term is lcm(1..n), which is n-smooth, times `x`, so BLS75
  Theorem 1 on the value less one (A074200) or Theorem 15, the Lucas test,
  on the value plus one (A078502) covers the whole run. A prime factor of
  `x` past the bound carries a subproof of its own, and the certificate is a
  finite tree whose leaves are deterministic tests. `certificates_verified`
  says every proof in the file was re-checked from scratch before it was
  written; `unproved` lists any index that has none.
* `also_settles` — what the find gives the rider entry: A093554(n) = N − 1
  for A078502 and A093553(n) = m + 1 for A074200, at every index the find
  settles. Sloane's comment on each says so and `lcml_reference`'s G2d
  re-derives it from the bare definition.
* `least_claim` — the sweep behind "least": the filter, the quotient it
  started from (`swept_from_x`: the previous term re-denominated, since
  a(n) ≥ a(n−1) because the conditions nest in the term), the wheel
  period, the sieve depth and the unit.
