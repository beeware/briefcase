import re
import sys
from pathlib import Path

import debugpy

from briefcase_debugger.config import DebuggerConfig


def find_first_matching_path(regex: str) -> str:
    """Returns the first element of sys.paths that matches regex, otherwise None."""
    for path in sys.path:
        if re.search(regex, path):
            return path
    raise ValueError(f"No sys.path entry matches regex '{regex}'")


def load_path_mappings(config: DebuggerConfig, verbose: bool) -> list[tuple[str, str]]:
    app_path_mappings = config.get("app_path_mappings", None)
    app_packages_path_mappings = config.get("app_packages_path_mappings", None)

    mappings_list = []
    if app_path_mappings:
        device_app_folder = find_first_matching_path(
            app_path_mappings["device_sys_path_regex"]
        )
        for app_subfolder_device, app_subfolder_host in zip(
            app_path_mappings["device_subfolders"],
            app_path_mappings["host_folders"],
            strict=False,
        ):
            mappings_list.append(
                (
                    app_subfolder_host,
                    str(Path(device_app_folder) / app_subfolder_device),
                )
            )
    if app_packages_path_mappings:
        device_app_packages_folder = find_first_matching_path(
            app_packages_path_mappings["sys_path_regex"]
        )
        mappings_list.append(
            (
                app_packages_path_mappings["host_folder"],
                str(Path(device_app_packages_folder)),
            )
        )

    if verbose:
        print("Extracted path mappings:")
        for idx, mapping in enumerate(mappings_list):
            print(f"[{idx}] host =   {mapping[0]}")
            print(f"[{idx}] device = {mapping[1]}")

    return mappings_list


def start_debugpy(config: DebuggerConfig, verbose: bool):
    host = config["host"]
    port = config["port"]
    path_mappings = load_path_mappings(config, verbose)

    # Starting remote debugger...
    print(f"Starting debugpy in server mode at {host}:{port}...")
    debugpy.listen((host, port), in_process_debug_adapter=True)

    if verbose:
        # pydevd is dynamically loaded and only available after debugpy is started
        import pydevd

        pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 3

    if len(path_mappings) > 0:
        if verbose:
            print("Adding path mappings...")

        # pydevd is dynamically loaded and only available after a debugger has connected
        import pydevd_file_utils

        pydevd_file_utils.setup_client_server_paths(path_mappings)

    print("The debugpy server started. Waiting for debugger to attach...")
    print(
        f"""
To connect to debugpy using VSCode add the following configuration to '.vscode/launch.json':
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
            }},
            "justMyCode": false
        }}
    ]
}}

For more information see: https://briefcase.readthedocs.io/en/stable/how-to/debugging/vscode.html#bundled-app
"""
    )
    debugpy.wait_for_client()

    print("Debugger attached.")
    print("-" * 75)
