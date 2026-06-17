import os
import shutil
import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class CondaVirtualEnvironment(VirtualEnvironment):
    """An environment manager using conda.

    The environment is created as a prefix-based conda environment (``conda
    create --prefix <path>``). The Python interpreter installed into the
    environment matches the major/minor version of the interpreter running
    Briefcase. Commands are executed against the environment by activating it
    (prepending the environment's binary directory to ``PATH``).
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
            f"{creating} Conda environment ({self.venv_path.name})..."
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
                    f"Failed to create Conda environment at {self.venv_path}"
                ) from e

        return True

    def clean(self) -> None:
        """Remove the conda environment directory tree if it exists."""
        if self.exists():
            shutil.rmtree(self.venv_path)

    def install_requirements(
        self,
        requires,
        installer_args=None,
        allow_editable=False,
    ):
        """Install requirements into the environment with `conda install`.

        Conda has no concept of editable installs, so `allow_editable` is
        ignored.

        :param requires: The list of requirements to install.
        :param installer_args: A list of additional arguments to pass to the installer.
        :param allow_editable: Ignored; conda does not support editable installs.
        """
        if not requires:
            return

        try:
            self.tools.subprocess.run(
                [
                    "conda",
                    "install",
                    "--prefix",
                    self.venv_path,
                    "--yes",
                    *(["--quiet"] if not self.tools.console.is_verbose else []),
                    *([] if installer_args is None else installer_args),
                    *requires,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RequirementsInstallError() from e

    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Run the command in a conda environment.

        If the first argument is a reference to `sys.executable`, remove
        any path component.
        """
        head = os.fspath(args[0])
        if os.path.normcase(head) == os.path.normcase(sys.executable):
            head = Path(sys.executable).name
        return ["conda", "run", "--prefix", self.venv_path, head, *args[1:]]

    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str | None] | None:
        """Return an environment for the conda invocation.

        No special handling is required, as all conda commands take
        a `--prefix` argument.

        :param overrides: Caller-supplied environment overrides.
        :returns: `overrides`
        """
        return overrides
