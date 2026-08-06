"""huntlib -- shared machinery for the hunts in this repository.

Every project in this repo follows the same skeleton (see ../CONVENTIONS.md):
an oracle, a CPU engine, a GPU engine, a checkpointed launcher, and a scored
benchmark. The pieces that are identical across projects live here:

    huntlib.hlog        timestamped, tagged event logging
    huntlib.checkpoint  atomic JSON checkpoints (config-keyed, resumable)
    huntlib.primes      deterministic 64-bit Miller-Rabin, factor witnesses
    huntlib.gpu         Barrett reciprocal helpers for CUDA kernels
    huntlib.scoring     gates x fingerprinted-benchmark score runner

Projects import it by adding the repo root to sys.path:

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from huntlib import hlog, checkpoint, primes
"""

from . import checkpoint, gpu, hlog, primes, scoring  # noqa: F401
