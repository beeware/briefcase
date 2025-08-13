import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from briefcase.config import AppConfig
from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError


def venv_bin(venv_path: Path):
    return venv_path / ("Scripts" if os.name == "nt" else "bin")


def venv_python(venv_path: Path):
    return venv_bin(venv_path) / ("python.exe" if os.name == "nt" else "python")


def env_with_venv(base_env: Optional[dict], venv_path: Optional[Path]):
    env = dict(base_env or os.environ)
    if venv_path is not None:
        env["VIRTUAL_ENV"] = os.fspath(venv_path)
        env["PATH"] = os.fspath(venv_bin(venv_path)) + os.pathsep + env.get("PATH", "")
        env.pop("PYTHONHOME", None)
        env.setdefault("PIP_DISABLE_PIP_VERSION_CHECK", "1")
    return env


class VenvRunner:
    def __init__(self, tools, venv_path: Optional[Path]):
        self.tools = tools
        self.venv_path = venv_path

    @property
    def python(self):
        if self.venv_path is None:
            return sys.executable
        return os.fspath(venv_python(self.venv_path))

    @property
    def env(self):
        return env_with_venv(os.environ, self.venv_path)

    def _rewrite_head(self, args: list[str]):
        if not args:
            return args
        head = str(args[0]).lower()
        candidates = ("python", "python3", "python.exe", str(sys.executable).lower())
        if head.endswith(candidates):
            return [self.python, *args[1:]]
        return args

    def run(self, args: list[str], **kwargs):
        args = self._rewrite_head(list(args))
        kwargs.setdefault("env", self.env)
        return self.tools.subprocess.run(args, **kwargs)

    def Popen(self, args: list[str], **kwargs):
        args = self._rewrite_head(list(args))
        kwargs.setdefault("env", self.env)
        return self.tools.subprocess.Popen(args, **kwargs)


def make_runner(tools, venv_path: Optional[Path]):
    return VenvRunner(tools=tools, venv_path=venv_path)


def pip_install_generic(
    tools,
    console,
    requires: list[str],
    *,
    venv_path: Path | None = None,
    extra_args: list[str] | None = None,
    message: str = "Installing requirements...",
    deep_debug: bool = False,
):
    if not requires:
        console.info("No requirements")
        return
    py_exe = os.fspath(venv_python(venv_path)) if venv_path else sys.executable
    env = env_with_venv(os.environ, venv_path)
    args = [py_exe, "-u", "-X", "utf8", "-m", "pip", "install", "--upgrade"]
    if deep_debug:
        args.append("-vv")
    if extra_args:
        args.extend(extra_args)
    args.extend(requires)

    with console.wait_bar(message):
        tools.subprocess.run(args, check=True, encoding="UTF-8", env=env)


class VenvEnvironment:
    def __init__(
        self,
        tools,
        console: Console,
        base_path: Path,
        app: AppConfig,
        *,
        recreate: bool = False,
        path: Optional[Path] = None,
        upgrade_bootstrap: bool = True,
    ):
        self.tools = tools
        self.console = console
        self.app = app
        self.venv_path = (
            path
            if path is not None
            else (base_path / ".briefcase" / app.app_name / "venv")
        )
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
                    subprocess.run(
                        [sys.executable, "-m", "venv", os.fspath(self.venv_path)],
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    raise BriefcaseCommandError(
                        f"Failed to create virtual environment for {self.app.app_name}"
                    ) from e

            if self.upgrade_bootstrap:
                with self.console.wait_bar(
                    "Upgrading pip tooling in virtual environment..."
                ):
                    try:
                        py = os.fspath(venv_python(self.venv_path))
                        env = env_with_venv(os.environ, self.venv_path)
                        subprocess.run(
                            [
                                py,
                                "-m",
                                "pip",
                                "install",
                                "-U",
                                "pip",
                                "setuptools",
                                "wheel",
                            ],
                            check=True,
                            env=env,
                        )
                    except subprocess.CalledProcessError as e:
                        raise BriefcaseCommandError(
                            f"Virtual environment created, but failed to bootstrap pip tooling for {self.app.app_name}"
                        ) from e
        return self.venv_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def virtual_environment(
    tools, console: Console, base_path: Path, app: AppConfig, **options
):
    return VenvEnvironment(
        tools,
        console,
        base_path,
        app,
        recreate=bool(options.get("update_requirements")),
        path=options.get("path"),
        upgrade_bootstrap=options.get("upgrade_bootstrap", True),
    )
