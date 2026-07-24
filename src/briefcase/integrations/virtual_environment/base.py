import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from briefcase.config import FinalizedAppConfig
from briefcase.exceptions import RequirementsInstallError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT


class VirtualEnvironment(ABC):
    """A managed Python environment."""

    env_type: str = "?"
    provides_python: bool = False

    def __init__(
        self,
        name: str,
        app: FinalizedAppConfig,
        tools: ToolCache,
        base_path: Path,
        *,
        platform: str | None = None,
        arch: str | None = None,
        platform_path: Path | None = None,
    ):
        """Initialise the virtual environment on a specific path.

        :param name: An identifying name for the environment. This will not be
            the *full* name; the environment will add additional information to
            disambiguate the app and environment type.
        :param app: The app configuration
        :param tools: The shared :class:`ToolCache` instance.
        :param base_path: The root of the project path.
        :param platform: The platform for the environment. If this isn't the
            host OS, the environment will be a cross build environment.
        :param arch: The architecture for the environment. If this isn't the
            host OS architeceture, the environment will be a cross build
            environment.
        :param platform_path: The path where platform details are stored.
        """
        self.name = name
        self.app = app
        self.tools = tools
        self.base_path = base_path
        self.platform = platform
        self.arch = arch
        self.platform_path = platform_path

    @property
    def venv_path(self):
        return (
            self.base_path
            / f".briefcase/{self.app.app_name}/{self.env_type}-{self.name}"
        )

    @classmethod
    @abstractmethod
    def verify(cls, tools: ToolCache):
        """Verify that the environment manager is available."""

    @property
    def bin_dir(self) -> Path:
        """The venv's binary directory (`bin` on POSIX, `Scripts` on Windows)."""
        return self.venv_path / (
            "Scripts" if self.tools.host_os == "Windows" else "bin"
        )

    @property
    def executable(self) -> Path:
        """Path to the Python executable inside the venv."""
        return self.bin_dir / (
            "python.exe" if self.tools.host_os == "Windows" else "python"
        )

    @abstractmethod
    def exists(self) -> bool:
        """`True` iff the environment is in a usable state.

        For an isolated venv: the venv directory exists and contains
        `pyvenv.cfg`. For a no-op environment: always `True`.
        """

    @abstractmethod
    def prepare(self, recreate=False) -> bool:
        """Ensure the virtual environment exists.

        If the environment does not already exist, or a recreate has been requested,
        create it.

        :param recreate: Force recreating the environment.
        :returns: `True` if the environment was created (or re-created).
        :raises BriefcaseCommandError: if venv creation or pip upgrade fails.
        """

    @abstractmethod
    def clean(self) -> None:
        """Remove the on-disk state associated with this environment."""

    def platform_tag(self, min_os_version: str | None):
        if self.platform == "macOS":
            min_os_tag = (min_os_version or "11.0").replace(".", "_")
            return f"macosx_{min_os_tag}_{self.arch}"
        elif self.platform in {"iphoneos", "iphonesimulator"}:
            min_os_tag = (min_os_version or "13.0").replace(".", "_")
            return f"ios_{min_os_tag}_{self.arch}_{self.platform}"
        else:
            # No --platform flag needed
            return None

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
        """Install requirements into the environment with pip.

        This should be overridden by subclasses if the environment uses a tool
        other than `pip` to install requirements.

        :param requires: The list of requirements to install.
        :param allow_editable: Should editable installs be allowed?
        :param require_binary: Should binary wheels be required?
        :param include_deps: Should transitive dependencies be installed?
        :param install_path: Where should the packages be installed?
        :param min_os_version: The minimum OS version to enforce on packages.
        :param extra_installer_args: A list of additional arguments to pass to the
            installer.
        :param install_hint: If an install fails, an additional context-specific hint
            that can be displayed to the user.
        """
        install_reqs = []
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
                install_reqs.extend(["-e", req])
            else:
                install_reqs.append(req)

        try:
            install_args = []
            if install_path:
                install_args.append(f"--target={install_path}")
                if platform_tag := self.platform_tag(min_os_version):
                    install_args.extend(["--platform", platform_tag])

            if require_binary:
                install_args.extend(["--only-binary", ":all:"])

            if not include_deps:
                install_args.append("--no-deps")

            # Platforms that need the BeeWare repo
            if self.platform in {"iphoneos", "iphonesimulator"}:
                install_args.extend(
                    [
                        "--extra-index-url",
                        "https://pypi.anaconda.org/beeware/simple",
                    ]
                )

            if extra_installer_args:
                install_args.extend(
                    self.tools.file.resolve_relative_args(
                        extra_installer_args,
                        self.base_path,
                    )
                )

            self.run(
                [
                    self.executable,
                    "-u",
                    "-X",
                    "utf8",
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-user",
                    "--upgrade",
                    *(["-vv"] if self.tools.console.is_deep_debug else []),
                    *install_args,
                    *install_reqs,
                ],
                check=True,
                encoding="UTF-8",
            )
        except subprocess.CalledProcessError as e:
            raise RequirementsInstallError(install_hint=install_hint) from e

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
        return self.tools[self.app].app_context.run(args, **kwargs)

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
        return self.tools[self.app].app_context.Popen(args, **kwargs)

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
        return self.tools[self.app].app_context.check_output(args, **kwargs)
