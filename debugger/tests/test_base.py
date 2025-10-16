import importlib
import json
import os
import sys
from unittest.mock import MagicMock

import briefcase_debugger


def test_import_for_code_coverage(monkeypatch, capsys):
    """Get 100% code coverage."""
    # The module `briefcase_debugger` is already imported through the .pth
    # file. Code executed during .pth files are not covered by coverage.py.
    # So we need to reload the module to get a 100% code coverage.
    importlib.reload(importlib.import_module("briefcase_debugger"))


def test_unknown_debugger(monkeypatch, capsys):
    """An unknown debugger raises an error and stops the application."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "unknown",
            "host": "somehost",
            "port": 9999,
            "host_os": "Windows",
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    fake_sys_exit = MagicMock()
    monkeypatch.setattr(sys, "exit", fake_sys_exit)

    briefcase_debugger.start_remote_debugger()

    fake_sys_exit.assert_called_once_with(-1)

    captured = capsys.readouterr()
    assert "Unknown debugger" in captured.out
