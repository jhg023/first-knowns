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

import contextlib
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


def _via_policy(accept, adopt, fn):
    """Refuse an old-key list that did not come from a CursorPolicy.

    The lists themselves are fine; passing them AT A CALL SITE is not,
    because there are three call sites and the bug is forgetting one. Twice
    now a launcher has taught `load` about its predecessor's key and left
    `refuse_mismatch` -- which checks the key independently -- to reject it,
    producing a green battery and a campaign that would not start. So the
    only way to declare an old key is to build a CursorPolicy, which owns
    every reader at once and is drilled by `drills.cursor_policy`.
    """
    if (accept or adopt) and not getattr(fn, "_policy", False):
        raise ValueError(
            "accept=/adopt= may only be passed by a CursorPolicy. Build one "
            "next to your CONFIG_KEY --\n"
            "    CURSOR = checkpoint.CursorPolicy(CKPT, CONFIG_KEY,\n"
            "                                     accept=..., adopt=...)\n"
            "-- route EVERY reader through it (the campaign's load, "
            "--status, and the refusal in main()), and pass it to "
            "drills.standard(cursor=CURSOR). Three separate call sites take "
            "an old-key list, and a list given to two of them is exactly the "
            "bug this refuses: the battery stays green and the campaign will "
            'not start. See CONVENTIONS.md "Reading an existing cursor".')


def load(path, expect_key, warn=None, accept=(), adopt=()):
    """Return the checkpoint dict, or None if absent/key-mismatched.

    `accept` names OLD keys whose swept line the current configuration
    inherits -- the case being an engine version that is gated to return
    the identical survivor stream, where discarding the cursor would
    re-sweep line already covered for no gain.  A migration is never
    silent: it is warned, so the log says which cursor was adopted and
    from what.  Anything that changes COVERAGE (a different wheel, a
    different sieve depth) must not be listed here; it belongs in the key.

    Raises CheckpointCorrupt if the file exists, cannot be parsed, and no
    usable `.bak` stands behind it.
    """
    _via_policy(accept, adopt, load)
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
    got_key = state.get("key")
    if got_key != expect_key:
        if got_key in tuple(accept):
            if warn:
                warn(f"checkpoint MIGRATED from {got_key} to {expect_key}: "
                     f"the configurations cover the same line, so the cursor "
                     f"carries over instead of re-sweeping it")
        elif got_key in tuple(adopt):
            if warn:
                warn(f"checkpoint ADOPTED from {got_key} by {expect_key}: "
                     f"these configurations do NOT cover the same line, so "
                     f"only the claim 'every k below this is swept' carries "
                     f"over -- the caller must re-denominate the cursor "
                     f"itself and must not reuse any index from it")
        else:
            if warn:
                warn(f"checkpoint key mismatch ({got_key}); ignoring it")
            return None
    return state


@contextlib.contextmanager
def _policy_call(fn):
    """Mark a reader as being called BY a CursorPolicy, for _via_policy."""
    fn._policy = True
    try:
        yield
    finally:
        fn._policy = False


class CursorPolicy:
    """Which stored keys this configuration may start from -- in ONE place.

    THE FAILURE THIS EXISTS TO PREVENT, which has now happened twice in this
    repo and both times only at the owner's hand:

        A launcher grows a second class of readable key -- an engine version
        whose swept line it inherits, or an older wheel whose cursor it
        re-denominates.  The author teaches `load` about it, because that is
        where the reading obviously happens, and misses that `refuse_mismatch`
        checks the key INDEPENDENTLY, and that `--status` reads it a third
        time.  Nothing in the gate battery ever writes a checkpoint with an
        old key, so every gate stays green and the campaign refuses to start
        the first time somebody runs it for real.

    Passing the same `accept=` list to three call sites is the shape of the
    bug: it is a thing you can forget at one of them.  So the list stops
    being an argument and becomes an OBJECT that owns all three readers.
    A launcher builds one of these next to its CONFIG_KEY and never calls
    `load` or `refuse_mismatch` directly again -- and `drills.cursor_policy`
    proves the readers agree, by writing a checkpoint under every key the
    policy claims and putting each reader in front of it.

    Two classes of old key, and they are NOT interchangeable:

      accept  the old configuration covers the IDENTICAL line -- an engine
              version gated to return the same survivor stream.  The cursor,
              including its indices, carries over untouched.
      adopt   the old configuration covers DIFFERENT line (a new wheel, a
              new sieve depth).  Only the arithmetic claim "every k below
              this is swept" carries over; the launcher must re-denominate
              the cursor onto its own units, flooring so no gap opens, and
              must not reuse any index from it.

    Anything that moves coverage belongs in `adopt`, never in `accept`.
    """

    def __init__(self, path, key, accept=(), adopt=()):
        self.path = path
        self.key = key
        self.accept = tuple(accept)
        self.adopt = tuple(adopt)
        clash = set(self.accept) & set(self.adopt)
        if clash:
            raise ValueError(
                f"{sorted(clash)} are listed as both accept and adopt: a "
                f"stored key either covers the identical line or it does "
                f"not, and the two are handled differently")
        if self.key in self.accept or self.key in self.adopt:
            raise ValueError(
                f"the live key {self.key!r} is also listed as an old one")

    def readable(self):
        """Every stored key this configuration is willing to start from."""
        return (self.key,) + self.accept + self.adopt

    def at(self, path):
        """The same policy against a different file -- for drills."""
        return CursorPolicy(path, self.key, self.accept, self.adopt)

    def refuse_mismatch(self, fresh=False, describe=None):
        with _policy_call(refuse_mismatch):
            refuse_mismatch(self.path, self.key, fresh=fresh,
                            describe=describe,
                            accept=self.accept, adopt=self.adopt)

    def load(self, warn=None):
        """(state, kind) with kind "own" / "inherited" / "adopted" / None."""
        with _policy_call(load):
            state = load(self.path, self.key, warn=warn,
                         accept=self.accept, adopt=self.adopt)
        if state is None:
            return None, None
        got = state.get("key")
        if got == self.key:
            return state, "own"
        return state, ("inherited" if got in self.accept else "adopted")


class CursorRefused(RuntimeError):
    """A cursor file exists that this configuration must not reinterpret."""


def refuse_mismatch(path, expect_key, fresh=False, describe=None, accept=(),
                    adopt=()):
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
    _via_policy(accept, adopt, refuse_mismatch)
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
    if (state.get("key") == expect_key
            or state.get("key") in tuple(accept)
            or state.get("key") in tuple(adopt)):
        return                      # see load(): `accept` covers the same
                                    # line, `adopt` does not but is still
                                    # readable; both are warned when read
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
