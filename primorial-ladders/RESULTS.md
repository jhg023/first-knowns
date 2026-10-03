# RESULTS — primorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

None yet. The project was built, gated and optimized on 2026-10-02; no
campaign has been started. What a find will look like, so a reader knows
what to expect here:

- one evidence file per discovery under `evidence/`, named
  `<entry>_a<n>_<integer>.json`, opening with the entry, its `forms` in
  the entry's own letters, the integer under that letter (p on A115785 and
  A115786, m on A145743) and `oeis_terms` — the literal `{index: integer}`
  of what to submit, several indices when one integer is several terms
  (the conditions nest on A115786 and A145743);
- every value of the run and its certificate (the deterministic
  Miller–Rabin test under 3.317×10²⁴, a re-verified BLS75 proof found by a
  bounded search above it), the three-way verification, the stopper that
  bounds the run (a composite with a factor witness, or on A115785 a value
  below 2), and on A145743 a factor witness that m is composite;
- the `least_claim`: the index's floor (prime(n)# + 2 on A115785, a(n−1)
  + 1 elsewhere), the exception zone covered on the host, the carried
  coverage of the previous filter where the line was carried, the wheel,
  the depth and the class.

Riders are expected on A115786 and A145743 (one integer settling several
indices) and impossible on A115785 below prime(n+1)#.

## Census

Counts per run length from each campaign's checkpoint (`--status`) and its
`[STATUS]` lines; nothing below the open term gets a line or a file.
Nothing to report yet.

## In progress

No campaign running. The open terms and what the model expects of them
are in [README.md](README.md); the rates at each opening are in
[BENCHMARKS.md](BENCHMARKS.md).
