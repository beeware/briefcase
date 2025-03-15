from datetime import datetime
from typing import TextIO

from briefcase.debuggers.base import BaseDebugger, DebuggerMode


class PdbDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    supported_modes = [DebuggerMode.SERVER]
    default_mode = DebuggerMode.SERVER

    def create_startup_file(self, file: TextIO, path_mappings: str) -> None:
        """Create the code that is necessary to start the debugger"""
        file.write(
            f"""\
# Generated {datetime.now()}

import socket
import sys
import re

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

def redirect_stdio():
    f'''Open a socket server and stream all stdio via the connection bidirectional.'''
    ip = "{self.ip}"
    port = {self.port}
    print(f'''
Stdio redirector server opened at {{ip}}:{{port}}, waiting for connection...
To connect to stdio redirector use eg.:
    - telnet {{ip}} {{port}}
    - nc -C {{ip}} {{port}}
    - socat readline tcp:{{ip}}:{{port}}
''')

    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    listen_socket.bind((ip, port))
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

redirect_stdio()
"""
        )
