from __future__ import annotations

import io
from pathlib import Path

import pytest
import tomli_w

from briefcase.commands import config as cfg_mod
from briefcase.commands.config import (
    ConfigCommand,
    find_project_root,
    get_config,
    normalize_briefcase_root,
    read_toml,
    scope_path,
    set_config,
    unset_config,
    write_toml,
)
from briefcase.exceptions import BriefcaseConfigError


class DummyConsole:
    def __init__(self):
        self.buf = io.StringIO()

    def print(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def info(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def warning(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")


def test_scope_path_global_uses_platformdirs(monkeypatch, tmp_path):
    """scope_path(global) resolves into PlatformDirs user_config_dir / config.toml."""

    class FakeDirs:
        def __init__(self):
            self.user_config_dir = str(tmp_path / "uconf")

    monkeypatch.setattr(cfg_mod, "PlatformDirs", lambda *a, **k: FakeDirs())
    p = scope_path(project_root=None, is_global=True)
    assert p == tmp_path / "uconf" / "config.toml"


def test_scope_path_project(tmp_path):
    pr = tmp_path
    p = scope_path(project_root=pr, is_global=False)
    assert p == pr / ".briefcase" / "config.toml"


def test_find_project_root_success(tmp_path, monkeypatch):
    """find_project_root walks up until it finds a pyproject with [tool.briefcase]."""
    base = tmp_path / "a" / "b" / "c"
    base.mkdir(parents=True)
    py = tmp_path / "a" / "pyproject.toml"
    py.write_text(
        tomli_w.dumps({"tool": {"briefcase": {"foo": "bar"}}}), encoding="utf-8"
    )
    monkeypatch.chdir(base)
    assert find_project_root() == tmp_path / "a"


def test_find_project_root_no_project(tmp_path, monkeypatch):
    """No pyproject with [tool.briefcase] -> BriefcaseConfigError."""
    d = tmp_path / "x" / "y"
    d.mkdir(parents=True)
    (tmp_path / "x" / "pyproject.toml").write_text(" [tool.poetry]\n", encoding="utf-8")
    monkeypatch.chdir(d)
    with pytest.raises(BriefcaseConfigError):
        find_project_root()


def test_read_toml_ok_and_invalid(tmp_path):
    path = tmp_path / "c.toml"
    # ok
    path.write_text('author = { email = "user@example.com" }', encoding="utf-8")
    assert read_toml(path)["author"]["email"] == "user@example.com"
    # invalid
    path.write_text("author = { email = 'missing_quote }", encoding="utf-8")
    with pytest.raises(BriefcaseConfigError):
        read_toml(path)


def test_normalize_briefcase_root_accepts_nested_and_root():
    nested = {"tool": {"briefcase": {"android": {"device": "@AVD"}}}}
    assert normalize_briefcase_root(nested) == {"android": {"device": "@AVD"}}
    root = {"android": {"device": "@AVD"}}
    assert normalize_briefcase_root(root) == root
    assert normalize_briefcase_root({}) == {}


def test_write_toml_ok_and_error(tmp_path, monkeypatch):
    p = tmp_path / "out.toml"

    write_toml(p, {"author": {"name": "Jane"}})
    assert p.exists()

    # error path: simulate open() failure so write_toml catches OSError and re-raises
    def boom_open(*a, **k):
        raise OSError("disk full")

    class FakeFile(Path):
        _flavour = Path(".")._flavour

        def open(self, *a, **k):
            return boom_open()

    with pytest.raises(BriefcaseConfigError):
        write_toml(FakeFile(p), {"x": 1})


def test_get_set_unset_helpers():
    d = {}
    set_config(d, "author.name", "Jane")
    set_config(d, "author.email", "jane@example.com")
    assert get_config(d, "author.name") == "Jane"
    assert get_config(d, "author.email") == "jane@example.com"
    # unset present
    assert unset_config(d, "author.email") is True
    assert get_config(d, "author.email") is None
    # unset missing -> False
    assert unset_config(d, "author.email") is False


def test_configcommand_placeholders_raise():
    cmd = ConfigCommand(console=DummyConsole())
    with pytest.raises(NotImplementedError):
        cmd.bundle_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_path(None)
    with pytest.raises(NotImplementedError):
        cmd.distribution_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_executable_path(None)
