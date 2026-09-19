"""The evidence directory -- first occurrences, and nothing else.

CONVENTIONS.md: **the evidence directory holds first occurrences only.**
Census values are counts in the checkpoint and tokens in the `[STATUS]`
line; they get no file.  A `[NEAR]` value -- one short of an open term --
gets one log line and no file either.  So there is exactly one way in, and
this is it.

Two properties every project needs and would otherwise re-implement:

  * **Idempotence.** The segment in flight when a run is interrupted or
    crashes is REDONE on resume, so the same discovery is recorded twice.
    Records are therefore keyed by the value itself and upserted -- a redone
    segment rewrites its record instead of appending a duplicate, and the
    ledger stays a set rather than a log.
  * **Durability.** An evidence file is the artefact the whole campaign
    exists to produce; it is written through the same fsync-and-replace
    path as a checkpoint, because a machine that stops during the write of
    a discovery has lost the discovery.
"""

import json
import os
import time

from . import checkpoint as _ckpt


def record(ev, dirname, filename, ledger, key="k", label=None, now=None):
    """Write one first-occurrence evidence file and upsert the ledger.

    `ev` is the project's evidence dict (exact integers, verification legs,
    factor witness, certificates); `key` names the field that identifies the
    find.  Returns the path written.
    """
    os.makedirs(dirname, exist_ok=True)
    path = os.path.join(dirname, filename)
    _ckpt.save_json(path, ev)

    allrec = []
    if os.path.exists(ledger):
        try:
            with open(ledger) as f:
                allrec = json.load(f)
        except Exception:
            allrec = []                 # a torn ledger is rebuilt, not trusted
    rec = dict(ev)
    if label is not None:
        rec["label"] = label
    rec["t"] = time.time() if now is None else now
    kv = int(ev[key])
    allrec = [d for d in allrec if int(d.get(key, -1)) != kv]
    allrec.append(rec)
    allrec.sort(key=lambda d: int(d.get(key, 0)))
    _ckpt.save_json(ledger, allrec)
    return path


def header(sequence, forms, letter, value, settles):
    """The first four fields of every evidence record, in the OEIS entry's
    own language (CONVENTIONS.md "Naming in an evidence file"):

        {"sequence": "A177013", "forms": "k!*m - 1, k = 1..n",
         "m": <the integer>, "oeis_terms": {"18": <the integer>}}

    `letter` is the letter the OEIS NAME uses for the term (m here, k in
    A088250, p in A164926, N in A078502) and must stand alone in `forms`;
    `oeis_terms` is the literal answer to "what do I type into the OEIS",
    one entry per index the find settles.  Never raises -- a discovery is
    not the moment to find a typo; `check_names` is what a gate runs.
    """
    return {"sequence": str(sequence), "forms": str(forms),
            str(letter): int(value),
            "oeis_terms": {str(int(n)): int(value) for n in settles}}


def check_names(ev, key):
    """(ok, msg): the record speaks the OEIS entry's language.

    An evidence file is read by the person who types the term into the
    OEIS, not by the engine, so:

      * `sequence` is the A-number;
      * `forms` states the condition in the OEIS entry's OWN letters;
      * `key` -- the field that carries the published integer -- is one of
        those letters, standing alone in `forms` (an engine's sweep variable
        under its own name is how factorial-ladders shipped `x` beside a
        `forms` that said `k!*m - 1`, and how five linear-ladders families
        shipped `k` for what their entries call m -- with k the INDEX);
      * `oeis_terms` maps every index the find settles to the exact integer
        to submit, {"13": v, "14": v, "15": v} for a rider;
      * every one of those integers IS `ev[key]`: a project whose engine
        sweeps something else (lcm-ladders' x, with N = L*x published)
        carries that as a second field under ITS letter in `forms`.
    """
    import re
    seq = str(ev.get("sequence", ""))
    if not re.fullmatch(r"A\d{6}", seq):
        return False, f"evidence names: `sequence` is {seq!r}, not an A-number"
    forms = ev.get("forms")
    if not isinstance(forms, str) or not forms:
        return False, "evidence names: no `forms` string"
    if key not in ev:
        return False, f"evidence names: no `{key}` field"
    if not re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(key), forms):
        return False, (f"evidence names: the published integer is carried as "
                       f"`{key}`, which does not appear in forms = {forms!r}")
    terms = ev.get("oeis_terms")
    if not isinstance(terms, dict) or not terms:
        return False, "evidence names: no `oeis_terms` {index: integer} map"
    if "settles" in ev and (sorted(map(int, terms))
                            != sorted(map(int, ev["settles"]))):
        return False, (f"evidence names: oeis_terms covers {sorted(terms)} but "
                       f"the find settles {ev['settles']}")
    if any(int(v) != int(ev[key]) for v in terms.values()):
        return False, (f"evidence names: an oeis_terms integer is not "
                       f"`{key}` = {ev[key]}")
    return True, "evidence names ok"


def gate_names(dirname, letter):
    """(ok, msg): every record under `dirname` -- each evidence file and
    each ledger row -- passes `check_names`.

    `letter` is the OEIS letter, or a callable record -> letter for a
    project whose families' entries disagree (linear-ladders: k in A088250,
    m in A173750).  An empty directory passes: there is nothing to misname.
    """
    import glob
    n = 0
    for path in sorted(glob.glob(os.path.join(dirname, "*.json"))):
        with open(path) as f:
            d = json.load(f)
        for rec in (d if isinstance(d, list) else [d]):
            key = letter(rec) if callable(letter) else letter
            ok, msg = check_names(rec, key)
            if not ok:
                return False, f"{os.path.basename(path)}: {msg}"
            n += 1
    return True, (f"evidence names ok: {n} record(s) carry the published "
                  f"integer under the OEIS entry's own letter, in a `forms` "
                  f"that uses it, with the oeis_terms map of what to submit")


def load_ledger(ledger):
    """The ledger as a list, or [] if there is not one yet."""
    if not os.path.exists(ledger):
        return []
    with open(ledger) as f:
        return json.load(f)


def gate_evidence(tmpdir):
    """(ok, msg): a redone segment rewrites its record, never duplicates it."""
    d = os.path.join(tmpdir, "evidence")
    ledger = os.path.join(d, "ledger.json")
    ev = {"k": 12345, "run": 10, "note": "first"}
    record(ev, d, "hit_12345.json", ledger, label="DISCOVERY")
    record(dict(ev, note="redone"), d, "hit_12345.json", ledger,
           label="DISCOVERY")
    record({"k": 999, "run": 9}, d, "hit_999.json", ledger, label="DISCOVERY")
    rows = load_ledger(ledger)
    if len(rows) != 2:
        return False, f"evidence: a redone segment duplicated ({len(rows)} rows)"
    if [int(r["k"]) for r in rows] != [999, 12345]:
        return False, "evidence: the ledger is not sorted by the key"
    if rows[1]["note"] != "redone":
        return False, "evidence: the upsert kept the stale record"
    with open(os.path.join(d, "hit_12345.json")) as f:
        if json.load(f)["note"] != "redone":
            return False, "evidence: the evidence file was not rewritten"
    # the naming check, in both directions: the shapes that shipped wrong
    # (the integer under the engine's letter; no oeis_terms) are refused
    good = dict(header("A000001", "k!*m - 1, k = 1..n", "m", 42, [13, 14]),
                settles=[13, 14])
    if not check_names(good, "m")[0] or list(good)[:4] != [
            "sequence", "forms", "m", "oeis_terms"]:
        return False, "evidence: header() does not pass check_names"
    bads = [(dict(good, x=42), "x"),
            ({k: v for k, v in good.items() if k != "oeis_terms"}, "m"),
            (dict(good, oeis_terms={"13": 42}), "m"),
            (dict(good, oeis_terms={"13": 42, "14": 43}), "m"),
            (dict(good, forms="k!*mm - 1"), "m"),
            (dict(good, sequence="factorial"), "m")]
    for bad, key in bads:
        if check_names(bad, key)[0]:
            return False, f"evidence: check_names accepted {bad} under `{key}`"
    return True, ("evidence ok: records are keyed and upserted, so the "
                  "segment redone after an interrupt rewrites its discovery "
                  "instead of appending a second copy; a record that carries "
                  "its integer under a letter the OEIS entry does not use, "
                  "or lacks its oeis_terms map, is refused")
