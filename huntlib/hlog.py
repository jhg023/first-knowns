"""Timestamped, tagged event logging -- the shared log voice of every hunt.

Tag taxonomy (used by all projects; keep log lines plain ASCII):

    STAGE        a phase of the campaign begins or ends
    STATUS       the 30-second heartbeat: position, rate, survivors, the
                 CENSUS COUNTS per run length (census_str), finds, live
                 odds, next rung + ETA
    MILESTONE    a power-of-ten boundary or a model-odds quartile crossed
    RUNG         a rung of the progress ladder passed
    CANARY-GOLD  an expected rediscovery confirmed (the stream is honest)
    NEAR         a value ONE SHORT of an open term (rare, individually
                 logged); anything shorter is counted, never logged
    DISCOVERY    a verified first occurrence -- evidence JSON written
    WARN/ALARM   something needs the operator's eyes; ALARM halts

The census convention (CONVENTIONS.md): a value whose run length r has
a(r+1) already settled is noise as an individual -- it is COUNTED in the
checkpoint and shown by census_str in every STATUS/MILESTONE line, and
nothing else: no log line, no evidence file, no near-miss record.  The
evidence directory holds first occurrences only.
"""

import time


def log(tag, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{tag}] {msg}", flush=True)


def banner(tag, lines):
    """A multi-line boxed announcement (discoveries)."""
    log(tag, "=" * 60)
    for ln in lines:
        log(tag, ln)
    log(tag, "=" * 60)


def census_str(counts, lo, hi):
    """The census counts per run length, lo..hi inclusive, as one token
    per length -- `census 7:280 8:71 9:28 10:8` -- so a STATUS line reads
    the same in every project.  `counts` is the checkpoint's per-length
    table (keys are strings or ints); absent lengths print as 0."""
    parts = []
    for r in range(int(lo), int(hi) + 1):
        n = counts.get(str(r), counts.get(r, 0)) if counts else 0
        parts.append(f"{r}:{int(n)}")
    return "census " + (" ".join(parts) if parts else "-")
