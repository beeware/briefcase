import subprocess
import sys
from pathlib import Path

from briefcase.config import AppConfig
from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError


class VenvEnvironment:
    def __init__(self, tools, console: Console, base_path: Path, app: AppConfig):
        self.tools = tools
        self.console = console
        self.app = app
        self.venv_path = base_path / ".briefcase" / app.app_name / "venv"
        self.pyvenv_cfg = self.venv_path / "pyvenv.cfg"

    def __enter__(self):
        self.console.info(
            f"Looking for isolated virtual environment for {self.app.app_name}."
        )

        if self.pyvenv_cfg.exists():
            self.console.info("Found existing virtual environment. Skipping creation.")
        else:
            self.console.info("No virtual environment found. Creating...")
            try:
                self.venv_path.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_path)],
                    check=True,
                )
                self.console.info("Virtual environment created successfully.")
            except subprocess.CalledProcessError as e:
                raise BriefcaseCommandError(
                    f"Failed to create virtual environment for {self.app.app_name}."
                ) from e

        return self.venv_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class NoOpEnvironment:
    def __init__(self, tools, console: Console, base_path: Path, app: AppConfig):
        self.tools = tools
        self.console = console
        self.app = app

    def __enter__(self):
        self.console.info(f"Running {self.app.app_name} without isolated environment.")
        return Path(sys.prefix)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def virtual_environment(
    tools, console: Console, base_path: Path, app: AppConfig, **options
):
    if options.get("no_isolation"):
        return NoOpEnvironment(tools, console, base_path, app)
    else:
        return VenvEnvironment(tools, console, base_path, app)
