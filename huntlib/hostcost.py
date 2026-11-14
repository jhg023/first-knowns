"""Per-item host cost in a campaign loop: the TAIL, not the average.

A campaign's host side handles its survivors one at a time -- classify,
refine an interval, verify, certify -- and almost every item is cheap.  The
failure this module exists to make visible is the RARE item that is not: a
fallback path that costs minutes, taken once in a few dozen windows, sitting
inside the segment loop.  Nothing else in the repo can see it:

  * a benchmark never classifies (it times the engine on a frozen shape);
  * a gate checks correctness, not time;
  * a wall/device measurement of the loop over a few dozen windows is an
    AVERAGE, and the windows measured can simply hold none of the rare
    items -- hl-records measured 1.057 over 30 windows the same day its
    campaign ran at ~1% of its engine (2026-11-11);
  * the heartbeat said "sweeping from k = ..." for the whole stall, because
    the label it reports was set once per segment.

There, one survivor in ~35 windows had its constant C within 2.4e-6 of a
census bin edge; the classifier's last cheap tier could not separate it,
and the fallback (two 30-digit analytic evaluations, ~4 minutes each at
k = 1.3e10, ~40 at 1e12) ran inside the loop -- every ~4 s of device work
followed by ~7.5 minutes of host work.  CONVENTIONS.md, "A rare host path
is priced by its rate, and announced when it runs", states the rules; this
module is the part of them that is code:

    hc = HostCost(say=log, hb=hb, warn_s=5.0)
    for k, t in survivors:
        with hc.item(f"classifying k = {k}"):  # the heartbeat names it
            handle(k, t)
    # inside handle, on a path that can be slow:
    hc.path("analytic resolve")              # counted, shown in [STATUS]
    hc.expect("discovery verification")      # slow by design: no [WARN]
    # in the [STATUS] line:
    bits.append(hc.status())                 # "" when nothing was slow

A step that takes longer than `warn_s` gets ONE [WARN] naming its label,
its duration and the slow paths it took; the heartbeat's stall report reads
"classifying k = ... for 240s" instead of the segment's label; and the
slowest step of the run stays in [STATUS].  The per-item overhead is two
clock reads and a label swap (a few microseconds): wrap the unit whose cost
can explode, which is per survivor in a hunt that classifies tens a second
and per task in one that classifies thousands.

`price` and `price_line` are for the measurement the conventions require
BEFORE a campaign: count how often each fallback WOULD be taken (run the
cheap classifier over the survivors of many windows with the fallback
stubbed out) and multiply by its cost.  hl-records' density argument put
the rate at one window in 700; the count said one in 35.
"""

import time

from .hlog import log


class HostCost:
    """Times per-item host steps; announces the slow ones; keeps the tail."""

    def __init__(self, say=log, hb=None, warn_s=5.0):
        self.say = say
        self.hb = hb
        self.warn_s = float(warn_s)
        self.n = 0                      # items timed
        self.total_s = 0.0
        self.slow = 0                   # items at or over warn_s
        self.warned = 0                 # ... of which unexpected (a [WARN])
        self.max_s, self.max_label = 0.0, ""
        self.paths = {}                 # named slow paths taken
        self._cur = None                # [label, paths taken, expected]

    def item(self, label):
        hc = self

        class _Item:
            def __enter__(self):
                if hc._cur is not None:
                    raise RuntimeError("HostCost items do not nest")
                hc._cur = [str(label), [], None]
                self.scope = hc.hb.scope(label) if hc.hb is not None else None
                if self.scope is not None:
                    self.scope.__enter__()
                self.t0 = time.perf_counter()
                return hc

            def __exit__(self, *exc):
                dt = time.perf_counter() - self.t0
                if self.scope is not None:
                    self.scope.__exit__(*exc)
                lab, paths, expected = hc._cur
                hc._cur = None
                hc._record(dt, lab, paths, expected)
                return False
        return _Item()

    def path(self, name):
        """Count a named path (a fallback, a deep refinement) as taken --
        by the current item when there is one."""
        self.paths[name] = self.paths.get(name, 0) + 1
        if self._cur is not None:
            self._cur[1].append(name)

    def expect(self, reason):
        """The current item is slow by design (a discovery's verification):
        it is timed and counted, but announces nothing."""
        if self._cur is not None:
            self._cur[2] = str(reason)

    def _record(self, dt, label, paths, expected):
        self.n += 1
        self.total_s += dt
        if dt > self.max_s:
            self.max_s, self.max_label = dt, label
        if dt < self.warn_s:
            return
        self.slow += 1
        if expected:
            return
        self.warned += 1
        how = f" via {', '.join(paths)}" if paths else ""
        self.say("WARN", f"host step took {dt:.1f}s: {label}{how} -- slow "
                         f"host step #{self.warned} of this run; a path this "
                         f"slow must be priced by its rate (CONVENTIONS.md, "
                         f"'A rare host path is priced by its rate')")

    def status(self):
        """'' while nothing has been slow, else a short [STATUS] fragment."""
        bits = []
        if self.slow:
            dur = (f"{self.max_s:.1f}s" if self.max_s < 10
                   else f"{self.max_s:.0f}s")
            bits.append(f"slow host steps {self.slow} (max {dur}: "
                        f"{self.max_label})")
        if self.paths:
            bits.append("paths " + " ".join(f"{k}:{v}" for k, v in
                                            sorted(self.paths.items())))
        return "; ".join(bits)


def price(rate_per_window, cost_s, window_s):
    """The fraction of device time a path costs: taken `rate_per_window`
    times a window at `cost_s` each, against `window_s` of device time."""
    return float(rate_per_window) * float(cost_s) / max(float(window_s), 1e-12)


def price_line(name, taken, windows, cost_s, window_s):
    """One line for an OPTIMIZATION_LOG: a path counted `taken` times over
    `windows` windows, at `cost_s` each, priced against `window_s`."""
    rate = taken / max(windows, 1)
    frac = price(rate, cost_s, window_s)
    every = f"once in {windows / taken:,.0f} windows" if taken else \
        f"never in {windows:,} windows"
    return (f"{name}: {every} ({taken} of {windows:,}), {cost_s:.3g} s each "
            f"-> {100 * frac:.3g}% of {window_s:.3g} s windows")


def drill():
    """The machinery itself: a slow item is announced once with its label
    and paths, an expected one is not, the heartbeat names the item while
    it runs and gets its own label back, and the tail reaches [STATUS]."""
    from .hlog import Heartbeat
    lines = []
    hb = Heartbeat(3600.0)
    hb.doing("sweeping")
    hc = HostCost(say=lambda tag, msg: lines.append((tag, msg)), hb=hb,
                  warn_s=0.02)
    named = []
    with hc.item("fast item"):
        pass
    with hc.item("classifying k = 7"):
        named.append(hb._doing)
        hc.path("analytic resolve")
        time.sleep(0.06)
    with hc.item("verifying k = 9"):
        hc.expect("discovery verification")
        time.sleep(0.03)
    nested = False
    try:
        with hc.item("outer"):
            with hc.item("inner"):
                pass
    except RuntimeError:
        nested = True
    hc._cur = None
    warns = [m for t, m in lines if t == "WARN"]
    st = hc.status()
    ok = (len(warns) == 1 and "classifying k = 7" in warns[0]
          and "analytic resolve" in warns[0]
          and named == ["classifying k = 7"] and hb._doing == "sweeping"
          and hc.slow == 2 and hc.warned == 1
          and hc.paths == {"analytic resolve": 1}
          and "classifying k = 7" in st and nested
          and abs(price(1 / 35, 450, 0.14) - 450 / 35 / 0.14) < 1e-9)
    return ok, ("host-cost drill: a slow item is announced once with its "
                "label and the path it took, an expected one (a discovery's "
                "verification) is not, the heartbeat names the item while it "
                "runs and then gets the segment's label back, the slowest "
                "step reaches [STATUS], and items refuse to nest")
