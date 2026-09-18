BRIEFCASE_EXIT_SUCCESS_SIGNAL = ">>>>>>>>>> EXIT 0 <<<<<<<<<<"
EXIT_SUCCESS_NOTIFY = ">>> successfully started...exiting <<<"

# When a Windows app fails in CI, no app output is seen by Briefcase at all, so there
# is nothing to diagnose the failure with (see #2969). A GUI app's output *is* normally
# visible when run interactively, so the reason it goes missing under CI is not yet
# understood.
#
# To make these failures diagnosable regardless, the app records its progress to the
# file nominated by the BRIEFCASE_STARTUP_LOG environment variable; a file write does
# not depend on stdout being usable. If the app fails to run, Briefcase reports the
# contents of that file. The last checkpoint recorded identifies how far the app got.
#
# The state of the app's own stdout is also recorded, to determine whether the missing
# output is because stdout is absent, is being silently discarded, or is written
# successfully but lost before Briefcase can read it.
STARTUP_DIAGNOSTICS = '''
import atexit
import faulthandler
import os
import sys
import traceback

_startup_log = os.environ.get("BRIEFCASE_STARTUP_LOG")
_startup_log_file = None

if _startup_log:
    # Line buffered, so a checkpoint is on disk before the next step is attempted.
    _startup_log_file = open(_startup_log, "w", buffering=1, encoding="UTF-8")

    # Route native crash reports (segfaults, aborts) into the diagnostics file. A
    # crash inside a GUI toolkit's native libraries is otherwise entirely silent.
    faulthandler.enable(file=_startup_log_file)

    # Report the exit status, so a "clean" early exit can be distinguished from a
    # crash, and record any exception that caused the interpreter to exit.
    def _log_exit():
        checkpoint("interpreter exiting")
        _startup_log_file.flush()

    atexit.register(_log_exit)

    def _log_exception(exc_type, exc_value, exc_traceback):
        checkpoint("UNHANDLED EXCEPTION")
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=_startup_log_file
        )
        _startup_log_file.flush()

    sys.excepthook = _log_exception


def checkpoint(message):
    """Record a startup checkpoint to the diagnostics file (if enabled)."""
    if _startup_log_file is not None:
        _startup_log_file.write(f"CHECKPOINT: {message}\\n")

    # Also print, for the benefit of platforms where output *is* visible.
    print(f"CHECKPOINT: {message}", flush=True)


def _probe(message):
    """Record a diagnostic detail about the app's own output streams."""
    if _startup_log_file is not None:
        _startup_log_file.write(f"PROBE: {message}\\n")


def probe_stdout():
    """Record the state of the app's stdout and stderr.

    Briefcase sees no app output at all when a Windows app fails under CI, even
    though a GUI app's output is normally visible when run interactively. This
    records enough detail to tell whether stdout is missing entirely, is being
    silently discarded, or is being written successfully but lost downstream.
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        _probe(f"sys.{name} = {stream!r}")

        # A None stream makes print() a silent no-op; this is the most likely
        # explanation for output vanishing without any error being raised.
        if stream is None:
            continue

        for attr in ("fileno", "isatty"):
            try:
                _probe(f"sys.{name}.{attr}() = {getattr(stream, attr)()}")
            except Exception as e:
                _probe(f"sys.{name}.{attr}() raised {type(e).__name__}: {e}")

        for attr in ("closed", "encoding", "line_buffering", "buffer"):
            try:
                _probe(f"sys.{name}.{attr} = {getattr(stream, attr, '<missing>')!r}")
            except Exception as e:
                _probe(f"sys.{name}.{attr} raised {type(e).__name__}: {e}")

    # Attempt an explicit write, and report how many characters were accepted. If
    # this reports a successful write that Briefcase never sees, the output is
    # being lost after the app hands it over, rather than never being produced.
    marker = ">>> STDOUT PROBE: if you can see this, app stdout reaches Briefcase <<<"
    try:
        written = sys.stdout.write(marker + "\\n")
        sys.stdout.flush()
        _probe(f"sys.stdout.write() accepted {written} of {len(marker) + 1} chars")
    except Exception as e:
        _probe(f"sys.stdout.write() raised {type(e).__name__}: {e}")

    # Write the same marker at the OS level, bypassing Python's stdout object
    # entirely. If this arrives but the Python-level write doesn't, the problem is
    # in Python's stream setup rather than the pipe itself.
    try:
        os.write(1, b">>> FD1 PROBE: raw write to fd 1 reaches Briefcase <<<\\n")
        _probe("os.write(1, ...) succeeded")
    except Exception as e:
        _probe(f"os.write(1, ...) raised {type(e).__name__}: {e}")
'''
