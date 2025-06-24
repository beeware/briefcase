import json
import sys

from remote_pdb import RemotePdb


def start_pdb(config_str: str, verbose: bool):
    """Start remote PDB server."""
    debugger_config: dict = json.loads(config_str)

    # Parsing host/port
    host = debugger_config["host"]
    port = debugger_config["port"]

    print(
        f"""
Remote PDB server opened at {host}:{port}.
Waiting for debugger to attach...
To connect to remote PDB use eg.:
    - telnet {host} {port} (Windows)
    - rlwrap socat - tcp:{host}:{port} (Linux, macOS)

For more information see: https://briefcase.readthedocs.io/en/stable/how-to/debugging/console.html#bundled-app
"""
    )

    # Create a RemotePdb instance
    remote_pdb = RemotePdb(host, port, quiet=True)

    # Connect the remote PDB with the "breakpoint()" function
    sys.breakpointhook = remote_pdb.set_trace

    print("Debugger client attached.")
    print("-" * 75)
