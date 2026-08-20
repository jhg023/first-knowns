"""Settledness bookkeeping -- what is already known, and what a find settles.

CONVENTIONS.md, "The discovery protocol": a discovery is a FIRST
OCCURRENCE, logged once.  Deciding that needs one question answered
consistently everywhere -- *is a(r) settled, and if so where?* -- against
four sources that every project in this repo has:

  * the LITERATURE table frozen in the oracle;
  * terms an earlier campaign of this project already published;
  * terms settled by a sibling sweep, where a project has one;
  * terms THIS campaign has verified, which live in the checkpoint so that
    the frontier promotes itself at runtime and needs no hand edit.

That is what this module is: the lookup, the promotion, and the census
counters.  What is deliberately NOT here is `event_kind` -- the function
that turns a survivor into DISCOVERY / NEAR / CENSUS / nothing.  Its rule
is repo-wide but its MATHEMATICS is per project (a monotone ladder settles
every shorter run at once; a per-length hunt settles exactly one; a hunt
that re-sieves for each term settles the term it is sieving for), so
CONVENTIONS.md puts one `event_kind` in each project and each selftest
drills it.  This module gives that function the facts it reasons from.
"""


def settled_at(tables, found, r):
    """Where a(r) is settled, or None if it is open.

    `tables` are the static dicts in priority order (literature first);
    `found` is the checkpoint's runtime table, whose keys may be strings
    because it has been through JSON.
    """
    r = int(r)
    for tab in tables:
        if tab and r in tab:
            return int(tab[r])
    if found:
        v = found.get(str(r), found.get(r))
        if v is not None:
            return int(v)
    return None


def is_open(tables, found, r):
    return settled_at(tables, found, r) is None


def top_settled(tables, found, floor=0):
    """The largest settled index -- the campaign frontier.

    Everything above it is undiscovered; everything at or below it is
    census.  `floor` is where a project starts counting when nothing at all
    is settled.
    """
    best = int(floor)
    for tab in tables:
        for r in (tab or {}):
            best = max(best, int(r))
    for r in (found or {}):
        best = max(best, int(r))
    return best


def next_open(tables, found, start):
    """The smallest open index at or above `start` -- the term being hunted.

    This is what the live odds and the rung ladder must both be quoted
    against: a campaign that has just found a(12) is hunting a(13), even
    though a(12) is where it stands.
    """
    r = int(start)
    while settled_at(tables, found, r) is not None:
        r += 1
    return r


def settle_one(found, r, value):
    """Record a(r) = value in the checkpoint table.  True if it was open.

    For a hunt where each term is its own question -- a per-length hunt, or
    one that re-sieves for every term.
    """
    r = str(int(r))
    if found.get(r) is not None:
        return False
    found[r] = int(value)
    return True


def settle_monotone(tables, found, r, value):
    """Settle a(r') = value for every open r' <= r; return the r' list.

    For a MONOTONE ladder, where a candidate reaching run r has reached
    every shorter run too, so one k can be a(11) and a(12) at once -- each
    logged once, which is the whole point of the discovery-once rule.
    """
    fr = top_settled(tables, found)
    newly = [rr for rr in range(fr + 1, int(r) + 1)]
    for rr in newly:
        found[str(rr)] = int(value)
    return newly


# --------------------------------- census -----------------------------------

def bump_census(counts, r):
    """Count one census value of run length r (keys stay JSON-friendly)."""
    k = str(int(r))
    counts[k] = int(counts.get(k, 0)) + 1
    return counts[k]


def census_total(counts, lo=None):
    """How many census values at or above `lo` this campaign has met."""
    return sum(int(v) for k, v in (counts or {}).items()
               if lo is None or int(k) >= int(lo))


def gate_frontier():
    """(ok, msg): lookups, promotion and the two settle policies behave."""
    known = {9: 3332396388090}
    camp = {10: 9328409578841430}
    found = {}
    tabs = (known, camp)
    if settled_at(tabs, found, 9) != 3332396388090:
        return False, "frontier: literature lookup failed"
    if settled_at(tabs, found, 11) is not None:
        return False, "frontier: an open term reported settled"
    if top_settled(tabs, found) != 10:
        return False, f"frontier: top is {top_settled(tabs, found)}, want 10"
    if next_open(tabs, found, 9) != 11:
        return False, "frontier: next_open skipped a settled term"

    # monotone: one value settles every open index below it, once
    newly = settle_monotone(tabs, found, 13, 12094123415384869458600)
    if newly != [11, 12, 13]:
        return False, f"frontier: monotone settle gave {newly}"
    if settle_monotone(tabs, found, 13, 999) != []:
        return False, "frontier: monotone settle re-settled what it had"
    if top_settled(tabs, found) != 13 or next_open(tabs, found, 9) != 14:
        return False, "frontier: the runtime table did not promote the frontier"
    if settled_at(tabs, found, 12) != 12094123415384869458600:
        return False, "frontier: a runtime-settled term reads back wrong"

    # per-term: exactly one index, and only while it is open
    f2 = {}
    if not settle_one(f2, 16, 39) or settle_one(f2, 16, 41):
        return False, "frontier: settle_one is not once-only"
    if f2 != {"16": 39}:
        return False, f"frontier: settle_one wrote {f2}"

    counts = {}
    for r in (7, 7, 8):
        bump_census(counts, r)
    if counts != {"7": 2, "8": 1} or census_total(counts, lo=8) != 1:
        return False, f"frontier: census counters wrong ({counts})"
    return True, ("frontier ok: literature/campaign/runtime lookups, a "
                  "monotone find settling 11-13 at once and once only, "
                  "per-term settling, and the census counters")


GATES = [gate_frontier]
