import os
import shutil
import sys
from pathlib import Path

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations import subprocess
from briefcase.integrations.subprocess import SubprocessArgsT


class VenvContext:
    """Context for running commands in a virtual environment.

    Wraps subprocess functions to ensure commands are run in the venv.
    """

    def __init__(self, tools, venv_path: Path):
        self.tools = tools
        self.venv_path = venv_path

    @property
    def bin_dir(self) -> Path:
        r"""Return the path to the virtual environment's binary directory.

        :return: <venv>/bin (or <venv>\Scripts on Windows)
        """
        return self.venv_path / ("Scripts" if os.name == "nt" else "bin")

    @property
    def executable(self) -> str:
        """Path to the Python executable in the virtual environment.

        :return: Absolute filesystem path to the venv's Python executable.
        """
        python = self.bin_dir / ("python.exe" if os.name == "nt" else "python")
        return os.fspath(python)

    def exists(self) -> bool:
        """Check whether the virtual environment exists.

        :return True if venv exists and contains a pyvenv.cfg file. else False
        """
        return self.venv_path.exists() and (self.venv_path / "pyvenv.cfg").exists()

    def create(self) -> None:
        """Create the virtual environment.

        :raises BriefcaseCommandError if creation fails.
        """
        try:
            self.venv_path.parent.mkdir(parents=True, exist_ok=True)
            self.tools.subprocess.run(
                [sys.executable, "-m", "venv", os.fspath(self.venv_path)],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Failed to create virtual environment at {self.venv_path}"
            ) from e

    def recreate(self) -> None:
        """Remove and re-create the virtual environment."""
        if self.exists():
            shutil.rmtree(self.venv_path)
        self.create()

    def update_core_tools(self):
        """Upgrade core Python packaging tooling in the venv."""
        try:
            self.run([self.executable, "-m", "pip", "install", "-U", "pip"], check=True)
        except Exception as e:
            raise BriefcaseCommandError(
                f"Virtual environment created, but failed to bootstrap pip tooling at {self.venv_path}"
            ) from e

    def _rewrite_head(self, args: SubprocessArgsT) -> SubprocessArgsT:
        """Rewrite the first argument to ensure it points to the venv's Python
        executable.

        param args: Original subprocess arguments.
        :return: Updated subprocess arguments.
        """
        if not args:
            return args
        head = os.fspath(args[0])
        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return [self.executable, *args[1:]]

        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return [self.executable, *args[1:]]
        return list(args)

    def full_env(self, overrides: dict[str, str | None] | None) -> dict[str, str]:
        """Generate the full environment for the venv.

        :param overrides: Environment variables to override or unset. Can be None if
            there are no explicit environment changes. Use None values to unset
            environment variables
        :return: environment mapping for the venv with overrides applied.
        """

        env = dict(os.environ)

        if overrides:
            env.update(overrides)

            env = {k: v for k, v in env.items() if v is not None}

        old_path = env.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["VIRTUAL_ENV"] = os.fspath(self.venv_path)

        if os.name == "nt":
            env.pop("PYTHONHOME", None)

        return env

    def run(self, args: list[str], **kwargs):
        """Run a command in the virtual environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.run.
        """
        args = self._rewrite_head(list(args))
        user_env = kwargs.pop("env", None)
        kwargs["env"] = self.full_env(user_env)
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: list[str], **kwargs):
        """Run a command in the virtual environment using Popen.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.Popen.
        """
        args = self._rewrite_head(list(args))
        user_env = kwargs.pop("env", None)
        kwargs["env"] = self.full_env(user_env)
        return self.tools.subprocess.Popen(args, **kwargs)

    def check_output(self, args: list[str], **kwargs):
        """Run a command in the virtual environment and return its output.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.check_output.
        """
        args = self._rewrite_head(list(args))
        user_env = kwargs.pop("env", None)
        kwargs["env"] = self.full_env(user_env)
        return self.tools.subprocess.check_output(args, **kwargs)


class VenvEnvironment:
    """Context manager for creating and managing a venv."""

    def __init__(
        self,
        tools,
        console: Console,
        *,
        path: Path,
        recreate: bool = False,
        update_pip: bool = True,
    ):
        self.tools = tools
        self.console = console
        self.venv_path = path
        self.pyvenv_cfg = self.venv_path / "pyvenv.cfg"
        self.recreate = recreate
        self.update_pip = update_pip
        self.venv_context = VenvContext(self.tools, self.venv_path)

    def __enter__(self):
        if self.recreate:
            with self.console.wait_bar("Recreating virtual environment..."):
                self.venv_context.recreate()
        elif not self.venv_context.exists():
            with self.console.wait_bar(
                f"Creating virtual environment at {self.venv_path}..."
            ):
                self.venv_context.create()

        if self.update_pip:
            with self.console.wait_bar("Upgrading pip tooling in virtual environment"):
                self.venv_context.update_core_tools()

        return self.venv_context

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class NoOpEnvironment:
    """A no-op environment that returns a native runner."""

    def __init__(self, tools, console: Console):
        self.tools = tools
        self.console = console

    def __enter__(self):
        return self.tools.subprocess

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def virtual_environment(
    tools,
    console: Console,
    base_path: Path,
    *,
    isolated: bool = True,
    recreate: bool = False,
    update_pip: bool = True,
) -> VenvEnvironment | NoOpEnvironment:
    """Return a environment context for the requested isolation settings. Creates either
    a virtual environment context or a no-op context.

    :param tools: The tools instance
    :param console: The console instance
    :param base_path: Base path for the virtual environment
    :param app: Application configuration
    :param isolated: If False, return NoOpEnvironment. Default True.
    :param recreate: Whether to recreate existing venv. Default False.
    :param update_pip: Whether to update pip after setup. Default True.
    :raises BriefcaseCommandError: if isolated=True but base_path is None.
    :returns: VenvEnvironment or NoOpEnvironment
    """
    if not isolated:
        return NoOpEnvironment(tools=tools, console=console)

    if base_path is None:
        raise BriefcaseCommandError("A virtual environment path must be provided")

    venv_path = base_path / "venv"

    return VenvEnvironment(
        tools=tools,
        console=console,
        path=venv_path,
        recreate=recreate,
        update_pip=update_pip,
    )
