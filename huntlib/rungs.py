"""The progress ladder -- how an indefinite campaign reports where it is.

CONVENTIONS.md: a campaign runs INDEFINITELY.  There is no default depth
cap and a launcher stops on its own only at the enforced ceiling, so
progress cannot be a percentage of anything.  It is read off RUNGS instead:
named depths taken from the odds model's predictions -- stated before the
run -- with the ceiling appended as the last rung.  Each is logged `[RUNG]`
as it is passed, and the next one, with an ETA, rides in every `[STATUS]`.

The rule that is easy to get wrong, and was got wrong:

  A RUNG RETIRES WITH ITS TERM.  A rung is a prediction of where a term
  should appear, so the moment that term is FOUND its unreached quartiles
  stop being progress markers.  dickson-ladders found a(12) and then spent
  hours advertising `next a(12) P90` while it hunted a(13), pointing at a
  depth that had stopped meaning anything.  The fix is structural rather
  than remembered: nothing here stores a ladder.  Every method takes the
  LIVE frontier and derives the live rungs from it, so a stale ladder is
  not a thing that can exist.

The ceiling rung belongs to no term (`term is None`) and therefore never
retires -- it is the one rung a campaign is guaranteed to be aiming at.
"""

import json

QUANTILES = ("Q1", "median", "Q3", "P90")


def eta_str(remaining, rate):
    """Human ETA for `remaining` units at `rate` units/s, ASCII only."""
    if not rate or rate <= 0 or remaining <= 0:
        return "?"
    s = remaining / rate
    if s < 90:
        return f"{s:.0f}s"
    if s < 5400:
        return f"{s / 60:.0f}m"
    if s < 172800:
        return f"{s / 3600:.1f}h"
    return f"{s / 86400:.1f}d"


class Ladder:
    """A set of (term, label, depth) rungs, read against a live frontier.

    `term` is the term index each rung is a prediction ABOUT; it is what
    makes retirement possible.  The ceiling rung carries `term = None`.
    """

    def __init__(self, rungs=(), ceiling=None, ceiling_label="engine ceiling"):
        # BY DEPTH, not by term: the ladder is walked in the order the sweep
        # meets it, and a term's Q1 can sit below the previous term's P90.
        self.rungs = sorted((((None if t is None else int(t)), str(lab),
                              float(d)) for t, lab, d in rungs),
                            key=lambda r: r[2])
        self.ceiling = None if ceiling is None else float(ceiling)
        self.ceiling_label = ceiling_label

    # ------------------------------------------------------------ building
    @classmethod
    def from_predictions(cls, preds, quantiles=QUANTILES, ceiling=None,
                         ceiling_label="engine ceiling"):
        """From {term: {"Q1": depth, "median": depth, ...}}.

        Missing quantiles are simply absent from the ladder: a model that
        cannot place a term's Q3 below the ceiling should not pretend to.
        """
        rungs = []
        for term, qs in (preds or {}).items():
            for q in quantiles:
                if q in qs and qs[q] is not None:
                    rungs.append((int(term), f"a({int(term)}) {q}",
                                  float(qs[q])))
        return cls(rungs, ceiling=ceiling, ceiling_label=ceiling_label)

    @classmethod
    def from_model_file(cls, path, **kw):
        """From a project's model_results.json ({"predictions": {...}}).

        A missing or unreadable file yields an EMPTY ladder rather than an
        error: the campaign still runs, it just has nothing to aim at, and
        that shows up as a one-rung ladder in the log.  Pass an absolute
        path built from `__file__`, never a relative one -- a campaign
        started from another directory once loaded no rungs at all and said
        so only by printing a suspiciously short ladder.
        """
        try:
            with open(path) as fh:
                preds = json.load(fh)["predictions"]
        except Exception:
            preds = {}
        return cls.from_predictions(preds, **kw)

    # ------------------------------------------------------------- reading
    def live(self, frontier, only_term=None):
        """The rungs still worth aiming at, ascending, ceiling last.

        `frontier` is the largest term already settled: its rungs, and every
        lower term's, are gone.  `only_term` narrows further, for a campaign
        whose sweep line RESTARTS per term (each term its own sieve), where
        a higher term's depths are not on the line currently being walked.
        """
        out = [(t, lab, d) for (t, lab, d) in self.rungs
               if t is not None and t > int(frontier)
               and (only_term is None or t == int(only_term))
               and (self.ceiling is None or d < self.ceiling)]
        if self.ceiling is not None:
            out.append((None, self.ceiling_label, self.ceiling))
        return out

    def newly_passed(self, pos, frontier, passed, only_term=None):
        """Labels of live rungs at or below `pos` that are not in `passed`.

        `passed` is the checkpoint's list of labels already logged, so a
        resumed campaign does not re-announce the ladder it has climbed.
        """
        done = set(passed or ())
        return [lab for (_t, lab, d) in self.live(frontier, only_term)
                if pos >= d and lab not in done]

    def next_rung(self, pos, frontier, only_term=None):
        """(label, depth) of the lowest live rung above `pos`, or None."""
        for (_t, lab, d) in self.live(frontier, only_term):
            if d > pos:
                return lab, d
        return None

    def retired_by(self, term, frontier_before, only_term=None):
        """Labels that stop being progress markers when `term` is settled."""
        return [lab for (t, lab, _d) in self.rungs
                if t is not None and frontier_before < t <= int(term)]

    def status_str(self, pos, frontier, rate=None, only_term=None):
        """`next: a(17) median at 8.2e+14 (ETA 2.1h)` for a [STATUS] line."""
        nxt = self.next_rung(pos, frontier, only_term)
        if nxt is None:
            return "next: -- (past the last rung)"
        lab, d = nxt
        if rate:
            return f"next: {lab} at {d:.3g} (ETA {eta_str(d - pos, rate)})"
        return f"next: {lab} at {d:.3g}"

    def progress_str(self, pos, frontier, passed, only_term=None):
        """`rung 5/17` -- which rung of the live ladder the campaign is on."""
        live = self.live(frontier, only_term)
        n_done = sum(1 for (_t, _lab, d) in live if pos >= d)
        return f"rung {n_done}/{len(live)}"

    def __len__(self):
        return len(self.rungs) + (1 if self.ceiling is not None else 0)


def gate_ladder():
    """(ok, msg): the ladder ascends, retires with its term, and never
    advertises a depth belonging to a term already found.

    This is the drill that would have caught the dickson-ladders incident,
    and it is here rather than in a project because the rule is repo-wide.
    """
    preds = {11: {"Q1": 1e16, "median": 7.2e16, "Q3": 1.9e17, "P90": 4.0e17},
             12: {"Q1": 4e18, "median": 1.8e19, "Q3": 5e19, "P90": 9.5e19},
             13: {"Q1": 5e20, "median": 2.1e21, "Q3": 6e21, "P90": 1.2e22}}
    lad = Ladder.from_predictions(preds, ceiling=4e22)
    live = lad.live(frontier=10)
    if len(live) != 13:
        return False, f"ladder: expected 12 rungs + ceiling, got {len(live)}"
    depths = [d for (_t, _l, d) in live]
    if depths != sorted(depths):
        return False, "ladder: rungs are not ascending"
    if live[-1][0] is not None:
        return False, "ladder: the ceiling rung is not last"

    # The retirement: with a(12) found, no a(11) or a(12) rung may be live,
    # and the next rung from a position INSIDE the retired range must be an
    # a(13) rung -- not the a(12) P90 the campaign has already passed by.
    pos = 5.6e19                                   # where a(12) turned up
    before = lad.next_rung(pos, frontier=11)
    if before is None or not before[0].startswith("a(12)"):
        return False, f"ladder: before the find the next rung was {before}"
    retired = lad.retired_by(12, frontier_before=11)
    if len(retired) != 4:
        return False, f"ladder: a(12) should retire 4 rungs, got {retired}"
    after = lad.next_rung(pos, frontier=12)
    if after is None or not after[0].startswith("a(13)"):
        return False, (f"ladder: after finding a(12) the campaign still aims "
                       f"at {after} -- a retired rung")
    if any(lab.startswith(("a(11)", "a(12)"))
           for (_t, lab, _d) in lad.live(frontier=12)):
        return False, "ladder: a settled term's rungs are still live"

    # newly_passed is idempotent against the checkpoint's record.
    first = lad.newly_passed(1e17, 10, [])
    if lad.newly_passed(1e17, 10, first):
        return False, "ladder: a passed rung is announced twice"

    # per-term ladders, for a campaign whose line restarts each term
    solo = lad.live(frontier=11, only_term=12)
    if len(solo) != 5 or any(t not in (12, None) for (t, _l, _d) in solo):
        return False, f"ladder: only_term leaked other terms ({solo})"
    return True, ("ladder ok: 12 rungs + ceiling ascend, a(12)'s find retires "
                  "its 4 rungs and moves the aim to a(13), a passed rung is "
                  "announced once, and only_term isolates one term's line")


GATES = [gate_ladder]
