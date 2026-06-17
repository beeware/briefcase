import os
import shutil
import subprocess
import sys

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class CondaVirtualEnvironment(VirtualEnvironment):
    """An environment manager using conda.

    The environment is created as a prefix-based conda environment (``conda
    create --prefix <path>``). The Python interpreter installed into the
    environment matches the major/minor version of the interpreter running
    Briefcase. Commands are executed against the environment by activating it
    (prepending the environment's binary directory to ``PATH``) rather than by
    wrapping every invocation in ``conda run``.
    """

    @property
    def python_version(self) -> str:
        """The ``major.minor`` Python version to request from conda."""
        return f"{sys.version_info.major}.{sys.version_info.minor}"

    def exists(self) -> bool:
        """`True` iff the conda environment directory and its `conda-meta` are
        present."""
        return self.venv_path.exists() and (self.venv_path / "conda-meta").exists()

    def prepare(self, recreate=False) -> bool:
        """Prepare a conda environment at the given path.

        If the environment does not already exist, or a recreate has been
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
                self.venv_path.parent.mkdir(parents=True, exist_ok=True)
                self.tools.subprocess.run(
                    [
                        "conda",
                        "create",
                        "--prefix",
                        self.venv_path,
                        f"python={self.python_version}",
                        "--yes",
                        *(["--quiet"] if not self.tools.console.is_verbose else []),
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Failed to create virtual environment at {self.venv_path}"
                ) from e

        return True

    def clean(self) -> None:
        """Remove the conda environment directory tree if it exists."""
        if self.exists():
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
        """Build a subprocess environment that activates the conda environment.

        Prepends the environment's `bin_dir` to `PATH`, sets `CONDA_PREFIX`,
        and removes `PYTHONHOME`. Caller-supplied overrides are honoured.

        :param overrides: Caller-supplied environment overrides.
        :returns: An updated environment applying modifications
            to enable the virtual environment
        """
        env = dict(overrides) if overrides else {}

        old_path = env.get("PATH") or os.environ.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["CONDA_PREFIX"] = os.fspath(self.venv_path)
        env.pop("PYTHONHOME", None)

        return env
