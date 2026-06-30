import os
import shutil
import subprocess
import sys
from pathlib import Path

from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class PixiVirtualEnvironment(VirtualEnvironment):
    """An environment manager using pixi.

    A pixi *workspace* is created at the requested path (`pixi init`), with a
    Python dependency added that matches the major/minor version of the
    interpreter running Briefcase. Pixi materialises the actual environment in
    a ``.pixi/envs/default`` directory inside the workspace, so the binary
    directory and Python executable are resolved relative to that location.
    """

    @property
    def provides_python(self) -> bool:
        return False

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
            f"{creating} Pixi environment ({self.venv_path.name})..."
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
                    f"Failed to create Pixi environment at {self.venv_path}"
                ) from e

        return True

    def clean(self) -> None:
        """Remove the pixi workspace directory tree if it exists."""
        if self.venv_path.exists():
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
                    "pixi",
                    "add",
                    "--manifest-path",
                    self.venv_path,
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
        return [
            "pixi",
            "run",
            "--manifest-path",
            self.venv_path,
            "--executable",
            head,
            *args[1:],
        ]

    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str | None] | None:
        """Return an environment for the conda invocation.

        No special handling is required, as all pixi commands take
        a `--prefix` argument.

        :param overrides: Caller-supplied environment overrides.
        :returns: `overrides`
        """
        return overrides
