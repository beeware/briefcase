import json
import os
import sys
from pathlib import Path, PosixPath, PureWindowsPath
from unittest.mock import MagicMock

import briefcase_debugger
import debugpy
import pytest


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
    "verbose,some_verbose_output,pydevd_trace_level",
    [
        (True, "Extracted path mappings:\n[0] host =   src/helloworld", 3),
        (False, "", 0),
    ],
)
def test_with_debugger(
    verbose, some_verbose_output, pydevd_trace_level, monkeypatch, capsys
):
    """Normal debug session."""
    # When running tests on Linux/macOS, we have to switch to WindowsPath.
    if isinstance(Path(), PosixPath):
        monkeypatch.setattr(briefcase_debugger.debugpy, "Path", PureWindowsPath)

    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1" if verbose else "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "debugpy",
            "host": "somehost",
            "port": 9999,
            "app_path_mappings": {
                "device_sys_path_regex": "app$",
                "device_subfolders": ["helloworld"],
                "host_folders": ["src/helloworld"],
            },
            "app_packages_path_mappings": None,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    sys_path = [
        "build\\helloworld\\windows\\app\\src\\app",
    ]
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
        [
            ("src/helloworld", "build\\helloworld\\windows\\app\\src\\app\\helloworld"),
        ]
    )

    captured = capsys.readouterr()
    assert "Waiting for debugger to attach..." in captured.out
    assert captured.err == ""

    assert some_verbose_output in captured.out
    assert fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL == pydevd_trace_level


@pytest.mark.parametrize(
    "verbose,some_verbose_output,pydevd_trace_level",
    [
        (True, "'os.__file__' not available. Patching it...", 3),
        (False, "", 0),
    ],
)
def test_os_file_bugfix(
    verbose, some_verbose_output, pydevd_trace_level, monkeypatch, capsys
):
    """The os.__file__ bugfix has to be applied (see https://github.com/microsoft/debugpy/issues/1943)."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1" if verbose else "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "debugpy",
            "host": "somehost",
            "port": 9999,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    # Fake an environment in that "os.__file__" is not available
    monkeypatch.delattr(os, "__file__", raising=False)

    fake_debugpy_listen = MagicMock()
    monkeypatch.setattr(debugpy, "listen", fake_debugpy_listen)

    fake_debugpy_wait_for_client = MagicMock()
    monkeypatch.setattr(debugpy, "wait_for_client", fake_debugpy_wait_for_client)

    # pydevd is dynamically loaded and only available when a real debugger is attached. So
    # we fake the whole module, as otherwise the import in start_remote_debugger would fail
    fake_pydevd = MagicMock()
    monkeypatch.setitem(sys.modules, "pydevd", fake_pydevd)
    fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL = 0

    # start test function
    briefcase_debugger.start_remote_debugger()

    fake_debugpy_listen.assert_called_once_with(
        ("somehost", 9999),
        in_process_debug_adapter=True,
    )

    assert hasattr(os, "__file__")
    assert os.__file__ == ""

    captured = capsys.readouterr()
    assert "Waiting for debugger to attach..." in captured.out
    assert captured.err == ""

    assert some_verbose_output in captured.out
    assert fake_pydevd.DebugInfoHolder.DEBUG_TRACE_LEVEL == pydevd_trace_level
