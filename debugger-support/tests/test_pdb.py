import json
import os
from unittest.mock import MagicMock

import briefcase_debugger
import briefcase_debugger.pdb
import pytest


def test_no_env_vars(monkeypatch, capsys):
    """Test that nothing happens, when no env vars are set."""
    os_environ = {}
    monkeypatch.setattr(os, "environ", os_environ)

    # start test function
    briefcase_debugger.start_remote_debugger()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_no_debugger_verbose(monkeypatch, capsys):
    """Test that nothing happens except a short message, when only verbose is
    requested."""
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


@pytest.mark.parametrize("verbose", [True, False])
def test_with_debugger(monkeypatch, capsys, verbose):
    """Test a normal debug session."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1" if verbose else "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "pdb",
            "host": "somehost",
            "port": 9999,
        }
    )
    monkeypatch.setattr(os, "environ", os_environ)

    fake_remote_pdb = MagicMock()
    monkeypatch.setattr(briefcase_debugger.pdb, "RemotePdb", fake_remote_pdb)

    # start test function
    briefcase_debugger.start_remote_debugger()

    fake_remote_pdb.assert_called_once_with(
        "somehost",
        9999,
        quiet=True,
    )

    captured = capsys.readouterr()
    assert "Waiting for debugger to attach..." in captured.out
    assert captured.err == ""
