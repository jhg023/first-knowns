"""Atomic, config-keyed, CRASH-DURABLE JSON checkpoints.

Rules (repo-wide):
- A checkpoint is only ever written via temp-file + os.replace, so a kill
  at any moment leaves a valid file.
- The temp file is FLUSHED AND FSYNCED BEFORE THE REPLACE. `os.replace` is
  atomic with respect to the directory ENTRY, not to the file's DATA: on
  NTFS (and on ext4 with delayed allocation) the rename can reach the disk
  while the bytes are still in the page cache. A machine that dies in that
  window leaves a file of exactly the right SIZE full of NUL. This is not
  hypothetical -- it is how this project once lost a live campaign cursor:
  785 bytes, every one of them zero. fsync closes it.
- The previous good checkpoint is kept alongside as `<path>.bak`, so even a
  torn write or a truncated file leaves a recoverable cursor one segment
  behind. `load` falls back to it automatically and says so.
- A checkpoint that is present but unreadable is NEVER silently treated as
  absent: `load` distinguishes "no checkpoint" (None) from "checkpoint is
  corrupt" (CheckpointCorrupt), because for a live frontier those two
  demand opposite responses -- start, and stop.
- Every checkpoint carries a config KEY describing the engine parameters
  that make its cursor meaningful. A loaded checkpoint whose key does not
  match the running configuration is IGNORED (never reinterpreted).
- Resume must be idempotent: segment-aligned cursors, so a kill redoes at
  most one segment.
"""

import json
import os


class CheckpointCorrupt(RuntimeError):
    """The file exists and cannot be read as a checkpoint."""


def save_json(path, obj):
    """Write any JSON-able object durably: temp -> fsync -> replace, .bak kept.

    The rotation order matters. The backup is taken from the file that is
    already on disk BEFORE the new one lands, so at every instant at least
    one of {path, path.bak} is complete.

    Separate from `save` because a checkpoint is not the only file a
    campaign cannot afford half of: an evidence JSON is the entire artefact
    of a discovery, and a torn ledger is worse than a stale one.
    """
    tmp = path + ".tmp"
    # newline="\n" so the repo's LF rule holds for the JSONs that get
    # committed (evidence files and ledgers); the default translates on
    # Windows and quietly commits CRLF.
    with open(tmp, "w", newline="\n") as f:
        json.dump(obj, f, indent=1)
        f.flush()
        os.fsync(f.fileno())          # the bytes, not just the directory entry
    if os.path.exists(path):
        bak = path + ".bak"
        try:
            os.replace(path, bak)
        except OSError:               # a backup is best-effort; never fatal
            pass
    os.replace(tmp, path)


def save(path, state):
    """Write a checkpoint durably.  See save_json."""
    save_json(path, state)


def _read(path):
    with open(path) as f:
        state = json.load(f)
    if not isinstance(state, dict):
        raise ValueError("checkpoint is not a JSON object")
    return state


def load(path, expect_key, warn=None):
    """Return the checkpoint dict, or None if absent/key-mismatched.

    Raises CheckpointCorrupt if the file exists, cannot be parsed, and no
    usable `.bak` stands behind it.
    """
    if not os.path.exists(path):
        return None
    try:
        state = _read(path)
    except Exception as e:
        bak = path + ".bak"
        if os.path.exists(bak):
            try:
                state = _read(bak)
            except Exception as e2:
                raise CheckpointCorrupt(
                    f"{path} is unreadable ({e}) and so is {bak} ({e2})")
            if warn:
                warn(f"{path} is unreadable ({e}); RECOVERED the previous "
                     f"checkpoint from {bak} -- at most one segment is redone")
        else:
            raise CheckpointCorrupt(
                f"{path} is unreadable ({e}) and there is no {bak}. A hard "
                f"crash during a save can leave a right-sized file of NUL; "
                f"the cursor in it is gone. Pass --fresh to restart the "
                f"sweep deliberately, or edit in a known-good cursor.")
    if state.get("key") != expect_key:
        if warn:
            warn(f"checkpoint key mismatch ({state.get('key')}); ignoring it")
        return None
    return state


class CursorRefused(RuntimeError):
    """A cursor file exists that this configuration must not reinterpret."""


def refuse_mismatch(path, expect_key, fresh=False, describe=None):
    """Raise unless it is SAFE to start: a key mismatch must halt the run.

    `load` ignores a checkpoint whose key does not match, which is the right
    default for a stale file and exactly the wrong one for a live frontier:
    "ignore" falls straight through to a fresh cursor at zero, and a
    campaign that silently restarts at the floor after a wheel change
    abandons every unit of line it had already swept. Reinterpreting the
    cursor instead is just as wrong in the other direction -- a count of
    wheel PERIODS read against a different period once misplaced a frontier
    by 31x.

    Both wrong answers are prevented the same way: an existing cursor this
    configuration cannot read is a REFUSAL. `--fresh` says "discard it, I
    mean it"; a project with a migration path offers that instead.

    `describe(state) -> str` may add a line saying what is being refused,
    in the project's own units.
    """
    if fresh or not os.path.exists(path):
        return
    try:
        state = _read(path)
    except Exception as e:
        bak = path + ".bak"
        if os.path.exists(bak):
            try:
                _read(bak)
                return              # load() will recover it and say so
            except Exception:
                pass
        raise CheckpointCorrupt(
            f"{path} exists but cannot be read ({e}), and no usable {bak} "
            f"stands behind it. A hard crash during a save can leave a "
            f"right-sized file of NUL bytes -- that is exactly what happened "
            f"here once, and it is why saves are fsynced and backed up now. "
            f"The cursor in it is gone: pass --fresh to restart the sweep "
            f"deliberately, or restore a cursor by hand.")
    if state.get("key") == expect_key:
        return
    extra = ""
    if describe:
        try:
            extra = "\n        stored     : " + str(describe(state))
        except Exception:
            extra = ""
    raise CursorRefused(
        f"a campaign cursor exists but this configuration cannot read it.\n"
        f"        stored key : {state.get('key')!r}\n"
        f"        wanted key : {expect_key!r}{extra}\n"
        f"  Starting anyway would begin a FRESH sweep and abandon that "
        f"frontier. Pass --fresh to discard it deliberately.")
