import sys

from remote_pdb import RemotePdb

from briefcase_debugger.config import DebuggerConfig


def start_pdb(config: DebuggerConfig, verbose: bool):
    """Start remote PDB server."""
    # Parsing host/port
    host = config["host"]
    port = config["port"]

    # Print help message
    host_os = config["host_os"]
    telnet_cmd = f"telnet {host} {port}"
    nc_cmd = f"nc {host} {port}"
    if host_os == "Windows":
        cmds_hint = f"    {telnet_cmd}"
    elif host_os in ("Linux", "Darwin"):
        cmds_hint = f"    {nc_cmd}"
    else:
        cmds_hint = f"""\
 - {telnet_cmd}
 - {nc_cmd}
"""
    print(f"""
Remote PDB server opened at {host}:{port}.
Waiting for debugger to attach...
To connect to remote PDB use for example:

{cmds_hint}

For more information see: https://briefcase.readthedocs.io/en/stable/how-to/debugging/console.html#bundled-app
""")

    # Create a RemotePdb instance
    remote_pdb = RemotePdb(host, port, quiet=True)

    # Connect the remote PDB with the "breakpoint()" function
    sys.breakpointhook = remote_pdb.set_trace

    print("Debugger client attached.")
    print("-" * 75)
