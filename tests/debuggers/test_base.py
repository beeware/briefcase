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
    "debugger_name, expected_class, additional_requirements, connection_mode",
    [
        (
            "pdb",
            PdbDebugger,
            [
                "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-pdb-debugadapter"
            ],
            DebuggerConnectionMode.SERVER,
        ),
        (
            "debugpy",
            DebugpyDebugger,
            [
                "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-debugpy-debugadapter"
            ],
            DebuggerConnectionMode.SERVER,
        ),
    ],
)
def test_debugger(
    debugger_name, expected_class, additional_requirements, connection_mode
):
    debugger = get_debugger(debugger_name)
    assert isinstance(debugger, expected_class)
    assert debugger.additional_requirements == additional_requirements
    assert debugger.connection_mode == connection_mode
