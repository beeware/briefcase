import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from briefcase.exceptions import RequirementsInstallError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT


class VirtualEnvironment(ABC):
    """A managed Python environment.

    The virtual environment will exist on disk after an instance of this object has been
    constructed. The instance can be used as a context manager; entering/exiting the
    context doesn't do anything.
    """

    def __init__(
        self,
        tools: ToolCache,
        venv_path: Path,
        *,
        recreate: bool = False,
    ):
        """Initialise the virtual environment on a specific path.

        :param tools: The shared :class:`ToolCache` instance.
        :param venv_path: The on-disk path associated with this environment.
            For an isolated venv, this is the venv directory; for a no-op
            environment, it is the directory used for the marker file.
        :param recreate: Should the environment be recreated if it already exists?
        """
        self.tools = tools
        self.venv_path = venv_path
        self.created = self.prepare(recreate=recreate)

    @property
    @abstractmethod
    def executable(self) -> Path:
        """The Python interpreter associated with this environment."""

    @property
    @abstractmethod
    def bin_dir(self) -> Path:
        """The directory containing the interpreter and its scripts."""

    @abstractmethod
    def exists(self) -> bool:
        """`True` iff the environment is in a usable state.

        For an isolated venv: the venv directory exists and contains
        `pyvenv.cfg`. For a no-op environment: always `True`.
        """

    @abstractmethod
    def prepare(self, recreate=False) -> bool:
        """Prepare a venv at the given environment.

        If the venv does not already exist, or a recreate has been requested, create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if venv creation or pip upgrade fails.
        """

    @abstractmethod
    def clean(self) -> None:
        """Remove the on-disk state associated with this environment."""

    def install_requirements(
        self,
        requires,
        installer_args=None,
        allow_editable=False,
    ):
        """Install requirements into the environment with pip.

        This should be overridden by subclasses if the environment uses a tool
        other than `pip` to install requirements.

        :param requires: The list of requirements to install.
        :param installer_args: A list of additional arguments to pass to the installer.
        :param allow_editable: Should editable installs be allowed?
        """
        require_args = []
        for req in requires:
            # Any requirement that is a local path, but *not* a reference to an archive
            # file (zip, tgz, etc) or wheel can be installed editable. If in doubt,
            # install non-editable.
            if (
                allow_editable
                and self.tools.file.is_local_path(req)
                and not self.tools.file.is_archive(req)
                and Path(req).suffix != ".whl"
            ):
                require_args.extend(["-e", req])
            else:
                require_args.append(req)

        try:
            self.run(
                [
                    self.executable,
                    "-u",
                    "-X",
                    "utf8",
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    *(["-vv"] if self.tools.console.is_deep_debug else []),
                    *require_args,
                    *([] if installer_args is None else installer_args),
                ],
                check=True,
                encoding="UTF-8",
            )
        except subprocess.CalledProcessError as e:
            raise RequirementsInstallError() from e

    # -- Process management -------------------------------------------------

    @abstractmethod
    def rewrite_args(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Adjust subprocess arguments for execution in this environment."""

    @abstractmethod
    def build_env(
        self,
        overrides: dict[str, str | None] | None,
    ) -> dict[str, str | None] | None:
        """Build the environment dict to pass to `subprocess`.

        :param overrides: A dictionary of environment keys to set, overriding the
            default environment.
        :returns: An updated environment applying modifications to enable the virtual
            environment
        """

    def run(self, args: SubprocessArgsT, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the virtual environment.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to `subprocess.run`.
        :returns: `CompletedProcess` from the subprocess execution.
        """
        args = self.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: SubprocessArgsT, **kwargs) -> subprocess.Popen:
        """Create a Popen instance for a command in the virtual environment.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to `subprocess.Popen`.
        :returns: A `Popen` instance for the subprocess execution.
        """
        args = self.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.Popen(args, **kwargs)

    def check_output(self, args: SubprocessArgsT, **kwargs) -> str:
        """Run a command in the virtual environment, return process output.

        References to `sys.executable` will be re-written, and the environment
        will be configured to reflect the environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to
            `subprocess.check_output`.
        :returns: String output from the subprocess execution.
        """
        args = self.rewrite_args(list(args))
        user_env = kwargs.pop("env", None)
        env = self.build_env(user_env)
        if env is not None:
            kwargs["env"] = env
        return self.tools.subprocess.check_output(args, **kwargs)

    # -- Context-manager protocol -------------------------------------------

    def __enter__(self) -> "VirtualEnvironment":
        """Return `self`.

        The lifecycle work was performed in `__init__`.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
