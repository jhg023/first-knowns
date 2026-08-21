# Evidence — prime-power-sums

**First occurrences only.** One JSON per verified discovery, plus
`psum_discoveries.json`, the ledger. Census values are counts, and the
counts live in the checkpoint and in the `[STATUS]` heartbeat — never
here (CONVENTIONS.md, the census rule).

Empty at present: no production sweep has been run.

Each file will carry, for one find:

| field | meaning |
|-------|---------|
| `sequence_index`, `sequence_prime` | the two OEIS sequences the find extends |
| `also_extends` | further sequences settled by the same value (m = 1 extends four) |
| `m`, `e`, `term` | the family, and which term index this is |
| `k`, `prime_k` | the index, and the prime at that index — the two published values |
| `sum` | the exact S(m, k), as a decimal string |
| `quotient` | (e + S)/k — **the witness**: one multiplication checks the claim |
| `previous_term`, `published_frontier`, `frontier_held_by` | what it beats, and whose search it beats |
| `verification` | the three legs, each recorded as it passed |
| `swept_from_prime`, `found_in_window` | the coverage the "first occurrence" claim rests on |

The claim that a find is the **next** term rests on the sweep being
contiguous from p = 2 with no gaps, which is what the checkpoint's
`(p, k, sums)` cursor and the resume drill enforce, and on the canary
chain: every published term below the find was rediscovered by the same
stream, or the campaign would have halted.

Nothing here is ever submitted anywhere automatically. Discoveries are
records; what happens to them is the owner's call.
