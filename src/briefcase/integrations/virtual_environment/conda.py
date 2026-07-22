import os
import shutil
import subprocess
import sys
from pathlib import Path

from packaging.version import Version

from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT
from briefcase.integrations.virtual_environment.base import VirtualEnvironment


class CondaVirtualEnvironment(VirtualEnvironment):
    """An environment manager using conda.

    The environment is created as a prefix-based conda environment (`conda
    create --prefix <path>`). The Python interpreter installed into the
    environment matches the major/minor version of the interpreter running
    Briefcase. Commands are executed against the environment by activating it
    (prepending the environment's binary directory to ``PATH``).
    """

    env_type: str = "conda"
    provides_python: bool = True
    verified: bool = False

    @classmethod
    def verify(cls, tools: ToolCache):
        """Verify that the environment manager is available."""
        # If conda has already been verified, shortcut the verification process.
        if cls.verified:
            return

        try:
            output = (
                tools.subprocess.check_output(["conda", "--version"])
                .strip("\n")
                .split(" ")
            )
            _, conda_version = output

            if Version(conda_version) < Version("26.5"):
                raise BriefcaseCommandError(f"""\
Briefcase requires Conda 26.5 (or newer); you have {conda_version}.

To upgrade your Conda version, run:

    conda install --name base 'conda>=26.5'
""")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise BriefcaseCommandError("""\
Could not find a Conda installation.

Ensure that you have installed Conda, and you are running Briefcase in an
active Conda environment.
""") from e
        else:
            cls.verified = True

    @property
    def python_version(self) -> str:
        """The ``major.minor`` Python version to request from conda."""
        return f"{sys.version_info.major}.{sys.version_info.minor}"

    def exists(self) -> bool:
        """`True` iff the conda environment directory and its `conda-meta` are
        present."""
        return self.venv_path.exists() and (self.venv_path / "conda-meta").exists()

    @property
    def executable(self) -> Path:
        """Path to the Python executable inside the venv."""
        return (
            self.venv_path / "python.exe"
            if self.tools.host_os == "Windows"
            else self.bin_dir / "python"
        )

    @property
    def conda_exe(self):
        return "conda.bat" if self.tools.host_os == "Windows" else "conda"

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
                        self.conda_exe,
                        "create",
                        "--prefix",
                        self.venv_path,
                        "--yes",
                        *(["--quiet"] if not self.tools.console.is_verbose else []),
                        f"python={self.python_version}",
                        "pip",
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
        requires: list[str],
        allow_editable: bool = False,
        require_binary: bool = False,
        include_deps: bool = True,
        install_path: Path | None = None,
        min_os_version: str | None = None,
        extra_installer_args: list[str] | None = None,
        install_hint: str = "",
    ):
        """Install requirements into the environment with `conda install`.

        Conda has no concept of editable installs, so `allow_editable` is
        ignored.

        :param requires: The list of requirements to install.
        :param allow_editable: Should editable installs be allowed?
        :param require_binary: Ignored; Conda always requires binary content.
        :param include_deps: Should transitive dependencies be installed?
        :param install_path: Ignored; Conda always installs into its own site-packages.
        :param min_os_version: Ignored; Conda self-enforces the min OS version.
        :param extra_installer_args: A list of additional arguments to pass to the
            installer.
        :param install_hint: If an install fails, an additional context-specific hint
            that can be displayed to the user.
        """
        if not requires:
            return

        conda_requires = []
        pip_requires = []
        for req in requires:
            # Any requirement that is a local path or a URL must be installed with pip.
            if self.tools.file.is_scm_url(req):
                pip_requires.append(req)
            elif self.tools.file.is_local_path(req):
                # If editable installs are allowed, and the requirement is *not* a
                # reference to an archive file (zip, tgz, etc) or wheel, it can be
                # installed editable.
                if (
                    allow_editable
                    and not self.tools.file.is_archive(req)
                    and Path(req).suffix != ".whl"
                ):
                    pip_requires.extend(["-e", req])
                else:
                    pip_requires.append(req)
            else:
                conda_requires.append(req)

        if conda_requires:
            try:
                if self.tools.console.is_verbose:
                    install_args = []
                else:
                    install_args = ["--quiet"]

                if not include_deps:
                    install_args.append("--no-deps")

                if extra_installer_args:
                    install_args.extend(extra_installer_args)

                self.tools.subprocess.run(
                    [
                        self.conda_exe,
                        "install",
                        "--prefix",
                        self.venv_path,
                        "--yes",
                        *install_args,
                        *conda_requires,
                    ],
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RequirementsInstallError(install_hint=install_hint) from e

        # If there are requirements that have to be installed with pip,
        # run a separate `pip install` pass in the conda environment.
        if pip_requires:
            try:
                install_args = ["--only-binary", ":all:"]
                if not include_deps:
                    install_args.append("--no-deps")

                self.run(
                    [
                        "pip",
                        "install",
                        *install_args,
                        *pip_requires,
                    ],
                    check=True,
                    env={
                        "PIP_REQUIRE_VIRTUALENV": None,
                    },
                )
            except subprocess.CalledProcessError as e:
                raise RequirementsInstallError(install_hint=install_hint) from e

    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Run the command in a conda environment.

        If the first argument is a reference to `sys.executable`, replace it
        with a reference to the Conda environment Python interpreter. Otherwise,
        run the command with `conda run`.
        """
        head = os.fspath(args[0])
        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return [self.executable, *args[1:]]
        else:
            # Run the command in the environment; don't capture stdout.
            return [
                self.conda_exe,
                "run",
                "--prefix",
                self.venv_path,
                "--no-capture-output",
                *args,
            ]

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
