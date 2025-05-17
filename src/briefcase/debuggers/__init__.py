import sys

from briefcase.exceptions import BriefcaseCommandError

if sys.version_info >= (3, 10):  # pragma: no-cover-if-lt-py310
    from importlib.metadata import entry_points
else:  # pragma: no-cover-if-gte-py310
    # Before Python 3.10, entry_points did not support the group argument;
    # so, the backport package must be used on older versions.
    from importlib_metadata import entry_points

from briefcase.debuggers.base import BaseDebugger
from briefcase.debuggers.debugpy import DebugpyDebugger  # noqa: F401
from briefcase.debuggers.pdb import PdbDebugger  # noqa: F401


def get_debuggers() -> dict[str, type[BaseDebugger]]:
    """Loads built-in and third-party debuggers."""
    return {
        entry_point.name: entry_point.load()
        for entry_point in entry_points(group="briefcase.debuggers")
    }


def get_debugger(name: str) -> BaseDebugger:
    """Get a debugger by name."""
    debuggers = get_debuggers()
    if name not in debuggers:
        raise BriefcaseCommandError(f"Unknown debugger: {name}")
    return debuggers[name]()
