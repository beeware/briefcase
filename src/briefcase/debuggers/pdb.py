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

        remote_debugger = dir / "briefcase_debugger_support" / "_remote_debugger.py"
        remote_debugger.write_text('''
import json
import sys

from remote_pdb import RemotePdb

def _start_remote_debugger(config_str: str, verbose: bool):
    """Start remote PDB server."""
    debugger_config: dict = json.loads(config_str)

    # Parsing host/port
    host = debugger_config["host"]
    port = debugger_config["port"]

    print(
        f"""
Remote PDB server opened at {host}:{port}, waiting for connection...
To connect to remote PDB use eg.:
    - telnet {host} {port} (Windows, Linux)
    - rlwrap socat - tcp:{host}:{port} (Linux, macOS)
"""
    )

    # Create a RemotePdb instance
    remote_pdb = RemotePdb(host, port, quiet=True)

    # Connect the remote PDB with the "breakpoint()" function
    sys.breakpointhook = remote_pdb.set_trace

    print("Debugger client attached.")
''')
