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


def test_pdb():
    debugger = PdbDebugger()
    debugger.additional_requirements == [
        "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-pdb-debugadapter"
    ]
    debugger.connection_mode == DebuggerConnectionMode.SERVER


def test_debugpy():
    debugger = DebugpyDebugger()
    debugger.additional_requirements == [
        "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-debugpy-debugadapter"
    ]
    debugger.connection_mode == DebuggerConnectionMode.SERVER
