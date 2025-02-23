import dataclasses
import enum
import textwrap
from datetime import datetime
from pathlib import Path
from typing import TextIO

from briefcase.config import AppConfig


class Debugger(enum.StrEnum):
    PDB = "pdb"
    DEBUGPY = "debugpy"


class DebuggerMode(enum.StrEnum):
    SERVER = "server"
    CLIENT = "client"


_DEBGGER_REQUIREMENTS_MAPPING = {
    Debugger.PDB: [],
    Debugger.DEBUGPY: ["debugpy~=1.8.12"],
}


@dataclasses.dataclass
class DebuggerConfig:
    debugger: Debugger
    debugger_mode: DebuggerMode
    ip: str
    port: int

    @property
    def additional_requirements(self) -> list[str]:
        return _DEBGGER_REQUIREMENTS_MAPPING[self.debugger]

    @staticmethod
    def from_app(app: AppConfig) -> "DebuggerConfig":
        debugger = app.debugger or Debugger.PDB
        debugger_mode = app.debugger_mode or DebuggerMode.SERVER
        debugger_ip = app.debugger_ip or "localhost"
        debugger_port = app.debugger_port or 5678

        try:
            debugger = Debugger(debugger)
        except Exception:
            raise ValueError("debugger has a wrong value")

        try:
            debugger_port = int(debugger_port)
        except Exception:
            raise ValueError("debugger_port has to be an integer")

        return DebuggerConfig(
            debugger,
            debugger_mode,
            debugger_ip,
            debugger_port,
        )


def write_debugger_startup_file(
    app_path: Path,
    pth_folder_path: Path | None,
    app: AppConfig,
    path_mappings: str,
):
    debugger_cfg = DebuggerConfig.from_app(app)

    startup_modul = "__briefcase_startup__"
    startup_code_path = app_path / f"{startup_modul}.py"

    if debugger_cfg.debugger == Debugger.PDB:
        if debugger_cfg.debugger_mode != DebuggerMode.SERVER:
            raise ValueError(
                f"{debugger_cfg.debugger_mode} not supported by {debugger_cfg.debugger}"
            )

        with startup_code_path.open("w", encoding="utf-8") as f:
            create_remote_pdb_startup_file(
                f,
                debugger_cfg,
            )
    elif debugger_cfg.debugger == Debugger.DEBUGPY:
        if debugger_cfg.debugger_mode not in (DebuggerMode.SERVER, DebuggerMode.CLIENT):
            raise ValueError(
                f"{debugger_cfg.debugger_mode} not supported by {debugger_cfg.debugger}"
            )

        with startup_code_path.open("w", encoding="utf-8") as f:
            create_debugpy_startup_file(
                f,
                debugger_cfg,
                path_mappings,
            )
    else:
        raise ValueError(f"debugger '{debugger_cfg.debugger}' not found")

    if pth_folder_path:
        startup_pth_path = pth_folder_path / f"{startup_modul}.pth"
        with startup_pth_path.open("w", encoding="utf-8") as f:
            f.write(f"import {startup_modul}")


def create_remote_pdb_startup_file(
    file: TextIO,
    debugger_cfg: DebuggerConfig,
) -> str:
    file.write(
        f"""
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
    ip = "{debugger_cfg.ip}"
    port = {debugger_cfg.port}
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


def create_debugpy_startup_file(
    file: TextIO,
    debugger_cfg: DebuggerConfig,
    path_mappings: str,
) -> str:
    """Create the code that is necessary to start the debugger"""
    file.write(
        f"""
# Generated {datetime.now()}

import os
import sys
from pathlib import Path

def start_debugger():
    ip = "{debugger_cfg.ip}"
    port = {debugger_cfg.port}
    path_mappings = []
    {textwrap.indent(path_mappings, "    ")}

    # When an app is bundled with briefcase "os.__file__" is not set at runtime
    # on some platforms (eg. windows). But debugpy accesses it internally, so it
    # has to be set or an Exception is raised from debugpy.
    if not hasattr(os, "__file__"):
        os.__file__ = ""

"""
    )
    if debugger_cfg.debugger_mode == DebuggerMode.CLIENT:
        file.write(
            """
    print(f'''
Connecting to debugpy server at {ip}:{port}...
To create the debugpy server using VSCode add the following configuration to launch.json and start the debugger:
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Briefcase: Attach (Listen)",
            "type": "debugpy",
            "request": "attach",
            "listen": {{
                "host": "{ip}",
                "port": {port}
            }}
        }}
    ]
}}
''')
    import debugpy
    try:
        debugpy.connect((ip, port))
    except ConnectionRefusedError as e:
        print("Could not connect to debugpy server. Is it already started? We continue with the app...")
        return
"""
        )
    elif debugger_cfg.debugger_mode == DebuggerMode.SERVER:
        file.write(
            """
    print(f'''
The debugpy server started at {ip}:{port}, waiting for connection...
To connect to debugpy using VSCode add the following configuration to launch.json:
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Briefcase: Attach (Connect)",
            "type": "debugpy",
            "request": "attach",
            "connect": {{
                "host": "{ip}",
                "port": {port}
            }}
        }}
    ]
}}
''')
    import debugpy
    debugpy.listen((ip, port), in_process_debug_adapter=True)
"""
        )

    file.write(
        """
    if (len(path_mappings) > 0):
        # path_mappings has to be applied after connection is established. If no connection is
        # established this import will fail.
        import pydevd_file_utils

        pydevd_file_utils.setup_client_server_paths(path_mappings)

start_debugger()
"""
    )
