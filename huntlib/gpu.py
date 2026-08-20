"""GPU-side helpers shared by the CUDA kernels in this repo.

The kernels themselves are project-specific and live in each project as
inline CUDA C (CuPy RawKernel). What is shared is the arithmetic trick
they all use:

Barrett magic-multiply modulo
-----------------------------
Hardware 64-bit integer division costs ~20-40 cycles on consumer GPUs and
appears in every sieve inner loop as `p % q`. We replace it: for a fixed
u32 modulus q, precompute MAGIC = floor(2^64 / q) once on the host. Then

    qhat = __umul64hi(p, MAGIC)          # upper half of p * MAGIC
    r    = p - qhat * q                  # in [0, 3q); at most 2 subtracts

because qhat lies in [floor(p/q) - 2, floor(p/q)]. Three cheap ops and
two predicated subtracts instead of a division. Exactness is never
assumed: every project pins its GPU stream bit-for-bit against a plain
`%`-based CPU engine in a parity gate before the kernel is trusted.

The corresponding CUDA snippet (paste into kernels; keep in sync with
barrett_magics below):

    unsigned long long qhat = __umul64hi(p, magic[j]);
    unsigned long long r64  = p - qhat * q;
    if (r64 >= q) r64 -= q;
    if (r64 >= q) r64 -= q;
"""

import numpy as np


def barrett_magics(moduli):
    """floor(2^64 / q) for each u32 modulus q, as a u64 numpy array."""
    return np.array([(1 << 64) // int(q) for q in np.asarray(moduli).tolist()],
                    dtype=np.uint64)


def device_report(held_bytes=None):
    """One line of machine state for a campaign's opening log.

    A hunt that runs for days on somebody's desktop should say, in its own
    log, how much of the machine it is taking and what the machine's limits
    were when it started -- so the log itself can answer "how much VRAM did
    it hold" and "was the card at stock limits" afterwards, without anyone
    having to reconstruct it.

    Everything here is READ-ONLY.  The campaign reports the machine's state
    and never changes a setting on the owner's behalf (CONVENTIONS.md,
    "Sizing a hunt so it leaves the machine usable", step 7): it may name
    the lever, it may not pull it.

    `held_bytes` is what the project's own engine has allocated; only the
    project knows which of its arrays those are.
    """
    bits = []
    try:
        import cupy as cp
        dev = cp.cuda.Device()
        props = cp.cuda.runtime.getDeviceProperties(dev.id)
        free, total = cp.cuda.runtime.memGetInfo()
        name = props["name"]
        name = name.decode() if isinstance(name, bytes) else str(name)
        bits.append(f"{name}, {props['multiProcessorCount']} SMs")
        held = ("" if held_bytes is None
                else f" (this engine holds {held_bytes / 2**30:.2f} GiB)")
        bits.append(f"VRAM {(total - free) / 2**30:.1f}/{total / 2**30:.1f} "
                    f"GiB used{held}")
    except Exception:
        pass
    try:
        import subprocess
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=power.limit,power.max_limit,"
             "clocks.max.sm,temperature.gpu,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10)
        if out.returncode == 0 and out.stdout.strip():
            pl, pmax, clk, temp, drv = [x.strip() for x in
                                        out.stdout.strip().splitlines()[0]
                                        .split(",")]
            cap = "" if pl == pmax else "  (CAPPED)"
            bits.append(f"driver {drv}, power limit {pl}/{pmax} W{cap}, "
                        f"max SM clock {clk} MHz, {temp} C")
    except Exception:
        pass
    return "; ".join(bits) if bits else "device state unavailable"


def nbytes_of(*objs):
    """Total nbytes of arrays, dicts of arrays and lists of them -- the
    input `device_report` wants, without every project writing the walk."""
    total = 0
    stack = list(objs)
    while stack:
        o = stack.pop()
        if o is None:
            continue
        if isinstance(o, dict):
            stack.extend(o.values())
        elif isinstance(o, (list, tuple, set)):
            stack.extend(o)
        else:
            total += int(getattr(o, "nbytes", 0) or 0)
    return total
