import json
import os
import sys
import traceback


def start_remote_debugger():
    try:
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

        # Parsing config json
        config = json.loads(config_str)

        # start debugger
        print("Starting remote debugger...")
        if config["debugger"] == "debugpy":
            from briefcase_debugger.debugpy import start_debugpy

            start_debugpy(config, verbose)
        elif config["debugger"] == "pdb":
            from briefcase_debugger.pdb import start_pdb

            start_pdb(config, verbose)
        else:
            raise ValueError(f"Unknown debugger '{config['debugger']}'")
    except Exception:
        # Show exception and stop the whole application when an error occurs
        print(traceback.format_exc())
        sys.exit(-1)
