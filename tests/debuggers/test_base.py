import py_compile
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib

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

    with TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        debugger.create_debugger_support_pkg(tmp_path)

        # Try to parse pyproject.toml to check for toml-format errors
        with (tmp_path / "pyproject.toml").open("rb") as f:
            tomllib.load(f)

        # try to compile to check existence and for syntax errors
        assert py_compile.compile(tmp_path / "setup.py") is not None
        assert (
            py_compile.compile(tmp_path / "briefcase_debugger_support" / "__init__.py")
            is not None
        )
        assert (
            py_compile.compile(
                tmp_path / "briefcase_debugger_support" / "_remote_debugger.py"
            )
            is not None
        )
