# RESULTS — polynomial-runs

> **Authorship disclaimer:** all code and documentation here was authored by
> **Claude (Anthropic's AI)** at the repository owner's direction.

## Verified finds

None yet. The project was built on 2026-10-08 and no campaign has been
started; `evidence/` is created by the first find. When a find lands, this
section gets one row per term in discovery order: the exact integer, the
time, the leg, the certificate routes, the stopper's factor and the
evidence file — and, for A230663, whether p − 2 was prime and so settled
A164926(n+1) (README, "A230663 and A164926 are one problem, shifted").

## The census

Counted per index in the checkpoint and the `[STATUS]` line (runs that
would be a term of index 8 or more), never listed. Nothing counted yet.

## What is open now

| entry | frontier | open indices (the comment terms skipped) | model median, from the bottom of the line |
|---|---|---|---|
| A165234 | a(15) = 17,762,917,045,631 | 16, 17, 18, 19, 20, 21, … (29 is known) | a(16) 3.7×10¹⁵, a(20) 5.0×10²¹, a(21) 2.2×10²³ |
| A230663 | a(15) = 19 | 16, 17, 18, 19, 20, 21, … (39 is known) | a(16) 2.6×10¹⁵, a(20) 3.6×10²¹ (bounded ≤ 2.3×10²⁰ by A164926(21) + 2), a(21) 6.4×10²² |
| A092120 | a(15) = 409,333 | 16, 17, 18, 20, 21, … (19 is known) | a(16) 1.5×10¹⁷, a(18) 1.9×10²⁰, a(20) 2.7×10²³ |
| A347537 | a(16) = 1,500,599,554,819 | 17, 18, 19, 20, 21, … | a(17) 1.4×10¹⁷, a(20) 6.3×10²¹, a(21) 2.4×10²³ |

Every campaign opens at the bottom of its line (p = 2) and settles the
indices in whatever order their first occurrences lie. What a first
campaign owes before it is read as a measurement: the rule 5g acceptance
test (the first `[STATUS]` lines against BENCHMARKS.md's table), and a
priced rate at every filter it promotes itself through (BENCHMARKS.md,
"What is owed").

## The OEIS entries

Checked against the export of 2026-10-08. A165234 lists a(1)–a(15) with
a(29) = 29 in a comment and "no other terms less than 10^12"; A230663
a(1)–a(15) with a(39) = 43 and "all other terms > 128865958933"; A092120
a(0)–a(15) with a(19) = 163 and "all other terms after a(15) are greater
than 10^17"; A347537 a(1)–a(16). A164926, which bounds A230663, lists
a(1)–a(19) with a(16) = 17, a(21) = 234,505,015,943,235,329,417 and
a(40) = 41 in comments; its a(20) is open above 3.744×10²¹
(euler-prime-runs).
