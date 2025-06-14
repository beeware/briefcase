from pathlib import Path

from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode


class PdbDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER

    def create_debugger_support_pkg(self, dir: Path) -> None:
        """Create the support package for the debugger.
        This package will be installed inside the packaged app bundle.

        :param dir: Directory where the support package should be created.
        """
        self._create_debugger_support_pkg_base(
            dir,
            dependencies=["remote-pdb>=2.1.0,<3.0.0"],
        )

        debugger_support = dir / "briefcase_debugger_support.py"
        debugger_support.write_text('''
import json
import os
import sys
import traceback
from remote_pdb import RemotePdb

REMOTE_DEBUGGER_STARTED = False


def _start_pdb(config_str: str, verbose: bool):
    """Start remote PDB server."""
    debugger_config: dict = json.loads(config_str)

    # Parsing host/port
    host = debugger_config["host"]
    port = debugger_config["port"]

    print(
        f"""
Remote PDB server opened at {host}:{port}, waiting for connection...
To connect to remote PDB use eg.:
    - telnet {host} {port} (Windows)
    - rlwrap socat - tcp:{host}:{port} (Linux, macOS)
"""
    )

    # Create a RemotePdb instance
    remote_pdb = RemotePdb(host, port, quiet=True)

    # Connect the remote PDB with the "breakpoint()" function
    sys.breakpointhook = remote_pdb.set_trace

    print("Debugger client attached.")


def start_remote_debugger():
    global REMOTE_DEBUGGER_STARTED
    REMOTE_DEBUGGER_STARTED = True

    # check verbose output
    verbose = True if os.environ.get("BRIEFCASE_DEBUG", "0") == "1" else False

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
    _start_pdb(config_str, verbose)


def autostart_remote_debugger():
    try:
        start_remote_debugger()
    except Exception:
        # Show exception and stop the whole application when an error occurs
        print(traceback.format_exc())
        sys.exit(-1)


# only start remote debugger on the first import
if REMOTE_DEBUGGER_STARTED == False:
    autostart_remote_debugger()
''')
