# RESULTS — lcm-ladders

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

None yet. The engine, the gate battery, the odds model and the campaign are
built and green (44/44, 2026-09-06); no hunt has been run.

Every find will be recorded here in discovery order with the exact integer,
the three-way verification, the factor witness for the value that stops the
run, the BLS75 certificate route for each of its n values, and the evidence
file path — and with what it settles in the rider entry, which is the same
integer shifted by one at every index the find settles.

## What is open, and what a find is worth

| entry | frontier | open | settles for free |
|---|---|---|---|
| A078502 | a(13) = a(14) = 7,272,877,497,848,202,240 (Andersen, Jan 2003) | a(15) | A093554(n) = a(n) − 1 |
| A074200 | a(14) = 2,918,756,139,031,688,155,200 (Andersen, Feb 2004) | a(15) | A093553(n) = a(n) + 1 |

Neither entry carries a published bound at any open index and neither has a
b-file, so the floor for a(15) is monotonicity alone: a(15) ≥ a(14).

## The odds, stated before the run

From `model_results.json` (Bateman–Horn, validated at mean E = 1.12 over 12
independently-searched knowns; see README.md). Depths are in x at that
filter; the published term is N = L(n)·x.

| term | median x | median N | device time to the median | P(found) at 2.5× the median |
|---|---|---|---|---|
| a(15) A078502 | 1.18e17 | 4.24e22 | 2.2 s | 92% |
| a(15) A074200 | 1.46e17 | 5.25e22 | 2.8 s | 92% |
| a(16) either | 2.13e19 | 1.53e25 | 71 s | 92% |
| a(17) either | 9.28e19 | 1.14e27 | 40 min | 92% |
| a(18) either | 2.89e22 | 3.54e29 | 20 h | 92% |

The times are the frozen benchmark's rates for that filter
(BENCHMARKS.md) against the modelled median, device only; the campaign's
own rate is the pipeline's and is what `[STATUS]` prints.

Read every depth as a floor. The four ladder projects before this one landed
their scored finds at a pooled optimism factor of about 1.9–2.5× the median
while every census showed the modelled intensity right to a percent or two:
mean count right, first occurrence late.

## The census

Counted, not narrated (CONVENTIONS.md). Runs of length ≥ 8 are counted per
length in the checkpoint and printed in every 30-second `[STATUS]` line; a
run one short of the open term gets a single `[NEAR]` line with its campaign
ordinal and is verified as a health check but never evidenced; only a first
occurrence is a `[DISCOVERY]` and only a first occurrence gets a file.

## In progress

Nothing is running. The campaign is ready to be started by the owner:

```bash
python launch.py                    # A078502 from a(15)
python launch.py --family A074200   # A074200 from a(15)
```
