from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode


class DebugpyDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        return [
            "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-debugpy-debugadapter"
        ]

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER
