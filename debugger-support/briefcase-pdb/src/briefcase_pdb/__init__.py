import os
import sys
import traceback

from ._remote_debugger import start_pdb

REMOTE_DEBUGGER_STARTED = False


def start_remote_debugger():
    global REMOTE_DEBUGGER_STARTED
    REMOTE_DEBUGGER_STARTED = True

    # check verbose output
    verbose = os.environ.get("BRIEFCASE_DEBUG", "0") == "1"

    # reading config
    config_str = os.environ.get("BRIEFCASE_DEBUGGER", None)

    # skip debugger if no config is set
    if config_str is None:
        if verbose:
            print(
                "No 'BRIEFCASE_DEBUGGER' environment variable found. Debugger not starting."
            )
        return  # If BRIEFCASE_DEBUGGER is not set, this packages does nothing...

    if verbose:
        print(f"'BRIEFCASE_DEBUGGER'={config_str}")

    # start debugger
    print("Starting remote debugger...")
    start_pdb(config_str, verbose)


# only start remote debugger on the first import
if not REMOTE_DEBUGGER_STARTED:
    try:
        start_remote_debugger()
    except Exception:
        # Show exception and stop the whole application when an error occurs
        print(traceback.format_exc())
        sys.exit(-1)
