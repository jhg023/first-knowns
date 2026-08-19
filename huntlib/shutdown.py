"""Graceful shutdown -- Ctrl+C ENDS a hunt, it never crashes one.

Every program in this repository is stopped by hand: the campaigns run for
days and the operator decides when they end.  So an interrupt is a NORMAL
EXIT PATH and gets the same care as any other, which means all four of:

  * the checkpoint on disk is left at the last SEGMENT BOUNDARY -- never a
    mid-segment save (counts are updated per value, so persisting a
    part-classified segment double-counts the census when the segment is
    redone) and never a torn write;
  * ONE [STAGE] line says what stopped and where it stopped;
  * NO TRACEBACK reaches the console -- not from the launcher, not from a
    classification worker, and not from a SECOND Ctrl+C landing inside the
    shutdown itself;
  * the exit code is 130, the conventional "terminated by SIGINT", so a
    supervising script can tell a stop from a crash.

The second Ctrl+C is the one that bites, and it is the common case: the
operator presses it, the launcher takes a second to save and stop its pool,
nothing appears to happen, so they press it again.  That second interrupt
lands inside the exception handler and Python prints the pair of them
("During handling of the above exception, another exception occurred"),
exits 0xC000013A -- and, worst of all, it can land inside the checkpoint
write, in the window between the .bak rotation and the replace, where the
campaign cursor exists in neither file.  So the FIRST thing the shutdown
does is go deaf: SIGINT and SIGBREAK are set to SIG_IGN before any callback
runs, and every callback is additionally wrapped, so nothing an operator
can type from the console can interrupt a checkpoint save.

Usage -- the launcher registers what to do, and wraps main():

    from huntlib import shutdown

    shutdown.on_interrupt(lambda: save_boundary())   # returns a message
    ...
    if __name__ == "__main__":
        sys.exit(shutdown.graceful(main))

and every process pool passes `ignore_in_worker` (or calls it first thing
in its own initializer), so the workers stay quiet and let the PARENT
decide when the run ends -- a worker that kills itself on Ctrl+C can break
the pool underneath a parent that is still trying to write its checkpoint.
"""

import signal
import sys

from .hlog import log

EXIT_INTERRUPTED = 130            # conventional: terminated by SIGINT

_callbacks = []                   # run LIFO on the way out
_shutting_down = False


def on_interrupt(cb):
    """Register `cb` to run when the program is interrupted.

    Callbacks run in reverse registration order.  A callback may return a
    short string, which is logged as a [STAGE] line -- that is how the
    launcher reports where its checkpoint ended up.  Registering is cheap
    and idempotent-friendly: re-register to replace what a callback closes
    over, the list is short and the last one registered runs first.
    """
    _callbacks.append(cb)
    return cb


def ignore_in_worker():
    """Deafen a pool worker to Ctrl+C.  Call it FIRST in every pool
    initializer.

    On Windows a console Ctrl+C is delivered to every process attached to
    the console, workers included; on POSIX it goes to the whole foreground
    process group.  Either way the parent is the only process that knows
    what a clean stop looks like, so workers ignore the signal and end when
    the parent shuts the pool down.
    """
    _deafen()


def _deafen():
    """Make SIGINT/SIGBREAK do nothing at all from here on."""
    for name in ("SIGINT", "SIGBREAK"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, signal.SIG_IGN)
            except (ValueError, OSError):     # not the main thread, or n/a
                pass


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def arm():
    """Route the other polite stop signals through the same path as Ctrl+C.

    SIGTERM (a supervisor asking to stop) and, on Windows, SIGBREAK
    (Ctrl+Break) both default to killing the process where it stands, with
    no checkpoint.  `graceful` arms them; call it directly only if you run
    a loop without `graceful`.
    """
    for name in ("SIGTERM", "SIGBREAK"):
        sig = getattr(signal, name, None)
        if sig is not None:
            try:
                signal.signal(sig, _raise_interrupt)
            except (ValueError, OSError):
                pass


def shutdown(why="Ctrl+C"):
    """Run the registered callbacks deaf to further signals; return 130."""
    global _shutting_down
    if _shutting_down:                        # re-entered: say nothing twice
        return EXIT_INTERRUPTED
    _shutting_down = True
    _deafen()                                 # BEFORE anything is written
    log("STAGE", f"interrupted ({why}) -- stopping cleanly; further Ctrl+C "
                 f"is ignored until the checkpoint is written")
    for cb in reversed(_callbacks):
        try:
            msg = cb()
        except BaseException as e:            # including a second interrupt
            log("WARN", f"shutdown step failed: {type(e).__name__}: {e}")
            continue
        if msg:
            log("STAGE", str(msg))
    log("STAGE", f"stopped by request; exit {EXIT_INTERRUPTED}")
    return EXIT_INTERRUPTED


def graceful(fn, *args, **kwargs):
    """Run `fn` and return its exit code; on interrupt return 130 instead.

    Wrap main() in this.  It is the ONLY place a KeyboardInterrupt is
    allowed to be caught in a launcher, which is what makes "no traceback"
    checkable: an interrupt anywhere -- the prelude, the pool ramp, a
    verification, the segment loop, the final save -- takes exactly one
    path out.
    """
    arm()
    try:
        return fn(*args, **kwargs)
    except KeyboardInterrupt:
        return shutdown()
    finally:
        sys.stdout.flush()
