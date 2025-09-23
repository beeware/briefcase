import json
import os
import sys
from unittest.mock import MagicMock

import briefcase_debugger
import debugpy
import pytest
from briefcase_debugger.config import AppPathMappings


def test_no_env_vars(monkeypatch, capsys):
    """Nothing happens, when no env vars are set."""
    os_environ = {}
    monkeypatch.setattr(os, "environ", os_environ)

    # start test function
    briefcase_debugger.start_remote_debugger()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_no_debugger_verbose(monkeypatch, capsys):
    """Nothing happens except a short message, when only verbose is requested."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1"
    monkeypatch.setattr(os, "environ", os_environ)

    # start test function
    briefcase_debugger.start_remote_debugger()

    captured = capsys.readouterr()
    assert (
        captured.out
        == "No 'BRIEFCASE_DEBUGGER' environment variable found. Debugger not starting.\n"
    )
    assert captured.err == ""


@pytest.mark.parametrize(
    "os_name,app_path_mappings,sys_path,expected_path_mappings",
    [
        (
            "nt",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["C:\\PROJECT_ROOT\\src\\helloworld"],
            ),
            ["C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app"],
            [
                (
                    "C:\\PROJECT_ROOT\\src\\helloworld",
                    "C:\\PROJECT_ROOT\\build\\helloworld\\windows\\app\\src\\app\\helloworld",
                )
            ],
        ),
        (
            "posix",
            AppPathMappings(
                device_sys_path_regex="app$",
                device_subfolders=["helloworld"],
                host_folders=["/PROJECT_ROOT/src/helloworld"],
            ),
            [
                "/PROJECT_ROOT/build/helloworld/macos/app/Hello World.app/Contents/Resources/app"
            ],
            [
                (
                    "/PROJECT_ROOT/src/helloworld",
                    "/PROJECT_ROOT/build/helloworld/macos/app/Hello World.app/Contents/Resources/app/helloworld",
                )
            ],
        ),
    ],
)
@pytest.mark.parametrize(
    "verbose,some_verbose_output,pydevd_trace_level",
    [
        (True, "Extracted path mappings:\n[0] host =   ", 3),
        (False, "", 0),
    ],
)
def test_with_debugger(
    os_name: str,
    app_path_mappings: AppPathMappings,
    sys_path: list[str],
    expected_path_mappings: list[tuple[str, str]],
    verbose: bool,
    some_verbose_output: str,
    pydevd_trace_level: int,
    monkeypatch,
    capsys,
):
    """Normal debug session."""
    if os.name != os_name:
        pytest.skip(f"Test only runs on {os_name} systems")

    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1" if verbose else "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "debugpy",
            "host": "somehost",
            "port": 9999,
            "host_os": "SomeOS",
            "app_path_mappings": app_path_mappings,
            "app_packages_path_mappings": None,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    monkeypatch.setattr(sys, "path", sys_path)

    fake_debugpy_listen = MagicMock()
    monkeypatch.setattr(debugpy, "listen", fake_debugpy_listen)

    fake_debugpy_wait_for_client = MagicMock()
    monkeypatch.setattr(debugpy, "wait_for_client", fake_debugpy_wait_for_client)

    # pydevd is dynamically loaded and only available when a real debugger is attached. So
    # we fake the whole module, as otherwise the import in start_remote_debugger would fail
    fake_pydevd = MagicMock()
    monkeypatch.setitem(sys.modules, "pydevd", fake_pydevd)
    fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 0
    fake_pydevd_file_utils = MagicMock()
    fake_pydevd_file_utils.setup_client_server_paths.return_value = None
    monkeypatch.setitem(sys.modules, "pydevd_file_utils", fake_pydevd_file_utils)

    # start test function
    briefcase_debugger.start_remote_debugger()

    fake_debugpy_listen.assert_called_once_with(
        ("somehost", 9999),
        in_process_debug_adapter=True,
    )

    fake_debugpy_wait_for_client.assert_called_once()
    fake_pydevd_file_utils.setup_client_server_paths.assert_called_once_with(
        expected_path_mappings
    )

    captured = capsys.readouterr()
    assert "Waiting for debugger to attach..." in captured.out
    assert captured.err == ""

    assert some_verbose_output in captured.out
    assert fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL == pydevd_trace_level


def test_with_debugger_without_path_mappings(monkeypatch, capsys):
    """Debug session without path mappings."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "debugpy",
            "host": "somehost",
            "port": 9999,
            "host_os": "SomeOS",
            "app_path_mappings": None,
            "app_packages_path_mappings": None,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    fake_debugpy_listen = MagicMock()
    monkeypatch.setattr(debugpy, "listen", fake_debugpy_listen)

    fake_debugpy_wait_for_client = MagicMock()
    monkeypatch.setattr(debugpy, "wait_for_client", fake_debugpy_wait_for_client)

    # pydevd is dynamically loaded and only available when a real debugger is attached. So
    # we fake the whole module, as otherwise the import in start_remote_debugger would fail
    fake_pydevd = MagicMock()
    monkeypatch.setitem(sys.modules, "pydevd", fake_pydevd)
    fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 0
    fake_pydevd_file_utils = MagicMock()
    fake_pydevd_file_utils.setup_client_server_paths.return_value = None
    monkeypatch.setitem(sys.modules, "pydevd_file_utils", fake_pydevd_file_utils)

    # start test function
    briefcase_debugger.start_remote_debugger()

    fake_debugpy_listen.assert_called_once_with(
        ("somehost", 9999),
        in_process_debug_adapter=True,
    )

    fake_debugpy_wait_for_client.assert_called_once()
    fake_pydevd_file_utils.setup_client_server_paths.assert_not_called()

    captured = capsys.readouterr()
    assert "Waiting for debugger to attach..." in captured.out
    assert captured.err == ""
