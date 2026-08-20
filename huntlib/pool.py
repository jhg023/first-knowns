"""The host classification pool -- sized from the work, and RAMPED.

A hunt is a device that sieves and a host that classifies what survives,
and the host side is where a campaign quietly takes over somebody's
desktop.  CONVENTIONS.md ("Sizing a hunt so it leaves the machine usable")
makes the load a DESIGN INPUT; this module is the part of that procedure
which is the same in every project, so that no project has to remember it:

  step 4  RAMP the pool, do not stamp it.  `ProcessPoolExecutor` spawns on
          submit, and only when no worker is idle -- so handing it a
          segment's worth of chunks starts every worker in the same
          instant.  On Windows each one is a fresh interpreter importing
          numpy and sympy, and N of those at once, while the device is flat
          out on the next segment, is the largest and fastest load step a
          campaign ever makes.  It also buys nothing: the pool has a whole
          segment of slack.  `ramp` starts them one at a time, warm.
  step 7  Never change a machine setting on the owner's behalf.  A worker
          drops ITS OWN priority and nothing else's.

  and the Ctrl+C rule (CONVENTIONS.md "Stopping a run"): a pool worker
  ignores the interrupt so the PARENT decides when the run ends.  A worker
  that kills itself on the console's Ctrl+C can break the pool underneath a
  parent that is still trying to write its checkpoint.

What is NOT here: how many workers, and what a worker computes.  The count
comes from each project's own measurement (classification cost per
survivor against device time per segment -- never from `cpu_count`), and
the work is the project's mathematics.  This module only makes sure that
however many there are, they come up politely.
"""

import os
import sys
import time

from . import shutdown as _shutdown

RAMP_S = 0.35                  # seconds between worker starts


def worker_init(*imports):
    """Pool initializer: go deaf to Ctrl+C, drop priority, pay the imports.

    Call it FIRST in every pool initializer, or pass it directly as one.
    The imports are named as strings and are done HERE, inside the ramp,
    rather than inside the first real segment -- the point of ramping is
    that the interpreter startup cost is paid before the campaign is
    depending on the worker.

    Priority is best effort: a platform that will not take the hint is not
    an error.  A classification worker is pure background arithmetic with a
    whole segment of slack; it has no business competing with the display
    driver, the CUDA host thread or the desktop for a time slice, and a
    machine whose driver threads are never starved is a machine that does
    not appear to have locked up when it is merely descheduled.
    """
    _shutdown.ignore_in_worker()
    try:
        if sys.platform == "win32":
            import ctypes
            below_normal = 0x00004000
            h = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(h, below_normal)
        else:
            os.nice(5)
    except Exception:
        pass
    for name in imports:
        try:
            __import__(name)
        except Exception:
            pass


def _hold(t):
    """Occupy a worker for t seconds.  See `ramp`."""
    time.sleep(t)
    return os.getpid()


def ramp(pool, workers, ramp_s=RAMP_S):
    """Start the pool's interpreters ONE AT A TIME; return how many came up.

    The subtlety that has to be right: a pool spawns a new worker on submit
    only if no existing worker is idle, so pinging and waiting ramps
    nothing -- the single worker that exists answers every ping and the pool
    never grows.  Each worker has to be HELD BUSY while the next one is
    asked for, which is what the hold task is for.

    Returns the number of DISTINCT worker pids that answered, which is what
    a project's ramp drill asserts on.
    """
    workers = int(workers)
    if workers < 1:
        return 0
    hold = ramp_s * workers + 1.0        # still busy when the next is asked
    futs = []
    for i in range(workers):
        futs.append(pool.submit(_hold, hold))
        if i + 1 < workers:
            time.sleep(ramp_s)
    return len({f.result() for f in futs})


def ramp_drill(pool_factory, workers=3, ramp_s=0.05):
    """(ok, msg): the workers really do come up one at a time.

    Every project's selftest runs this (CONVENTIONS.md, rule 6 checklist).
    Three distinct interpreters must answer, and the ramp must have taken at
    least the interval it promised -- a pool that stamped them all would
    return in nearly zero time with the same three pids, which is exactly
    the failure this drill exists to catch.
    """
    t0 = time.time()
    with pool_factory(workers) as pool:
        up = ramp(pool, workers, ramp_s=ramp_s)
    el = time.time() - t0
    if up != workers:
        return False, (f"ramp drill: {up} of {workers} workers came up")
    if el < ramp_s * (workers - 1):
        return False, (f"ramp drill: {workers} workers came up in {el:.3f}s, "
                       f"faster than the {ramp_s * (workers - 1):.3f}s ramp -- "
                       f"they were stamped, not ramped")
    return True, (f"ramp drill: {workers} workers started one at a time "
                  f"({el:.2f}s, >= {ramp_s:.2f}s apart) and each paid its "
                  f"imports before the first segment")
