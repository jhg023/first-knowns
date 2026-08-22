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


def cursor_policy_drill(policy, tmpdir=None):
    """Every key a policy CLAIMS to read must pass every reader it has.

    This is the drill for the one bug the whole battery could not see, and
    it has been paid for twice.  A launcher grows a second class of readable
    key -- an inherited engine version, a re-denominated wheel -- and the
    author teaches `load` about it and misses `refuse_mismatch`, which
    checks the key independently, or `--status`, which reads it a third
    time.  Every gate stays green, because nothing in a gate battery ever
    writes a checkpoint carrying an OLD key, and the campaign then refuses
    to start the first time it is run for real, at the owner's hand.

    So: write a checkpoint under each declared key in turn and make both
    readers answer.  A key the policy says it can read must (1) not be
    refused and (2) come back from load with the right classification.  A
    key it has never heard of must be refused, and --fresh must override
    that; those two are what stop a "fix" that simply accepts everything.
    """
    own = tmpdir is None
    tmp = tempfile.mkdtemp(prefix="huntlib-cursor-") if own else tmpdir
    path = os.path.join(tmp, "cursor_policy_drill.json")
    pol = policy.at(path)
    kinds = ({policy.key: "own"}
             | {k: "inherited" for k in policy.accept}
             | {k: "adopted" for k in policy.adopt})
    try:
        for key, want in kinds.items():
            _ckpt.save(path, {"key": key, "k": 12345, "j": 7})
            try:
                pol.refuse_mismatch()
            except _ckpt.CursorRefused:
                return False, (
                    f"CURSOR POLICY FAIL: the policy lists {key!r} as "
                    f"readable but refuse_mismatch rejects it -- the "
                    f"campaign would refuse to start on that cursor")
            state, kind = pol.load()
            if state is None:
                return False, (f"CURSOR POLICY FAIL: {key!r} is listed as "
                               f"readable but load() ignored it")
            if kind != want:
                return False, (f"CURSOR POLICY FAIL: {key!r} loaded as "
                               f"{kind!r}, expected {want!r}")
            if int(state.get("k", 0)) != 12345:
                return False, f"CURSOR POLICY FAIL: {key!r} lost its cursor"

        # ...and a key it has never heard of must still stop the campaign
        _ckpt.save(path, {"key": "a-configuration-that-never-existed",
                          "k": 999, "j": 1})
        try:
            pol.refuse_mismatch()
        except _ckpt.CursorRefused:
            pass
        else:
            return False, ("CURSOR POLICY FAIL: an unknown key did NOT "
                           "refuse -- a campaign would silently restart at "
                           "the floor and abandon the frontier")
        if pol.load()[0] is not None:
            return False, ("CURSOR POLICY FAIL: an unknown key was loaded "
                           "anyway")
        pol.refuse_mismatch(fresh=True)          # --fresh must override
    finally:
        if own:
            try:
                for f in os.listdir(tmp):
                    os.remove(os.path.join(tmp, f))
                os.rmdir(tmp)
            except OSError:
                pass
    return True, (f"cursor policy ok: all {len(kinds)} declared key(s) pass "
                  f"BOTH readers with the right classification "
                  f"({', '.join(sorted(set(kinds.values())))}); an unknown "
                  f"key refuses; --fresh overrides")


def standard(pool_factory=None, tmpdir=None, cursor=None):
    """Every repo-wide drill, as [(ok, msg)].  A project's selftest prints
    these alongside its own.

    `pool_factory(workers) -> a context-managed pool` adds the ramp drill;
    a project without a host pool passes None.

    `cursor` is the launcher's CursorPolicy and every project should pass
    it.  It is a keyword with a default only so that adding it did not
    break the launchers that predate it -- the drill it enables is the one
    that catches "this configuration cannot read its own predecessor's
    checkpoint", which no other gate can see because no other gate ever
    writes an old key.
    """
    own = tmpdir is None
    tmp = tempfile.mkdtemp(prefix="huntlib-drill-") if own else tmpdir
    try:
        out = [shutdown_drill(), durability_drill(tmp), evidence_drill(tmp)]
        if cursor is not None:
            out.append(cursor_policy_drill(cursor, tmp))
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
