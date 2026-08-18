# huntlib

> **Authorship disclaimer:** None of this code was written by me — it was
> entirely authored by **Claude (Anthropic's AI)** at my direction.

The shared library behind every hunt in this repository. Projects add
the repo root to `sys.path` and import:

```python
from huntlib.hlog import log, banner, census_str, Heartbeat
from huntlib import checkpoint
from huntlib.primes import mr_is_prime, factor_witness, MR_VALID_BELOW
from huntlib.gpu import barrett_magics
from huntlib import scoring
```

| module | contents |
|--------|----------|
| `hlog` | timestamped tagged logging + the repo-wide tag taxonomy; `census_str` — the one format every `[STATUS]` line uses for the census counts per run length (`census 7:280 8:71 9:28 10:8`); `Heartbeat` — the wall-clock `[STATUS]` timer thread every launcher runs (mark positions at segment boundaries, `doing()` around long steps; it reports the end-to-end rate and, when nothing has moved, what the launcher is stuck on) |
| `checkpoint` | atomic (temp + `os.replace`) config-keyed JSON checkpoints |
| `primes` | deterministic 7-base Miller–Rabin (valid < 3.317×10²⁴, bound exported as a constant) and factor witnesses (trial division, a bounded Brent rho, then sympy's ECM — never unbounded: a rho on a semiprime run breaker once stalled a live campaign for 105 s) |
| `gpu` | Barrett magic-multiply reciprocals: the host-side helper and the canonical CUDA snippet that every kernel uses in place of hardware u64 division |
| `scoring` | the gates × fingerprinted-benchmark SCORE contract |

Design rule: huntlib holds only what is genuinely identical across
projects. Kernels, wheels, and problem mathematics stay in each project —
a reader auditing a hunt should find all of its *mathematics* in one
directory, and only *infrastructure* here.

One deliberate exception to sharing: each project's `*_reference.py`
oracle does **not** use huntlib's Miller–Rabin — oracles stick to sympy
so that the verification legs stay independent.
