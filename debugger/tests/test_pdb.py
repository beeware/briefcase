import json
import os
from unittest.mock import MagicMock

import briefcase_debugger
import briefcase_debugger.pdb
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
    expected_msg = (
        "No 'BRIEFCASE_DEBUGGER' environment variable found. "
        "Debugger not starting.\n"
    )
    assert captured.out == expected_msg
    assert captured.err == ""


@pytest.mark.parametrize("verbose", [True, False])
@pytest.mark.parametrize(
    ("host_os", "expected_host_cmds"),
    [
        ("Windows", ["telnet somehost 9999"]),
        ("Darwin", ["nc somehost 9999"]),
        ("Linux", ["nc somehost 9999"]),
        ("UnknownOS", ["nc somehost 9999", "telnet somehost 9999"]),
    ],
)
def test_with_debugger(monkeypatch, host_os, expected_host_cmds, capsys, verbose):
    """Normal debug session."""
    os_environ = {}
    os_environ["BRIEFCASE_DEBUG"] = "1" if verbose else "0"
    os_environ["BRIEFCASE_DEBUGGER"] = json.dumps(
        {
            "debugger": "pdb",
            "host": "somehost",
            "port": 9999,
            "host_os": host_os,
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
    for cmd in expected_host_cmds:
        assert cmd in captured.out
    assert captured.err == ""
