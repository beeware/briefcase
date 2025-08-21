import os
import shutil
import sys
from pathlib import Path

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations import subprocess


class VenvContext:
    """Context for running commands in a virtual environment."""

    def __init__(self, tools, venv_path: Path):
        self.tools = tools
        self.venv_path = venv_path

    @property
    def bin_dir(self) -> Path:
        """Return the path to the virtual environment's binary directory."""
        return self.venv_path / ("Scripts" if os.name == "nt" else "bin")

    @property
    def executable(self) -> str:
        """Return the path to the Python executable in the virtual environment."""
        python = self.bin_dir / ("python.exe" if os.name == "nt" else "python")
        return os.fspath(python)

    @property
    def env(self) -> dict:
        "Environment variables for the venv"
        env = dict(os.environ)
        old_path = env.get("PATH", "")
        env["PATH"] = os.fspath(self.bin_dir) + (
            os.pathsep + old_path if old_path else ""
        )
        env["VIRTUAL_ENV"] = os.fspath(self.venv_path)
        if os.name == "nt":
            env.pop("PYTHONHOME", None)
        return env

    def _rewrite_head(self, args: list[str]):
        """Rewrite the first argument to ensure it points to the venv's Python
        executable."""
        if not args:
            return list(args)
        head = os.fspath(args[0])

        if os.path.normcase(head) == os.path.normcase(sys.executable):
            return [self.executable, *args[1:]]
        return list(args)

    def run(self, args: list[str], **kwargs):
        """Run a command in the virtual environment."""
        args = self._rewrite_head(list(args))
        kwargs.setdefault("env", self.env)
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: list[str], **kwargs):
        """Run a command in the virtual environment using Popen."""
        args = self._rewrite_head(list(args))
        kwargs.setdefault("env", self.env)
        return self.tools.subprocess.Popen(args, **kwargs)

    def check_output(self, args: list[str], **kwargs):
        """Run a command in the virtual environment and return its output."""
        args = self._rewrite_head(list(args))
        kwargs.setdefault("env", self.env)
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
        upgrade_bootstrap: bool = True,
    ):
        self.tools = tools
        self.console = console
        self.venv_path = path
        self.pyvenv_cfg = self.venv_path / "pyvenv.cfg"
        self.recreate = recreate
        self.upgrade_bootstrap = upgrade_bootstrap

    def __enter__(self):
        venv_exists = self.pyvenv_cfg.exists()

        if self.recreate and venv_exists:
            self.console.info("Recreating virtual environment...")
            shutil.rmtree(self.venv_path)
            venv_exists = False

        if not venv_exists:
            with self.console.wait_bar(
                f"Creating virtual environment at {self.venv_path}..."
            ):
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

            if self.upgrade_bootstrap:
                with self.console.wait_bar(
                    "Upgrading pip tooling in virtual environment..."
                ):
                    runner = VenvContext(self.tools, self.venv_path)
                    try:
                        runner.run(
                            [runner.executable, "-m", "pip", "install", "-U", "pip"],
                            check=True,
                        )
                    except Exception as e:
                        raise BriefcaseCommandError(
                            f"Virtual environment created, but failed to bootstrap pip tooling at {self.venv_path}"
                        ) from e

        return VenvContext(tools=self.tools, venv_path=self.venv_path)

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


def virtual_environment(tools, console: Console, **options):
    """Return a environment context for the requested isolation settings".

    Options:
    - no_isolation: bool -> return NoOpEnvironment
    - path: Path -> location for venv
    - recreate: bool -> recreate venv if it exists
    - upgrade_bootstrap: bool
    """

    if options.get("no_isolation", False):
        return NoOpEnvironment(tools=tools, console=console)
    path = options.get("path")
    if path is None:
        raise BriefcaseCommandError("A virtual environment path must be providded")

    recreate = options.get("update_requirements", False)

    return VenvEnvironment(
        tools=tools,
        console=console,
        path=path,
        recreate=recreate,
        upgrade_bootstrap=options.get("upgrade_bootstrap", True),
    )
