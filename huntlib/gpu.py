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
