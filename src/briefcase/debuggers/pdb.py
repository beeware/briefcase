from briefcase.debuggers.base import BaseDebugger, DebuggerMode


class PdbDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    name = "pdb"
    supported_modes = [DebuggerMode.SERVER]
    default_mode = DebuggerMode.SERVER

    @property
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        return ["git+https://github.com/timrid/briefcase-remote-debugger@main"]
