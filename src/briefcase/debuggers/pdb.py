import briefcase
import briefcase.utils
from briefcase.debuggers.base import BaseDebugger, DebuggerConnectionMode


class PdbDebugger(BaseDebugger):
    """Definition for a plugin that defines a new Briefcase debugger."""

    @property
    def connection_mode(self) -> DebuggerConnectionMode:
        """Return the connection mode of the debugger."""
        return DebuggerConnectionMode.SERVER

    @property
    def debugger_support_pkg(self) -> str:
        """Get the name of the debugger support package."""
        if briefcase.utils.IS_EDITABLE and briefcase.utils.REPO_ROOT is not None:
            local_path = (
                briefcase.utils.REPO_ROOT
                / "debugger-support"
                / "briefcase-pdb-debugger-support"
            )
            if local_path.exists() and local_path.is_dir():
                return str(local_path)

        return f"briefcase-pdb-debugger-support=={briefcase.__version__}"
