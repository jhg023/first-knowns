# RESULTS — factorial-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

None yet. The engine, the gate battery, the odds model and the campaign are
built and green (2026-09-16); no hunt has been run.

Every find will be recorded here in discovery order with the exact integer,
the three-way verification, the factor witness for the value that stops the
run, the BLS75 certificate route for each of its n values, and the evidence
file path — and, for A177014, what it settles in A226935, which is the same
integer plus one at every index the find settles.

## What is open, and what a find is worth

| entry | frontier | open | settles for free |
|---|---|---|---|
| A177013 | a(10) = 3,240,034,842 (Haga & Firoozbakht, May 2010) | a(11) | — |
| A177014 | a(9) = a(10) = 228,698,250 (Haga & Firoozbakht, May 2010; a(10) corrected by Schoenfield, 2018) | a(11) | A226935(n) = a(n) + 1 |

Neither entry carries a published bound at any open index and neither has a
b-file, so the floor for a(11) is monotonicity alone: a(11) ≥ a(10).

**A caveat on what the early terms are worth.** The modelled medians for
a(11)–a(15) are 3e10 to 6e16: minutes of a CPU, not a frontier that stood
because it was hard. They stood because nobody returned to these entries
after 2010. The hunt proper is a(16) onward, and the census discipline
below applies to all of it.

## The odds, stated before the run

From `model_results.json` (Bateman–Horn, validated at mean E = 1.20 over 8
independently-searched knowns; see README.md). Depths are x, the published
term itself.

| term | median x | P90 | P(found) at 2.5× the median |
|---|---|---|---|
| a(11) A177013 | 3.4e10 | 1.7e11 | 92% |
| a(11) A177014 | 2.4e10 | 1.5e11 | 92% |
| a(12) | 1.3e12 | 7.8e12 | 92% |
| a(13) | 4.9e13 | 3.0e14 | 92% |
| a(14) | 1.9e15 | 1.1e16 | 92% |
| a(15) | 6.2e16 | 3.5e17 | 92% |
| a(16) | 3.1e18 | 1.7e19 | 92% |
| a(17) | 1.4e20 | 7.8e20 | 92% |
| a(18) | 6.0e21 | 3.2e22 | 92% |
| a(19) | 2.8e23 | 1.5e24 | 92% |

The device time each depth costs is in BENCHMARKS.md, at the frozen rates
for that filter. Read every depth as a floor: the four ladder projects
before this one landed their scored finds at a pooled optimism factor of
about 1.9–2.5× the median while every census showed the modelled intensity
right to a percent or two — mean count right, first occurrence late.

## The census

Counted, not narrated (CONVENTIONS.md). Runs of length ≥ 8 are counted per
length in the checkpoint and printed in every 30-second `[STATUS]` line; a
run one short of the open term gets a single `[NEAR]` line with its campaign
ordinal and is verified as a health check but never evidenced; only a first
occurrence is a `[DISCOVERY]` and only a first occurrence gets a file. At
the opening filter a single segment holds a(11) and probably a(12), and
several run-11 values behind them: they are narrated in x order at the
segment close, the frontier moving as each lands.

## In progress

Nothing is running. The campaign is ready to be started by the owner:

```bash
python launch.py                    # A177013 from a(11)
python launch.py --family A177014   # A177014 from a(11)
```
