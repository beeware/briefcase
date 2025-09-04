import importlib
import json
import os
import sys
from unittest.mock import MagicMock, call

import briefcase_debugger


def test_auto_startup(monkeypatch, capsys):
    """Debugger startup code is executed on import."""
    fake_environ = MagicMock()
    monkeypatch.setattr(os, "environ", fake_environ)

    fake_environ.get.return_value = None

    # reload the module to trigger the auto startup code
    importlib.reload(importlib.import_module("briefcase_debugger"))

    # check if the autostart was executed
    assert fake_environ.get.mock_calls == [
        call("BRIEFCASE_DEBUG", "0"),
        call("BRIEFCASE_DEBUGGER", None),
    ]


def test_unknown_debugger(monkeypatch, capsys):
    """An unknown debugger raises an error and stops the application."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "unknown",
            "host": "somehost",
            "port": 9999,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    fake_sys_exit = MagicMock()
    monkeypatch.setattr(sys, "exit", fake_sys_exit)

    briefcase_debugger.start_remote_debugger()

    fake_sys_exit.assert_called_once_with(-1)

    captured = capsys.readouterr()
    assert "Unknown debugger" in captured.out
