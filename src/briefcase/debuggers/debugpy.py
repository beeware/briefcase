import briefcase
from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode


class DebugpyDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER

    @property
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package"""
        return f"briefcase-debugpy-debugger-support=={briefcase.__version__}"
