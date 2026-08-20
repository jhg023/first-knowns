"""The drills every project's selftest owes, in one place.

CONVENTIONS.md states four rules that are about INFRASTRUCTURE rather than
about any one problem -- Ctrl+C is a normal exit, a checkpoint survives the
machine, the pool ramps, evidence is upserted -- and rule 6's checklist
requires each of them to be drilled in every project's selftest.  Written
out per project they were four copies of the same eighty lines, and a fifth
project would have been a fifth chance to leave one out.

So they live here, as functions returning `(ok, message)` in the same shape
as a gate.  A project's selftest calls `standard(...)` and prints what comes
back; what stays in the project is the drills about ITS mathematics -- the
parity gate, the canary rediscovery, the classification chain, the
event_kind taxonomy.

These drills MUTATE PROCESS STATE deliberately (they interrupt the shutdown
machinery, they corrupt files) and put it all back, so a selftest can run
them in the middle of a battery and carry on.
"""

import os
import signal
import tempfile

from . import checkpoint as _ckpt
from . import evidence as _ev
from . import pool as _pool
from . import shutdown as _shutdown


def shutdown_drill():
    """(ok, msg): Ctrl+C runs every save, LIFO, deaf, and exits 130.

    The four properties CONVENTIONS.md requires, all of them checkable:
    every registered callback runs; they run in reverse registration order;
    SIGINT is already IGNORED while they run (so the second Ctrl+C -- the
    one an operator presses because the first appeared to do nothing --
    cannot land inside the checkpoint write); a callback that itself raises
    KeyboardInterrupt does not escape; and the exit code is 130 while a
    normal return passes through untouched.
    """
    saved_cbs = list(_shutdown._callbacks)
    saved_flag = _shutdown._shutting_down
    saved_sig = {}
    for name in ("SIGINT", "SIGBREAK", "SIGTERM"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                saved_sig[sig] = signal.getsignal(sig)
            except (ValueError, OSError):
                pass
    try:
        _shutdown._callbacks.clear()
        _shutdown._shutting_down = False
        order, deaf = [], []

        def first():
            order.append("first")
            return "checkpoint at the last segment boundary"

        def second():
            order.append("second")
            raise KeyboardInterrupt          # a second Ctrl+C, mid-shutdown

        def third():
            order.append("third")
            try:
                deaf.append(signal.getsignal(signal.SIGINT) is signal.SIG_IGN)
            except (ValueError, OSError):
                deaf.append(True)            # no signals here to check
            return None

        _shutdown.on_interrupt(first)
        _shutdown.on_interrupt(second)
        _shutdown.on_interrupt(third)

        def interrupted():
            raise KeyboardInterrupt

        rc = _shutdown.graceful(interrupted)
        _shutdown._shutting_down = False
        rc_ok = _shutdown.graceful(lambda: 7)
    finally:
        _shutdown._callbacks[:] = saved_cbs
        _shutdown._shutting_down = saved_flag
        for sig, handler in saved_sig.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError, TypeError):
                pass

    if rc != _shutdown.EXIT_INTERRUPTED:
        return False, f"shutdown drill: exit code {rc}, want 130"
    if order != ["third", "second", "first"]:
        return False, f"shutdown drill: callbacks ran {order}, want LIFO"
    if not all(deaf):
        return False, ("shutdown drill: SIGINT was still live while a save "
                       "callback ran -- a second Ctrl+C could land inside it")
    if rc_ok != 7:
        return False, f"shutdown drill: a normal return came back as {rc_ok}"
    return True, ("shutdown drill: an interrupt runs every save LIFO with "
                  "SIGINT already ignored, a second Ctrl+C inside the "
                  "shutdown does not escape, exit is 130, and a normal "
                  "return passes through")


def durability_drill(tmpdir=None):
    """(ok, msg): a crash mid-save costs one segment, never the cursor.

    The corruption drilled here is the one that actually happened: a
    checkpoint that came back from an abrupt stop as 785 bytes of NUL --
    exactly the right SIZE, no content, because `os.replace` is atomic for
    the directory entry while the DATA was still in the page cache.  With a
    `.bak` behind it the campaign recovers one segment back; without one it
    must STOP, because for a live frontier "no checkpoint" and "corrupt
    checkpoint" demand opposite responses and conflating them silently
    re-sweeps ground already covered.
    """
    own = tmpdir is None
    tmp = tempfile.mkdtemp(prefix="huntlib-drill-") if own else tmpdir
    try:
        path = os.path.join(tmp, "ckpt.json")
        key = "drill/v1"
        _ckpt.save(path, {"key": key, "cursor": 1})
        _ckpt.save(path, {"key": key, "cursor": 2})     # rotates the .bak
        if not os.path.exists(path + ".bak"):
            return False, "durability drill: no .bak was rotated"
        if _ckpt.load(path, key)["cursor"] != 2:
            return False, "durability drill: the current cursor did not load"

        with open(path, "wb") as fh:                    # the real corruption
            fh.write(bytes(785))
        warned = []
        got = _ckpt.load(path, key, warn=warned.append)
        if got is None or got["cursor"] != 1:
            return False, ("durability drill: a 785-NUL checkpoint did not "
                           "recover the cursor from the .bak")
        if not any("RECOVER" in w.upper() for w in warned):
            return False, "durability drill: the recovery was silent"

        os.remove(path + ".bak")
        try:
            _ckpt.load(path, key)
            return False, ("durability drill: an unreadable checkpoint with "
                           "no .bak read as ABSENT instead of raising")
        except _ckpt.CheckpointCorrupt:
            pass

        # and a cursor this configuration cannot read must refuse to start
        _ckpt.save(path, {"key": "some/other/config", "cursor": 9})
        try:
            _ckpt.refuse_mismatch(path, key, fresh=False)
            return False, ("durability drill: a key mismatch was allowed to "
                           "fall through to a fresh sweep at the floor")
        except _ckpt.CursorRefused:
            pass
        _ckpt.refuse_mismatch(path, key, fresh=True)    # --fresh is the escape
        return True, ("durability drill: saves fsync before replace and "
                      "rotate a .bak; a 785-NUL checkpoint recovers one "
                      "segment back and says so; with no .bak it raises "
                      "CheckpointCorrupt; a key mismatch refuses to start "
                      "unless --fresh")
    finally:
        if own:
            for f in os.listdir(tmp):
                try:
                    os.remove(os.path.join(tmp, f))
                except OSError:
                    pass
            os.rmdir(tmp)


def evidence_drill(tmpdir=None):
    """(ok, msg): see huntlib.evidence.gate_evidence."""
    own = tmpdir is None
    tmp = tempfile.mkdtemp(prefix="huntlib-drill-") if own else tmpdir
    try:
        return _ev.gate_evidence(tmp)
    finally:
        if own:
            d = os.path.join(tmp, "evidence")
            for f in (os.listdir(d) if os.path.isdir(d) else []):
                try:
                    os.remove(os.path.join(d, f))
                except OSError:
                    pass
            try:
                os.rmdir(d)
            except OSError:
                pass
            try:
                os.rmdir(tmp)
            except OSError:
                pass


def event_kind_drill(classify, cases):
    """(ok, msg): the discovery-once taxonomy, drilled on a project's own
    `event_kind`.

    `classify(r) -> "DISCOVERY" | "NEAR" | "CENSUS" | None` and `cases` is
    [(r, expected)].  Every project states its own cases because what counts
    as one-short depends on the shape of its ladder; what is shared is the
    insistence that all four outcomes are exercised, so that a project
    cannot pass by having only ever tested the happy one.
    """
    seen = set()
    for r, want in cases:
        got = classify(r)
        if got != want:
            return False, (f"event_kind drill: r = {r} classified {got!r}, "
                           f"want {want!r}")
        seen.add(want)
    missing = {"DISCOVERY", "NEAR", "CENSUS", None} - seen
    if missing:
        return False, (f"event_kind drill: never exercised {sorted(missing, key=str)} "
                       f"-- all four outcomes must be drilled")
    return True, (f"event_kind drill: all four outcomes correct on "
                  f"{len(cases)} cases (discovery / one-short NEAR / counted "
                  f"census / below the floor)")


def standard(pool_factory=None, tmpdir=None):
    """Every repo-wide drill, as [(ok, msg)].  A project's selftest prints
    these alongside its own.

    `pool_factory(workers) -> a context-managed pool` adds the ramp drill;
    a project without a host pool passes None.
    """
    own = tmpdir is None
    tmp = tempfile.mkdtemp(prefix="huntlib-drill-") if own else tmpdir
    try:
        out = [shutdown_drill(), durability_drill(tmp), evidence_drill(tmp)]
        if pool_factory is not None:
            out.append(_pool.ramp_drill(pool_factory))
        return out
    finally:
        if own:
            for root, dirs, files in os.walk(tmp, topdown=False):
                for f in files:
                    try:
                        os.remove(os.path.join(root, f))
                    except OSError:
                        pass
                for d in dirs:
                    try:
                        os.rmdir(os.path.join(root, d))
                    except OSError:
                        pass
            try:
                os.rmdir(tmp)
            except OSError:
                pass
