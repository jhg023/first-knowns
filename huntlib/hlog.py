"""Timestamped, tagged event logging -- the shared log voice of every hunt.

Tag taxonomy (used by all projects; keep lines ASCII for Windows consoles):

    STAGE        a phase of the campaign begins or ends
    STATUS       periodic heartbeat (position, rate, live odds, ETA)
    MILESTONE    a power-of-ten boundary crossed
    CANARY-GOLD  an expected rediscovery confirmed (the stream is honest)
    NEAR         a near-miss worth dopamine (rare, individually logged)
    DISCOVERY    a verified find -- evidence JSON written
    WARN/ALARM   something needs the operator's eyes; ALARM halts
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
