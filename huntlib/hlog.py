"""Timestamped, tagged event logging -- the shared log voice of every hunt.

Tag taxonomy (used by all projects; keep log lines plain ASCII):

    STAGE        a phase of the campaign begins or ends
    STATUS       the 30-second heartbeat: position, rate, survivors, the
                 CENSUS COUNTS per run length (census_str), finds, live
                 odds, next rung + ETA -- emitted by Heartbeat on its own
                 thread, on the wall clock, whatever the main loop is doing
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

The heartbeat convention (CONVENTIONS.md): [STATUS] is logged every 30 s
of WALL CLOCK, from a timer thread (Heartbeat below), never from inside
the segment loop -- a launcher that only checks the clock between
segments goes silent for as long as one segment, one classification, or
one verification takes, and silence is indistinguishable from a hang.
When nothing has moved since the last line the heartbeat says what the
launcher is busy with and for how long, so a stall is visible as a stall.
"""

import collections
import threading
import time

_lock = threading.Lock()          # two threads never interleave a line


def log(tag, msg):
    with _lock:
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


class Heartbeat:
    """The wall-clock [STATUS] heartbeat every launcher runs.

    A daemon thread wakes every `interval` seconds and logs
    `line_fn()` as [STATUS] -- independent of the segment loop, so the
    line lands on time whether the main thread is sieving, waiting on a
    classification pool, or factoring a run breaker.  The main loop only
    has to:

        hb = Heartbeat(30.0); hb.start(line_fn)
        hb.mark(pos)          # at every segment boundary: position in the
                              # sweep's own units (k, p, ...)
        hb.doing("verifying run-10 k=1.14e17")   # what it is busy with
        hb.stop()             # in `finally`

    and `line_fn` composes the project's line, using:

        hb.rate()             # end-to-end units per second over the last
                              # >= interval seconds of wall clock, stall
                              # time INCLUDED (the honest rate)
        hb.stalled()          # None, or (what, seconds) when no mark has
                              # landed since the previous line -- append it
                              # so a stall reads as a stall, not as silence

    Positions and counters are read from the main thread's state without
    locking: they are ints and dict lookups, and a heartbeat that is one
    segment stale is fine.  `line_fn` must never save the checkpoint (a
    mid-segment save would persist counts the redone segment re-counts);
    saving stays in the main loop at segment boundaries.  An exception in
    `line_fn` is logged as [WARN] and never kills the thread.
    """

    def __init__(self, interval=30.0):
        self.interval = float(interval)
        self._samples = collections.deque(maxlen=4096)   # (t, pos)
        self._doing, self._doing_t = "", time.time()
        self._last_line_t = time.time()
        self._marks_since_line = 0
        self._stop = threading.Event()
        self._thread = None
        self._line_fn = None

    # ---- called from the main loop
    def mark(self, pos):
        self._samples.append((time.time(), pos))
        self._marks_since_line += 1

    def doing(self, what):
        self._doing, self._doing_t = str(what), time.time()

    # ---- read by line_fn
    def pos(self):
        return self._samples[-1][1] if self._samples else None

    def rate(self, now=None):
        """Units per second over the last >= interval seconds of wall clock:
        movement since the reference sample divided by the time since it,
        NOW included -- so a stall lowers the number instead of zeroing it.
        The reference is the newest sample at least `interval` old that is
        not the latest one (else the oldest sample)."""
        if len(self._samples) < 2:
            return 0.0
        now = time.time() if now is None else now
        samples = list(self._samples)
        t1, p1 = samples[-1]
        ref = samples[0]
        for t, p in reversed(samples[:-1]):
            if t <= now - self.interval:
                ref = (t, p)
                break
        t0, p0 = ref
        return (p1 - p0) / max(now - t0, 1e-9)

    def stalled(self, now=None):
        """(what, seconds) when nothing has been marked since the previous
        line, else None."""
        if self._marks_since_line or not self._samples:
            return None
        now = time.time() if now is None else now
        return self._doing or "between segments", now - self._doing_t

    # ---- lifecycle
    def emit(self):
        """Log one [STATUS] line now (also used for the final line)."""
        try:
            msg = self._line_fn() if self._line_fn else None
        except Exception as e:                       # never kill the beat
            log("WARN", f"heartbeat line failed: {e!r}")
            msg = None
        if msg:
            log("STATUS", msg)
        self._last_line_t = time.time()
        self._marks_since_line = 0

    def _run(self):
        while not self._stop.wait(self.interval):
            self.emit()

    def start(self, line_fn):
        self._line_fn = line_fn
        self._last_line_t = time.time()
        self._thread = threading.Thread(target=self._run, name="heartbeat",
                                        daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
