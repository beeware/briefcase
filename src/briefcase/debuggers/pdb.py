from briefcase.debuggers.base import BaseDebugger, DebuggerMode


class PdbDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    name = "pdb"

    @property
    def additional_requirements(self) -> list[str]:
        """Return a list of additional requirements for the debugger."""
        return [
            "git+https://github.com/timrid/briefcase-debugadapter#subdirectory=briefcase-pdb-debugadapter"
        ]

    @property
    def debugger_mode(self) -> DebuggerMode:
        """Return the mode of the debugger."""
        return DebuggerMode.SERVER
