# tests/commands/base/test_precedence.py
from __future__ import annotations

from pathlib import Path

import briefcase.commands.base as base_mod
from briefcase.commands.base import BaseCommand

# tests/commands/base/test_precedence.py


class DummyConsole:
    def __init__(self):
        import io

        self.buffer = io.StringIO()

    def print(self, *args, **kwargs):
        self.buffer.write(" ".join(map(str, args)) + "\n")

    def info(self, *args, **kwargs):
        self.buffer.write(" ".join(map(str, args)) + "\n")


class DummyCommand(BaseCommand):
    command = "config"
    description = "dummy"
    platform = "android"
    output_format = "gradle"

    def __init__(self):
        super().__init__(console=DummyConsole())
        # Leave self.tools as created by BaseCommand; it already has .console
        self.apps = {}
        self.global_config = None

    @property
    def binary_path(self) -> Path:
        return Path("bin")

    def verify_tools(self):
        pass


def _write_empty_pyproject(tmp_path: Path) -> Path:
    """Create an empty file just so BaseCommand.parse_config can open it."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("", encoding="utf-8")
    return pyproject


def test_cli_overrides_everything(tmp_path, monkeypatch):
    """CLI overrides take top priority for both global and app configs."""
    cmd = DummyCommand()
    pyproject = _write_empty_pyproject(tmp_path)

    # 1) Stub pyproject parser: return baseline global/app
    def fake_parse_config(fileobj, platform, output_format, console):
        global_cfg = {"author": {"email": "py@example.com"}}
        app_cfgs = {
            "demo": {
                "author": {"email": "pyapp@example.com"},
                "android": {"device": "@PY_AVD"},
            }
        }
        return global_cfg, app_cfgs

    # 2) Stub user config loader: return (global_user, project_user)
    def fake_load_user_config_files(project_root):
        global_user = {
            "author": {"email": "global@example.com"},
            "android": {"device": "emulator-5554"},
        }
        project_user = {"author": {"email": "project@example.com"}}
        return global_user, project_user

    # 3) Make create_config a pass-through so we can assert dicts directly
    monkeypatch.setattr(base_mod, "parse_config", fake_parse_config)
    monkeypatch.setattr(base_mod, "load_user_config_files", fake_load_user_config_files)
    monkeypatch.setattr(base_mod, "create_config", lambda klass, config, msg: config)

    # CLI overrides we want to win
    overrides = {
        "author": {"email": "cli@example.com"},
        "android": {"device": "emulator-9999"},
    }

    cmd.parse_config(filename=pyproject, overrides=overrides)

    # Global merged config should reflect CLI values
    assert cmd.global_config["author"]["email"] == "cli@example.com"
    assert cmd.global_config["android"]["device"] == "emulator-9999"

    # App merged config should also reflect CLI values
    assert "demo" in cmd.apps
    app = cmd.apps["demo"]
    assert app["author"]["email"] == "cli@example.com"
    assert app["android"]["device"] == "emulator-9999"


def test_pyproject_overrides_user_configs(tmp_path, monkeypatch):
    """When CLI doesn't specify a key, pyproject value overrides user-level values."""
    cmd = DummyCommand()
    pyproject = _write_empty_pyproject(tmp_path)

    # pyproject declares email/device that should override user config
    def fake_parse_config(fileobj, platform, output_format, console):
        return (
            {"author": {"email": "py@example.com"}, "android": {"device": "@PY_AVD"}},
            {"demo": {"author": {"email": "pyapp@example.com"}}},
        )

    def fake_load_user_config_files(project_root):
        # user configs disagree with pyproject; pyproject should win
        return (
            {
                "author": {"email": "global@example.com"},
                "android": {"device": "emulator-5554"},
            },
            {
                "author": {"email": "project@example.com"},
                "android": {"device": "@PROJ_AVD"},
            },
        )

    monkeypatch.setattr(base_mod, "parse_config", fake_parse_config)
    monkeypatch.setattr(base_mod, "load_user_config_files", fake_load_user_config_files)
    monkeypatch.setattr(base_mod, "create_config", lambda klass, config, msg: config)

    cmd.parse_config(filename=pyproject, overrides={})  # no CLI overrides

    # Global picks pyproject over user configs
    assert cmd.global_config["author"]["email"] == "py@example.com"
    assert cmd.global_config["android"]["device"] == "@PY_AVD"

    # App config gets user-merged first, then pyproject wins for missing/overlapping keys
    app = cmd.apps["demo"]
    assert app["author"]["email"] == "pyapp@example.com"
    # 'android.device' wasn't specified at app level; should come from user merge → project wins over global
    assert app["android"]["device"] == "@PROJ_AVD"


def test_project_user_overrides_global_user_when_pyproject_missing(
    tmp_path, monkeypatch
):
    """If pyproject doesn't define a key, project-user value overrides global-user."""
    cmd = DummyCommand()
    pyproject = _write_empty_pyproject(tmp_path)

    def fake_parse_config(fileobj, platform, output_format, console):
        # pyproject omits 'android.device' both globally and for app
        return (
            {"author": {"email": "py@example.com"}},
            {"demo": {"author": {"email": "pyapp@example.com"}}},
        )

    def fake_load_user_config_files(project_root):
        return (
            {"android": {"device": "emulator-5554"}},  # global user
            {"android": {"device": "@PROJ_AVD"}},  # project user (should win)
        )

    monkeypatch.setattr(base_mod, "parse_config", fake_parse_config)
    monkeypatch.setattr(base_mod, "load_user_config_files", fake_load_user_config_files)
    monkeypatch.setattr(base_mod, "create_config", lambda klass, config, msg: config)

    cmd.parse_config(filename=pyproject, overrides={})

    # Global inherits user merge; project user wins over global user
    assert cmd.global_config["android"]["device"] == "@PROJ_AVD"

    # App inherits the same merged user view (since pyproject omitted), so also @PROJ_AVD
    assert cmd.apps["demo"]["android"]["device"] == "@PROJ_AVD"
