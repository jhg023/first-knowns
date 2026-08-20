"""huntlib -- shared machinery for the hunts in this repository.

Every project in this repo follows the same skeleton (see ../CONVENTIONS.md):
an oracle, a CPU engine, a GPU engine, a checkpointed launcher, and a scored
benchmark. The pieces that are identical across projects live here:

    huntlib.hlog        timestamped, tagged event logging + the heartbeat
    huntlib.checkpoint  atomic JSON checkpoints (config-keyed, resumable)
    huntlib.primes      deterministic 64-bit Miller-Rabin, factor witnesses
    huntlib.certificate BLS75 primality proofs above the Miller-Rabin bound
    huntlib.gpu         Barrett reciprocal helpers for CUDA kernels
    huntlib.pool        the host classification pool: ramped, polite
    huntlib.frontier    settledness bookkeeping and the census counters
    huntlib.rungs       the progress ladder of an indefinite campaign
    huntlib.evidence    first-occurrence evidence files and their ledger
    huntlib.scoring     gates x fingerprinted-benchmark score runner
    huntlib.shutdown    graceful Ctrl+C: checkpoint, one line, no traceback
    huntlib.drills      the repo-wide selftest drills every project owes

Projects import it by adding the repo root to sys.path:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import hlog, checkpoint, primes

Design rule: huntlib holds only what is genuinely identical across
projects. Kernels, wheels and problem mathematics stay in each project -- a
reader auditing a hunt should find all of its MATHEMATICS in one directory
and only INFRASTRUCTURE here. Two deliberate consequences: the oracles do
not use huntlib's Miller-Rabin (they stay sympy-pure, so the verification
legs stay independent), and `event_kind` stays in each project even though
the rule it implements is repo-wide.
"""

from . import (certificate, checkpoint, drills, evidence, frontier,  # noqa: F401
               gpu, hlog, pool, primes, rungs, scoring, shutdown)    # noqa: F401
