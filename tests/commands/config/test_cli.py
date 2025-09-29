# tests/commands/config/test_cli.py
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

from briefcase.commands.config import ConfigCommand
from briefcase.exceptions import BriefcaseConfigError

if sys.version_info >= (3, 11):  # pragma: no-cover-if-lt-py311
    import tomllib
else:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib


class DummyConsole:
    """Minimal console capturing .print() and .info() output like other tests do."""

    def __init__(self):
        self.buffer = io.StringIO()

    def print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        self.buffer.write(text + "\n")

    def info(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        self.buffer.write(text + "\n")

    def getvalue(self) -> str:
        return self.buffer.getvalue()


def make_command():
    return ConfigCommand(console=DummyConsole())


def project_scope_path(project_root: Path) -> Path:
    return project_root / ".briefcase" / "config.toml"


def global_scope_path(global_root: Path) -> Path:
    return global_root / "config.toml"


def test_set_outside_project_without_global_errors(monkeypatch):
    """Running 'set' outside a Briefcase project without --global raises."""
    cmd = make_command()

    # Simulate "not in a project": find_project_root raises BriefcaseConfigError
    def _raise():
        raise BriefcaseConfigError("No Briefcase project found")

    monkeypatch.setattr("briefcase.commands.config.find_project_root", _raise)

    with pytest.raises(BriefcaseConfigError):
        cmd(
            mode="set",
            key="author.email",
            value="user@example.com",
            global_scope=False,  # no --global
            list=False,
        )


def test_global_scope_set_get_list_unset(tmp_path, monkeypatch):
    """Global scope round-trip for set/get/list/unset."""
    cmd = make_command()

    # Redirect the global scope path into a temp dir
    def _scope_path(project_root, is_global: bool):
        if is_global:
            return global_scope_path(tmp_path)
        else:
            # project path shouldn't be used in this test
            return project_scope_path(tmp_path)

    # Never called in this test; patch anyway for completeness
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)
    monkeypatch.setattr("briefcase.commands.config.scope_path", _scope_path)

    # 1) set (global)
    cmd(
        mode="set",
        key="author.email",
        value="user@example.com",
        global_scope=True,  # --global
        list=False,
    )

    # Verify file content
    gpath = global_scope_path(tmp_path)
    assert gpath.exists()
    with gpath.open("rb") as f:
        data = tomllib.load(f)
    assert data["author"]["email"] == "user@example.com"

    # 2) get (global)
    cmd(
        get="author.email",
        global_scope=True,
    )

    out = cmd.console.getvalue()
    assert "user@example.com" in out

    # Clear console capture
    cmd.console.buffer = io.StringIO()

    # 3) list (global)
    cmd(
        mode=None,
        key=None,
        value=None,
        global_scope=True,
        list=True,
    )
    out = cmd.console.getvalue()
    # should show a TOML-ish dump including our key
    assert "author" in out
    assert "email" in out
    assert "user@example.com" in out

    # 4) unset (global)
    cmd.console.buffer = io.StringIO()
    cmd(
        unset="author.email",
        global_scope=True,
    )
    # file no longer has author.email
    with gpath.open("rb") as f:
        data2 = tomllib.load(f)
    assert "author" not in data2 or "email" not in data2.get("author", {})


def test_project_scope_set_get_list_unset(tmp_path, monkeypatch):
    """Project scope round-trip when inside a project (find_project_root returns
    tmp)."""
    cmd = make_command()

    # Simulate being *inside* a project
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)

    # Use actual scope_path logic based on the found project root, but ensure
    # global also lands in tmp_path for isolation.
    def _scope_path(project_root, is_global: bool):
        if is_global or project_root is None:
            return global_scope_path(tmp_path)
        return project_scope_path(project_root)

    monkeypatch.setattr("briefcase.commands.config.scope_path", _scope_path)

    # 1) set (project)
    cmd(
        mode="set",
        key="android.device",
        value="@Pixel_7_API_34",
        global_scope=False,  # project scope
        list=False,
    )

    # Verify project config file content
    ppath = project_scope_path(tmp_path)
    assert ppath.exists()
    with ppath.open("rb") as f:
        pdata = tomllib.load(f)
    assert pdata["android"]["device"] == "@Pixel_7_API_34"

    # 2) get (project)
    cmd(
        get="android.device",
        global_scope=False,
    )
    out = cmd.console.getvalue()
    assert "@Pixel_7_API_34" in out

    # 3) list (project)
    cmd.console.buffer = io.StringIO()
    cmd(
        mode=None,
        key=None,
        value=None,
        global_scope=False,
        list=True,
    )
    out = cmd.console.getvalue()
    assert "android" in out
    assert "device" in out
    assert "@Pixel_7_API_34" in out

    # 4) unset (project)
    cmd.console.buffer = io.StringIO()
    cmd(
        unset="android.device",
        global_scope=False,
    )
    with ppath.open("rb") as f:
        pdata2 = tomllib.load(f)
    assert "android" not in pdata2 or "device" not in pdata2.get("android", {})


def test_cli_rejects_unknown_key(tmp_path, monkeypatch):
    """CLI 'set' rejects keys outside the allow-list."""
    cmd = make_command()
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)

    def _scope_path(project_root, is_global: bool):
        return project_scope_path(project_root or tmp_path)

    monkeypatch.setattr("briefcase.commands.config.scope_path", _scope_path)

    with pytest.raises(BriefcaseConfigError):
        cmd(
            mode="set",
            key="foo.bar",
            value="baz",
            global_scope=False,
            list=False,
        )


def test_cli_rejects_invalid_value(tmp_path, monkeypatch):
    """CLI 'set' rejects values that fail per-key validation."""
    cmd = make_command()
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)

    def _scope_path(project_root, is_global: bool):
        return project_scope_path(project_root or tmp_path)

    monkeypatch.setattr("briefcase.commands.config.scope_path", _scope_path)

    with pytest.raises(BriefcaseConfigError):
        cmd(
            mode="set",
            key="android.device",
            value="R58N42ABCD",  # invalid under strict Android rule
            global_scope=False,
            list=False,
        )


def test_no_operation_errors(monkeypatch, tmp_path):
    # global/project resolution won't be used, but wire them anyway
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        "briefcase.commands.config.scope_path",
        lambda pr, is_global: (
            tmp_path / ("g.toml" if is_global else ".briefcase/config.toml")
        ),
    )
    with pytest.raises(BriefcaseConfigError):
        make_command()(global_scope=True)


def test_multiple_operations_errors(monkeypatch, tmp_path):
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        "briefcase.commands.config.scope_path",
        lambda pr, is_global: (
            tmp_path / ("g.toml" if is_global else ".briefcase/config.toml")
        ),
    )
    with pytest.raises(BriefcaseConfigError):
        make_command()(get="author.name", list=True, global_scope=True)
