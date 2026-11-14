# evidence — hl-records (A331940)

First occurrences only: one JSON per verified new record of the
Hardy-Littlewood constant C of x^2 + x + k, plus the ledger
`hlc_discoveries.json`. **23 records, a(12) through a(34)**, found
2026-11-11 to 2026-11-14 and re-verified from disk on 2026-11-14
([RESULTS.md](../RESULTS.md)).

Each record opens with the four fields of `huntlib.evidence.header`
(`sequence`, `forms` = "x^2 + x + k", the integer under `k`, and
`oeis_terms` {index: integer}), then carries the record value of C twice
-- `C` to 34 digits with `C_error_bound`, and `C_table` rounded to the 5
decimals the entry's own table prints -- followed by the margin over the
previous record (C less the upper end of the previous record's interval),
the three confirmations and the least-k basis (README.md, "The discovery
protocol"). `python launch.py --status` lists every term found with both
forms of its C. The ledger holds the same records in discovery order, each
with its `label` and the time `t` it was written.

## b-file

`b331940.txt` is the OEIS b-file for A331940, n = 1..34, ready to upload
as it stands: one `n a(n)` pair per line, ASCII, no header. a(1)..a(11)
are the entry's published terms; a(12)..a(34) are taken from the
`oeis_terms` of the files here. It is derived from the JSONs rather than
being evidence in its own right, and the gates read only `*.json`.
