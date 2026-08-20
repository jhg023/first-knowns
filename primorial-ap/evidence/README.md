# evidence — primorial-ap

**First occurrences only.** One JSON per verified new term of
[A053647](https://oeis.org/A053647), plus `ap_discoveries.json`, the ledger
that indexes them.

Nothing else belongs here (CONVENTIONS.md, "The discovery protocol"). A
chain one value short of the term being hunted gets a single `[NEAR]` line
in the log and no file; every chain from depth 6 up is counted in the
checkpoint and appears only in the census of the 30-second `[STATUS]` line.
The census is counted, never narrated, and never written to disk as
individual records.

The directory is **empty** because no production sweep has been run.

Each file will carry, for one find:

- `p`, `n`, and the exact `difference` P(n) = A002110(n);
- all `n` `values` as exact integers;
- `legs` — the three independent confirmations and what each returned;
- `proofs` — a primality proof for every value (`deterministic-mr` below
  3.317×10²⁴, otherwise a BLS75 certificate that `huntlib.certificate.verify`
  re-checks from scratch);
- `chain_breaker` and its factor witness, so the chain length is checkable
  with one multiplication;
- `swept_from` / `swept_to` and the engine `config`, which is what the
  least-claim rests on.
