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
    return True, ("evidence ok: records are keyed and upserted, so the "
                  "segment redone after an interrupt rewrites its discovery "
                  "instead of appending a second copy")
