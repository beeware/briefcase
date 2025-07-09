import briefcase
from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode
from briefcase.utils import IS_EDITABLE, REPO_ROOT


class DebugpyDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER

    @property
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package"""
        if IS_EDITABLE and REPO_ROOT is not None:
            local_path = (
                REPO_ROOT / "debugger-support/briefcase-debugpy-debugger-support"
            )
            if local_path.exists() and local_path.is_dir():
                return str(local_path)

        return f"briefcase-debugpy-debugger-support=={briefcase.__version__}"
