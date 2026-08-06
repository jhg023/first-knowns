"""Atomic, config-keyed JSON checkpoints.

Rules (repo-wide):
- A checkpoint is only ever written via temp-file + os.replace, so a kill
  at any moment leaves a valid file.
- Every checkpoint carries a config KEY describing the engine parameters
  that make its cursor meaningful. A loaded checkpoint whose key does not
  match the running configuration is IGNORED (never reinterpreted).
- Resume must be idempotent: segment-aligned cursors, so a kill redoes at
  most one segment.
"""

import json
import os


def save(path, state):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, path)


def load(path, expect_key, warn=None):
    """Return the checkpoint dict, or None if absent/mismatched."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        state = json.load(f)
    if state.get("key") != expect_key:
        if warn:
            warn(f"checkpoint key mismatch ({state.get('key')}); ignoring it")
        return None
    return state
