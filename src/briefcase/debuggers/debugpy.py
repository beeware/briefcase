import textwrap

from briefcase.debuggers.base import BaseDebugger, DebuggerMode


class DebugpyDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    supported_modes = [DebuggerMode.SERVER, DebuggerMode.CLIENT]
    default_mode = DebuggerMode.SERVER

    @property
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        return ["debugpy~=1.8.12"]

    def generate_startup_code(self, path_mappings: str) -> str:
        """
        Generate the code that is necessary to start the debugger.

        :param path_mappings: The path mappings that should be used in the startup file.
        """
        code = f"""\
import os
import sys
from pathlib import Path

def start_remote_debugger():
    ip = "{self.ip}"
    port = {self.port}
    path_mappings = []
    {textwrap.indent(path_mappings, "    ")}

    # When an app is bundled with briefcase "os.__file__" is not set at runtime
    # on some platforms (eg. windows). But debugpy accesses it internally, so it
    # has to be set or an Exception is raised from debugpy.
    if not hasattr(os, "__file__"):
        os.__file__ = ""

"""
        if self.mode == DebuggerMode.CLIENT:
            code += """\
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
        elif self.mode == DebuggerMode.SERVER:
            code += """\
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

        code += """\
    if (len(path_mappings) > 0):
        # path_mappings has to be applied after connection is established. If no connection is
        # established this import will fail.
        import pydevd_file_utils

        pydevd_file_utils.setup_client_server_paths(path_mappings)
"""
        return code
