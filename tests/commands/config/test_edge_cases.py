from __future__ import annotations

import io
from pathlib import Path

import pytest

import briefcase.commands.config as cfg_mod
from briefcase.commands.config import ConfigCommand
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

    def getvalue(self):
        return self.buf.getvalue()


def _global_path(root: Path) -> Path:
    return root / "config.toml"


def _patch_scope_global(monkeypatch, tmp: Path):
    """Route global scope into tmp; project scope would go to .briefcase/ (unused
    here)."""
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda: tmp)
    monkeypatch.setattr(
        cfg_mod,
        "scope_path",
        lambda project_root, is_global: _global_path(tmp)
        if is_global
        else (tmp / ".briefcase" / "config.toml"),
    )


def test_set_key_trimming_and_collision_not_a_table(tmp_path, monkeypatch):
    """Keys are trimmed; setting a sub-key under a non-table raises a config error."""
    _patch_scope_global(monkeypatch, tmp_path)
    cmd = ConfigCommand(console=DummyConsole())

    # 1) trimming: leading/trailing spaces in key should be accepted and written
    cmd(key="  author.name  ", value="Jane", global_scope=True)
    text = _global_path(tmp_path).read_text(encoding="utf-8")
    assert "Jane" in text

    # 2) collision: author.name is a string; setting author.name.first should error
    with pytest.raises(BriefcaseConfigError):
        cmd(key="author.name.first", value="J.", global_scope=True)


def test_get_invalid_key_is_rejected(tmp_path, monkeypatch):
    """GET on an unknown key should not crash; it should emit nothing or a warning."""
    _patch_scope_global(monkeypatch, tmp_path)
    cmd = ConfigCommand(console=DummyConsole())

    cmd(get="not.a.real.key", global_scope=True)

    out = cmd.console.getvalue()
    assert ("not.a.real.key" in out) or (out.strip() == "")


def test_unset_invalid_key_is_rejected(tmp_path, monkeypatch):
    """UNSET on an unknown key should not crash; it may warn."""
    _patch_scope_global(monkeypatch, tmp_path)
    cmd = ConfigCommand(console=DummyConsole())

    cmd(unset="not.a.real.key", global_scope=True)

    out = cmd.console.getvalue()
    assert ("not.a.real.key" in out) or (out.strip() == "")


def test_global_path_parent_dirs_created(tmp_path, monkeypatch):
    """Global scope SET should ensure parent directories exist before write."""
    # Route global scope; don't pre-create the dir
    _patch_scope_global(monkeypatch, tmp_path / "deep" / "nest")
    cmd = ConfigCommand(console=DummyConsole())

    # Should not raise; write should create parents
    cmd(key="author.email", value="user@example.com", global_scope=True)

    # Verify file exists at deep path
    gp = _global_path(tmp_path / "deep" / "nest")
    assert gp.exists()


def test_placeholders_are_not_implemented():
    """Exercise the NotImplemented placeholders at the end of the command."""
    cmd = ConfigCommand(console=DummyConsole())
    with pytest.raises(NotImplementedError):
        cmd.bundle_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_path(None)
    with pytest.raises(NotImplementedError):
        cmd.distribution_path(None)
    with pytest.raises(NotImplementedError):
        cmd.binary_executable_path(None)
