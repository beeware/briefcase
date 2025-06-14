from pathlib import Path

from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode


class DebugpyDebugger(BaseDebugger):
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
            dependencies=["debugpy>=1.8.14,<2.0.0"],
        )

        debugger_support = dir / "briefcase_debugger_support.py"
        debugger_support.write_text(
            '''\
import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import List, Optional, Tuple, TypedDict

import debugpy

REMOTE_DEBUGGER_STARTED = False

class AppPathMappings(TypedDict):
    device_sys_path_regex: str
    device_subfolders: list[str]
    host_folders: list[str]


class AppPackagesPathMappings(TypedDict):
    sys_path_regex: str
    host_folder: str


class DebuggerConfig(TypedDict):
    host: str
    port: int
    app_path_mappings: AppPathMappings | None
    app_packages_path_mappings: AppPackagesPathMappings | None


def _load_path_mappings(config: DebuggerConfig, verbose: bool) -> List[Tuple[str, str]]:
    app_path_mappings = config.get("app_path_mappings", None)
    app_packages_path_mappings = config.get("app_packages_path_mappings", None)

    mappings_list = []
    if app_path_mappings:
        device_app_folder = next(
            (
                p
                for p in sys.path
                if re.search(app_path_mappings["device_sys_path_regex"], p)
            ),
            None,
        )
        if device_app_folder:
            for app_subfolder_device, app_subfolder_host in zip(
                app_path_mappings["device_subfolders"],
                app_path_mappings["host_folders"],
            ):
                mappings_list.append(
                    (
                        app_subfolder_host,
                        str(Path(device_app_folder) / app_subfolder_device),
                    )
                )
    if app_packages_path_mappings:
        device_app_packages_folder = next(
            (
                p
                for p in sys.path
                if re.search(app_packages_path_mappings["sys_path_regex"], p)
            ),
            None,
        )
        if device_app_packages_folder:
            mappings_list.append(
                (
                    app_packages_path_mappings["host_folder"],
                    str(Path(device_app_packages_folder)),
                )
            )

    if verbose:
        print("Extracted path mappings:")
        for idx, p in enumerate(mappings_list):
            print(f"[{idx}] host =   {p[0]}")
            print(f"[{idx}] device = {p[1]}")

    return mappings_list


def _start_debugpy(config_str: str, verbose: bool):
    # Parsing config json
    debugger_config: dict = json.loads(config_str)

    host = debugger_config["host"]
    port = debugger_config["port"]
    path_mappings = _load_path_mappings(debugger_config, verbose)

    # When an app is bundled with briefcase "os.__file__" is not set at runtime
    # on some platforms (eg. windows). But debugpy accesses it internally, so it
    # has to be set or an Exception is raised from debugpy.
    if not hasattr(os, "__file__"):
        if verbose:
            print("'os.__file__' not available. Patching it...")
        os.__file__ = ""

    # Starting remote debugger...
    print(f"Starting debugpy in server mode at {host}:{port}...")
    debugpy.listen((host, port), in_process_debug_adapter=True)

    if len(path_mappings) > 0:
        if verbose:
            print("Adding path mappings...")

        import pydevd_file_utils

        pydevd_file_utils.setup_client_server_paths(path_mappings)

    print("The debugpy server started. Waiting for debugger to attach...")
    print(
        f"""
To connect to debugpy using VSCode add the following configuration to launch.json:
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Briefcase: Attach (Connect)",
            "type": "debugpy",
            "request": "attach",
            "connect": {{
                "host": "{host}",
                "port": {port}
            }}
        }}
    ]
}}
"""
    )
    debugpy.wait_for_client()

    print("Debugger attached.")


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
    _start_debugpy(config_str, verbose)


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
'''
        )
