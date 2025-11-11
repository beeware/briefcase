from importlib.metadata import entry_points

from briefcase.debuggers.base import BaseDebugger
from briefcase.debuggers.debugpy import DebugpyDebugger  # noqa: F401
from briefcase.debuggers.pdb import PdbDebugger  # noqa: F401
from briefcase.exceptions import BriefcaseCommandError


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
