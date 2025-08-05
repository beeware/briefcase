from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from briefcase.debuggers import (
    DebugpyDebugger,
    PdbDebugger,
    get_debugger,
    get_debuggers,
)
from briefcase.debuggers.base import DebuggerConnectionMode
from briefcase.exceptions import BriefcaseCommandError


def test_get_debuggers():
    debuggers = get_debuggers()
    assert isinstance(debuggers, dict)
    assert debuggers["pdb"] is PdbDebugger
    assert debuggers["debugpy"] is DebugpyDebugger


def test_get_debugger():
    assert isinstance(get_debugger("pdb"), PdbDebugger)
    assert isinstance(get_debugger("debugpy"), DebugpyDebugger)

    # Test with an unknown debugger name
    try:
        get_debugger("unknown")
    except BriefcaseCommandError as e:
        assert str(e) == "Unknown debugger: unknown"


@pytest.mark.parametrize(
    "debugger_name, expected_class, connection_mode",
    [
        (
            "pdb",
            PdbDebugger,
            DebuggerConnectionMode.SERVER,
        ),
        (
            "debugpy",
            DebugpyDebugger,
            DebuggerConnectionMode.SERVER,
        ),
    ],
)
def test_debugger(debugger_name, expected_class, connection_mode):
    debugger = get_debugger(debugger_name)
    assert isinstance(debugger, expected_class)
    assert debugger.connection_mode == connection_mode
    assert (
        f"briefcase-{debugger_name}-debugger-support" in debugger.debugger_support_pkg
    )


@pytest.mark.parametrize(
    "debugger_name",
    ["pdb", "debugpy"],
)
def test_debugger_editable(debugger_name, monkeypatch):
    with TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        (
            tmp_path
            / "debugger-support"
            / f"briefcase-{debugger_name}-debugger-support"
        ).mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("briefcase.utils.IS_EDITABLE", True)
        monkeypatch.setattr("briefcase.utils.REPO_ROOT", tmp_path)

        debugger = get_debugger(debugger_name)
        assert (
            f"{tmp_path}/debugger-support/briefcase-{debugger_name}-debugger-support"
            == debugger.debugger_support_pkg
        )


@pytest.mark.parametrize(
    "debugger_name",
    ["pdb", "debugpy"],
)
def test_debugger_editable_path_not_found(debugger_name, monkeypatch):
    with TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        monkeypatch.setattr("briefcase.utils.IS_EDITABLE", True)
        monkeypatch.setattr("briefcase.utils.REPO_ROOT", tmp_path)

        debugger = get_debugger(debugger_name)
        assert (
            f"briefcase-{debugger_name}-debugger-support=="
            in debugger.debugger_support_pkg
        )
