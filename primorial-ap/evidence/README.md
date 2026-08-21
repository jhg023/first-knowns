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

The directory holds the three terms of the 2026-08-20/21 campaign:
`ap_a16_p116781362669989.json`, `ap_a17_p2097209048106247.json` and
`ap_a18_p14042451608819603.json`. That campaign classified 1,984,305,704
survivors, and its last sweep alone met chains at every depth from 6 to 17;
none of the rest is here, by rule.

Each file carries, for one find:

- `p`, `n`, and the exact `difference` P(n) = A002110(n);
- all `n` `values` as exact integers;
- `legs` — the three independent confirmations and what each returned;
- `proofs` — a primality proof for every value (`deterministic-mr` below
  3.317×10²⁴, otherwise a BLS75 certificate that `huntlib.certificate.verify`
  re-checks from scratch);
- `depth`, the chain's TRUE length, which can exceed `n` — a(17)'s runs 19
  deep — because a(n) asks for *at least* n values, and `values` lists the
  n the term requires;
- `chain_breaker` and its factor witness, so the chain length is checkable
  with one multiplication; the breaker sits at `depth`, not at `n`;
- `swept_from` / `swept_to` and the engine `config`, which is what the
  least-claim rests on.
