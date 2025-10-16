import argparse
import importlib
import io
from pathlib import Path

import pytest


# ---- tiny console that mirrors the rest of the project ----
class _StreamConsole:
    def __init__(self):
        self._buf = io.StringIO()

    def print(self, msg):
        print(msg, file=self._buf)

    def info(self, msg):
        print(msg, file=self._buf)

    def warning(self, msg):
        print(msg, file=self._buf)

    def error(self, msg):
        print(msg, file=self._buf)

    def getvalue(self):
        return self._buf.getvalue()

    def clear(self):
        self._buf.seek(0)
        self._buf.truncate(0)


@pytest.fixture
def cfg_mod():
    """Import the module under test once per test function (fresh enough for unit
    tests)."""
    return importlib.import_module("briefcase.commands.config")


@pytest.fixture
def make_cmd_and_parser(cfg_mod):
    """Returns a factory that builds (cmd, parser, console).

    We parse the *config* subcommand options directly (no global CLI).
    """

    def factory():
        console = _StreamConsole()
        cmd = cfg_mod.ConfigCommand(console=console)
        parser = argparse.ArgumentParser(prog="briefcase config", add_help=False)
        cmd.add_options(parser)
        return cmd, parser, console

    return factory


@pytest.fixture
def force_global_path(monkeypatch, tmp_path, cfg_mod):
    """Force global-scope path to a temp file so tests are hermetic.

    Returns the target Path.
    """
    target = tmp_path / "briefcase" / "config.toml"

    def scope_path(project_root, is_global: bool):
        return (
            target if is_global else (Path(project_root) / ".briefcase" / "config.toml")
        )

    monkeypatch.setattr(cfg_mod, "scope_path", scope_path, raising=True)
    return target


@pytest.fixture
def make_project(tmp_path):
    """Create a minimal Briefcase project that satisfies discovery in
    find_project_root().

    Returns the project Path.
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "pyproject.toml").write_text(
        "[tool.briefcase]\n"
        "[tool.briefcase.app.example]\n"
        "formal_name = 'Example'\n"
        "bundle = 'com.example'\n"
        "version = '1.0.0'\n",
        encoding="utf-8",
    )
    return proj
