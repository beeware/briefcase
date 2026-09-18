BRIEFCASE_EXIT_SUCCESS_SIGNAL = ">>>>>>>>>> EXIT 0 <<<<<<<<<<"
EXIT_SUCCESS_NOTIFY = ">>> successfully started...exiting <<<"

# A GUI app on Windows is built against the GUI subsystem, so it has no console, and
# its stdout/stderr never reach the pipe that Briefcase is streaming. As a result, an
# app that fails during startup exits with no diagnostic output whatsoever (see #2969).
#
# To make those failures diagnosable, the app records its progress through startup to
# the file nominated by the BRIEFCASE_STARTUP_LOG environment variable. If the app
# fails to run, Briefcase reports the contents of that file. The last checkpoint
# recorded identifies how far the app got before it died.
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
'''
