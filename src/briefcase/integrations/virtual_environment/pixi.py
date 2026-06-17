import os
import shutil
import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class PixiVirtualEnvironment(VirtualEnvironment):
    """An environment manager using pixi.

    A pixi *workspace* is created at the requested path (``pixi init``), with a
    Python dependency added that matches the major/minor version of the
    interpreter running Briefcase. Pixi materialises the actual environment in
    a ``.pixi/envs/default`` directory inside the workspace, so the binary
    directory and Python executable are resolved relative to that location.
    Commands are executed against the environment by prepending that binary
    directory to ``PATH``.
    """

    @property
    def python_version(self) -> str:
        """The ``major.minor`` Python version to request from pixi."""
        return f"{sys.version_info.major}.{sys.version_info.minor}"

    @property
    def env_path(self) -> Path:
        """The path to the materialised default pixi environment."""
        return self.venv_path / ".pixi" / "envs" / "default"

    @property
    def bin_dir(self) -> Path:
        """The default environment's binary directory.

        On Windows, executables live directly in the environment directory; on
        POSIX, they live in a `bin` subdirectory.
        """
        return self.env_path if os.name == "nt" else self.env_path / "bin"

    def exists(self) -> bool:
        """`True` iff the pixi workspace manifest and the default environment are
        present."""
        manifest = self.venv_path / "pixi.toml"
        return manifest.exists() and self.env_path.exists()

    def prepare(self, recreate=False) -> bool:
        """Prepare a pixi workspace at the given path.

        If the workspace does not already exist, or a recreate has been
        requested, create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if environment creation fails.
        """
        creating = "Creating"
        if self.exists():
            if recreate:
                creating = "Recreating"
            else:
                return False

        with self.tools.console.wait_bar(
            f"{creating} virtual environment ({self.venv_path.name})..."
        ):
            if recreate:
                self.clean()

            try:
                self.venv_path.mkdir(parents=True, exist_ok=True)
                self.tools.subprocess.run(
                    [
                        "pixi",
                        "init",
                        self.venv_path,
                    ],
                    check=True,
                )
                self.tools.subprocess.run(
                    [
                        "pixi",
                        "add",
                        "--manifest-path",
                        self.venv_path,
                        f"python=={self.python_version}",
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Failed to create virtual environment at {self.venv_path}"
                ) from e

        return True

    def clean(self) -> None:
        """Remove the pixi workspace directory tree if it exists."""
        if self.venv_path.exists():
            shutil.rmtree(self.venv_path)

    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Replace the head argument with the environment's Python iff it equals
        `sys.executable` (case-insensitive, normalised).

        Empty inputs are returned unchanged. Otherwise a fresh `list` is
        returned; the input is never mutated.
        """
        if not args:
            return args
        head = os.fspath(args[0])
        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return [self.executable, *args[1:]]
        return list(args)

    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str]:
        """Build a subprocess environment that activates the pixi environment.

        Prepends the environment's `bin_dir` to `PATH`, sets `CONDA_PREFIX` to
        the materialised environment path, and removes `PYTHONHOME`.
        Caller-supplied overrides are honoured.

        :param overrides: Caller-supplied environment overrides.
        :returns: An updated environment applying modifications
            to enable the virtual environment
        """
        env = dict(overrides) if overrides else {}

        old_path = env.get("PATH") or os.environ.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["CONDA_PREFIX"] = os.fspath(self.env_path)
        env.pop("PYTHONHOME", None)

        return env
