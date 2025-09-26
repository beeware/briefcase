import os
import shutil
import subprocess as stdlib_subprocess
import sys
from pathlib import Path

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations import subprocess
from briefcase.integrations.base import Tool, ToolCache
from briefcase.integrations.subprocess import SubprocessArgsT


class VenvContext(Tool):
    """Context for running commands in a virtual environment.

    Wraps subprocess functions to ensure commands are run in the venv.
    """

    name = "venv_context"
    full_name = "Virtual Environment Context"

    def __init__(self, tools, venv_path: Path):
        super().__init__(tools=tools)
        self.venv_path = venv_path

    @classmethod
    def verify_install(
        cls, tools: ToolCache, venv_path: Path, **kwargs
    ) -> "VenvContext":
        """Return a VenvContext for the specified path."""
        return cls(tools=tools, venv_path=venv_path)

    @property
    def bin_dir(self) -> Path:
        r"""Return the path to the virtual environment's binary directory.

        :return: The ``/bin`` (``\Scripts`` on Windows) directory of the venv.
        """
        return self.venv_path / ("Scripts" if os.name == "nt" else "bin")

    @property
    def executable(self) -> str:
        """Path to the Python executable in the virtual environment.

        :return: Absolute filesystem path to the venv's Python executable.
        """
        python = self.bin_dir / ("python.exe" if os.name == "nt" else "python")
        return python

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
                [sys.executable, "-m", "venv", self.venv_path],
                check=True,
            )
            self.update_core_tools()
        except stdlib_subprocess.CalledProcessError as e:
            raise BriefcaseCommandError(
                f"Failed to create virtual environment at {self.venv_path}"
            ) from e

    def recreate(self) -> None:
        """Remove and re-create the virtual environment."""
        if self.exists():
            shutil.rmtree(self.venv_path)
        self.create()

    def update_core_tools(self) -> None:
        """Upgrade core Python packaging tooling in the venv."""
        try:
            self.run([self.executable, "-m", "pip", "install", "-U", "pip"], check=True)
        except Exception as e:
            raise BriefcaseCommandError(
                f"Failed to update core tooling for {self.venv_path}"
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

        return list(args)

    def full_env(self, overrides: dict[str, str | None] | None) -> dict[str, str]:
        """Generate the full environment for the venv.

        :param overrides: Environment variables to override or unset. Can be None if
            there are no explicit environment changes. Use None values to unset
            environment variables
        :return: environment mapping for the venv with overrides applied.
        """

        if overrides:
            env = overrides.copy()
        else:
            env = {}

        old_path = env.get("PATH") or os.environ.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["VIRTUAL_ENV"] = os.fspath(self.venv_path)

        # Remove PYTHONHOME to avoid conflicts with the venv.
        env.pop("PYTHONHOME", None)

        return env

    def run(self, args: SubprocessArgsT, **kwargs) -> subprocess.CompletedProcess:
        """Run a command in the virtual environment.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.run.
        :returns: CompletedProcess from the subprocess execution.
        """
        args = self._rewrite_head(list(args))
        user_env = kwargs.pop("env", None)
        kwargs["env"] = self.full_env(user_env)
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: SubprocessArgsT, **kwargs) -> stdlib_subprocess.Popen:
        """Run a command in the virtual environment using Popen.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.Popen.
        :returns: A Popen instance for the subprocess execution.
        """
        args = self._rewrite_head(list(args))
        user_env = kwargs.pop("env", None)
        kwargs["env"] = self.full_env(user_env)
        return self.tools.subprocess.Popen(args, **kwargs)

    def check_output(self, args: SubprocessArgsT, **kwargs) -> str:
        """Run a command in the virtual environment and return its output.

        :param args: Command and arguments to run.
        :param kwargs: Additional keyword arguments to pass to subprocess.check_output.
        :returns: String output from the subprocess execution.
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
    ):
        self.tools = tools
        self.console = console
        self.venv_path = path
        self.recreate = recreate
        self.venv_context = VenvContext.verify_install(
            tools=self.tools, venv_path=self.venv_path
        )

    def __enter__(self):
        if self.recreate:
            with self.console.wait_bar("Recreating virtual environment..."):
                self.venv_context.recreate()
        elif not self.venv_context.exists():
            with self.console.wait_bar(
                f"Creating virtual environment at {self.venv_path}..."
            ):
                self.venv_context.create()

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
    venv_path: Path,
    *,
    isolated: bool = True,
    recreate: bool = False,
) -> VenvEnvironment | NoOpEnvironment:
    """Return a environment context for the requested isolation settings. Creates either
    a virtual environment context or a no-op context.

    If an isolated environment is requested, a `venv_path` *must* be provided.

    :param tools: The tools instance
    :param console: The console instance
    :param venv_path: Complete path for the virtual environment
    :param isolated: If False, return NoOpEnvironment. Default True.
    :param recreate: Whether to recreate existing venv. Default False.
    :returns: A context manager for an environment where code can be executed.
    """
    if not isolated:
        return NoOpEnvironment(tools=tools, console=console)

    if venv_path is None:
        raise BriefcaseCommandError("A virtual environment path must be provided")

    return VenvEnvironment(
        tools=tools,
        console=console,
        path=venv_path,
        recreate=recreate,
    )
