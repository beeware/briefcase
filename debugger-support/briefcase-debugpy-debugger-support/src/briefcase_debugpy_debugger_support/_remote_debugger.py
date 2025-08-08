import json
import os
import re
import sys
from pathlib import Path
from typing import TypedDict

import debugpy


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


def _load_path_mappings(config: DebuggerConfig, verbose: bool) -> list[tuple[str, str]]:
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


def start_debugpy(config_str: str, verbose: bool):
    # Parsing config json
    debugger_config: dict = json.loads(config_str)

    host = debugger_config["host"]
    port = debugger_config["port"]
    path_mappings = _load_path_mappings(debugger_config, verbose)

    # There is a bug in debugpy that has to be handled until there is a new
    # debugpy release, see https://github.com/microsoft/debugpy/issues/1943
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

        # pydevd is dynamically loaded and only available after a debugger has connected
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
    print("-" * 75)
