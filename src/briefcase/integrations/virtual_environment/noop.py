import sys
from pathlib import Path

from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class NoOpVirtualEnvironment(VirtualEnvironment):
    """An environment manager for running in the ambient Python interpreter.

    No real virtual environment is created. Instead a small marker file is
    used to detect "first use" and interpreter changes, so callers can decide
    whether one-shot work (e.g., requirements installation) needs to run.

    Subprocess invocations forward `args` and `env` unchanged so the
    ambient process environment is preserved.
    """

    env_type: str = "noop"

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify that the environment manager is available."""
        # No-op environment management is available in the standard library.

    @property
    def marker_path(self) -> Path:
        return self.venv_path / "venv_path"

    @property
    def executable(self) -> Path:
        """The active interpreter (`sys.executable`)."""
        return Path(sys.executable)

    @property
    def bin_dir(self) -> Path:
        """The directory containing the active interpreter."""
        return Path(sys.executable).parent

    def exists(self) -> bool:
        """Always `True` — the ambient interpreter is always present."""
        return True

    def prepare(self, recreate=False) -> bool:
        """Prepare a venv at the given environment.

        If the venv does not already exist, or a recreate has been requested, create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if venv creation or pip upgrade fails.
        """
        self.marker_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = self.marker_path.read_text(encoding="utf-8").strip()
            if existing != sys.executable or recreate:
                self.marker_path.write_text(sys.executable, encoding="utf-8")
                created = True
            else:
                created = False
        except (OSError, UnicodeDecodeError):
            self.marker_path.write_text(sys.executable, encoding="utf-8")
            return True

        return created

    def clean(self) -> None:
        """Unlink the marker file if present."""
        if self.marker_path.exists():
            self.marker_path.unlink()

    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Return `args` as-is."""
        return args

    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str | None] | None:
        """Forward `overrides` unchanged."""
        return overrides
