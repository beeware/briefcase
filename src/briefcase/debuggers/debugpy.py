from briefcase.debuggers.base import (
    BaseDebugger,
    DebuggerConnectionMode,
    get_debugger_requirement,
)


class DebugpyDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def name(self) -> str:
        """Return the name debugger."""
        return "debugpy"

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER

    @property
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package."""
        return get_debugger_requirement("briefcase-debugger", "[debugpy]")
