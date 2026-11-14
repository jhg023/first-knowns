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

  and `burst`: a short-lived pool for one heavy host computation (a
  discovery's confirmations), which on Ctrl+C terminates its workers at
  once instead of waiting out chunks that can run for minutes.

What is NOT here: how many workers, and what a worker computes.  The count
comes from each project's own measurement (classification cost per
survivor against device time per segment -- never from `cpu_count`), and
the work is the project's mathematics.  This module only makes sure that
however many there are, they come up politely.
"""

import contextlib
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


def wait(fut, slice_s=0.25):
    """`fut.result()`, waited for in short slices.  On Windows a blocking
    wait on a future (a lock acquire) is not interruptible: Ctrl+C is held
    until the future completes, which for a long chunk means minutes of a
    stop that appears to do nothing.  Waiting in slices returns to the
    interpreter often enough for the interrupt to be raised at once."""
    while True:
        try:
            return fut.result(timeout=slice_s)
        except TimeoutError:
            continue


@contextlib.contextmanager
def burst(pool_factory, workers):
    """A pool for ONE heavy host computation -- a discovery's confirmations,
    minutes of arithmetic split into chunks -- started when it is needed and
    gone when it is done.

    The difference from `with pool_factory(n) as pool:` is the way out.
    A worker ignores Ctrl+C (`worker_init`), and a chunk can run for
    minutes, so the executor's own __exit__ -- shutdown(wait=True) -- would
    hold an interrupted campaign until every running chunk finished, with
    the checkpoint unwritten and the operator pressing Ctrl+C again.  Here
    a normal exit waits as usual, and ANY exception (KeyboardInterrupt
    included) terminates the workers at once and re-raises, so the stop
    proceeds to the boundary checkpoint in milliseconds.  The caller ramps
    the pool by spacing its first submissions (each starts one interpreter
    while the earlier ones already work), and waits on its futures with
    `wait` (or its own sliced wait), never a bare `result()` -- on Windows
    that would hold the interrupt until the chunk finished.
    """
    pool = pool_factory(int(workers))
    ok = False
    try:
        yield pool
        ok = True
    finally:
        if ok:
            pool.shutdown(wait=True)
        else:
            try:
                kill = getattr(pool, "terminate_workers", None)
                if kill is not None:             # Python 3.14+
                    kill()
                else:
                    for p in list(getattr(pool, "_processes", {}).values()):
                        p.terminate()
            finally:
                pool.shutdown(wait=False, cancel_futures=True)


def burst_drill(pool_factory, workers=2):
    """(ok, msg): an interrupt in the middle of a burst ends it at once.

    Two workers each start a 60-second task; the main thread is interrupted
    0.5 s in (as Ctrl+C would), and the burst must re-raise within a few
    seconds with both workers gone -- not wait out the tasks."""
    import _thread
    import signal
    import threading
    t0 = time.time()
    procs = []
    timer = threading.Timer(0.5, _thread.interrupt_main)
    # interrupt_main does nothing while SIGINT is ignored (an earlier
    # shutdown drill in the same process may have deafened it)
    old = signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        with burst(pool_factory, workers) as pool:
            futs = [pool.submit(_hold, 60.0) for _ in range(workers)]
            procs = list(getattr(pool, "_processes", {}).values())
            timer.start()
            for f in futs:
                wait(f)
        return False, "burst drill: the interrupt never arrived"
    except KeyboardInterrupt:
        el = time.time() - t0
    finally:
        timer.cancel()
        signal.signal(signal.SIGINT, old)
    deadline = time.time() + 10.0
    while any(p.is_alive() for p in procs) and time.time() < deadline:
        time.sleep(0.05)
    alive = sum(1 for p in procs if p.is_alive())
    if el > 10.0 or alive or len(procs) != workers:
        return False, (f"burst drill: interrupted after {el:.1f}s with "
                       f"{alive} of {len(procs)} workers still alive")
    return True, (f"burst drill: an interrupt 0.5 s into two 60-second "
                  f"chunks ends the burst in {el:.1f}s with both workers "
                  f"terminated (a plain executor would have waited a "
                  f"minute)")


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
