import json
from importlib import metadata
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from briefcase.debuggers import (
    DebugpyDebugger,
    PdbDebugger,
    get_debugger,
    get_debuggers,
)
from briefcase.debuggers.base import DebuggerConnectionMode, _is_editable_pep610
from briefcase.exceptions import BriefcaseCommandError


class DummyDist:
    def __init__(self, direct_url):
        self._direct_url = direct_url

    def read_text(self, name):
        return self._direct_url if name == "direct_url.json" else None


@pytest.mark.parametrize(
    "direct_url,is_editable",
    [
        (json.dumps({"dir_info": {"editable": True}}), True),  # editable
        (json.dumps({"dir_info": {"editable": False}}), False),  # not editable
        (json.dumps({}), False),  # missing dir_info
        (None, False),  # missing direct_url.json
        ("not-json", False),  # invalid JSON
    ],
)
def test_is_editable_pep610(monkeypatch, direct_url, is_editable):
    """Detection of editable installs via PEP 610 direct_url.json works."""
    monkeypatch.setattr(metadata, "distribution", lambda name: DummyDist(direct_url))
    assert _is_editable_pep610("briefcase") is is_editable


def test_is_editable_pep610_package_not_found(monkeypatch):
    """Detection of editable install throws an Error if package is not found."""

    def raise_not_found(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(metadata, "distribution", raise_not_found)
    with pytest.raises(metadata.PackageNotFoundError):
        _is_editable_pep610("briefcase")


def test_get_debuggers():
    """Builtin debuggers are available."""
    debuggers = get_debuggers()
    assert isinstance(debuggers, dict)
    assert debuggers["pdb"] is PdbDebugger
    assert debuggers["pdb"]().name == "pdb"
    assert debuggers["debugpy"] is DebugpyDebugger
    assert debuggers["debugpy"]().name == "debugpy"


def test_get_debugger():
    """Debugger can be retrieved by name."""
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
def test_debugger(debugger_name, expected_class, connection_mode, monkeypatch):
    """Debugger uses correct connection mode and support package."""
    monkeypatch.setattr("briefcase.debuggers.base.IS_EDITABLE", False)

    debugger = get_debugger(debugger_name)
    assert isinstance(debugger, expected_class)
    assert debugger.connection_mode == connection_mode
    assert f"briefcase-debugger[{debugger_name}]" in debugger.debugger_support_pkg


@pytest.mark.parametrize(
    "debugger_name",
    ["pdb", "debugpy"],
)
def test_debugger_editable(debugger_name, monkeypatch):
    """Debugger support package is local path in editable briefcase install."""
    with TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        (tmp_path / "debugger-support" / f"briefcase-{debugger_name}").mkdir(
            parents=True, exist_ok=True
        )
        monkeypatch.setattr("briefcase.debuggers.base.IS_EDITABLE", True)
        monkeypatch.setattr("briefcase.debuggers.base.REPO_ROOT", tmp_path)

        debugger = get_debugger(debugger_name)
        assert (
            str(tmp_path / f"debugger-support[{debugger_name}]")
            == debugger.debugger_support_pkg
        )


@pytest.mark.parametrize(
    "debugger_name",
    ["pdb", "debugpy"],
)
def test_debugger_editable_path_not_found(debugger_name, monkeypatch):
    """Debugger support package is not the local path when path is not available."""
    with TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        monkeypatch.setattr("briefcase.debuggers.base.IS_EDITABLE", True)
        monkeypatch.setattr("briefcase.debuggers.base.REPO_ROOT", tmp_path)

        debugger = get_debugger(debugger_name)
        assert f"briefcase-debugger[{debugger_name}]==" in debugger.debugger_support_pkg
