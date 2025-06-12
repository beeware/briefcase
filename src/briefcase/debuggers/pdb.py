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
            dependencies=[],
        )

        debugger_support = dir / "briefcase_debugger_support.py"
        debugger_support.write_text('''
import json
import os
import platform
import re
import socket
import sys
import traceback

REMOTE_DEBUGGER_STARTED = False

NEWLINE_REGEX = re.compile("\\r?\\n")

class SocketFileWrapper(object):
    def __init__(self, connection: socket.socket):
        self.connection = connection
        self.stream = connection.makefile('rw')

        self.read = self.stream.read
        self.readline = self.stream.readline
        self.readlines = self.stream.readlines
        self.close = self.stream.close
        self.isatty = self.stream.isatty
        self.flush = self.stream.flush
        self.fileno = lambda: -1
        self.__iter__ = self.stream.__iter__

    @property
    def encoding(self):
        return self.stream.encoding

    def write(self, data):
        data = NEWLINE_REGEX.sub("\\r\\n", data)
        self.connection.sendall(data.encode(self.stream.encoding))

    def writelines(self, lines):
        for line in lines:
            self.write(line)

def _start_pdb(config_str: str, verbose: bool):
    """Open a socket server and stream all stdio via the connection bidirectional."""
    debugger_config: dict = json.loads(config_str)

    # Parsing host/port
    host = debugger_config["host"]
    port = debugger_config["port"]

    print(
        f"""
Stdio redirector server opened at {host}:{port}, waiting for connection...
To connect to stdio redirector use eg.:
    - telnet {host} {port}
    - nc -C {host} {port}
    - socat readline tcp:{host}:{port}
"""
    )

    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    listen_socket.bind((host, port))
    listen_socket.listen(1)
    connection, address = listen_socket.accept()
    print(f"Stdio redirector accepted connection from {{repr(address)}}.")

    file_wrapper = SocketFileWrapper(connection)

    sys.stderr = file_wrapper
    sys.stdout = file_wrapper
    sys.stdin = file_wrapper
    sys.__stderr__ = file_wrapper
    sys.__stdout__ = file_wrapper
    sys.__stdin__ = file_wrapper


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
            print("No 'BRIEFCASE_DEBUGGER' environment variable found. Debugger not starting.")
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
