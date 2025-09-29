from __future__ import annotations

import io
from pathlib import Path

import pytest
import tomli_w

from briefcase.commands.config import ConfigCommand
from briefcase.exceptions import BriefcaseConfigError


class DummyConsole:
    def __init__(self):
        self.buffer = io.StringIO()

    def print(self, *args, **kwargs):
        self.buffer.write(" ".join(str(a) for a in args) + "\n")

    def info(self, *args, **kwargs):
        self.buffer.write(" ".join(str(a) for a in args) + "\n")

    def warning(self, *args, **kwargs):
        self.buffer.write(" ".join(str(a) for a in args) + "\n")

    def getvalue(self) -> str:
        return self.buffer.getvalue()


def make_cmd():
    # BaseCommand.__init__ requires a console
    return ConfigCommand(console=DummyConsole())


def project_scope_path(project_root: Path) -> Path:
    return project_root / ".briefcase" / "config.toml"


def global_scope_path(tmp_root: Path) -> Path:
    return tmp_root / "config.toml"


def patch_scope_for_global(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("briefcase.commands.config.find_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        "briefcase.commands.config.scope_path",
        lambda project_root, is_global: global_scope_path(tmp_path)
        if is_global
        else project_scope_path(tmp_path),
    )


def test_no_operation_errors(tmp_path, monkeypatch):
    """Calling the command with no get/unset/list/key+value raises an error."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)
    with pytest.raises(BriefcaseConfigError):
        cmd(global_scope=True)  # no op provided


def test_multiple_operations_error(tmp_path, monkeypatch):
    """Providing more than one operation at once is rejected."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)
    with pytest.raises(BriefcaseConfigError):
        cmd(get="author.name", list=True, global_scope=True)


def test_set_empty_value_rejected(tmp_path, monkeypatch):
    """Empty/whitespace values on set are rejected by validation."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)
    with pytest.raises(BriefcaseConfigError):
        cmd(key="author.email", value="   ", global_scope=True)


@pytest.mark.parametrize(
    "key", ["android.device", "iOS.device", "macOS.identity", "macOS.xcode.identity"]
)
def test_question_sentinel_allowed_for_device_identity(tmp_path, monkeypatch, key):
    """'?' sentinel is accepted for device/identity keys."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # set
    cmd(key=key, value="?", global_scope=True)

    # verify it was written
    path = global_scope_path(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "?" in text and key.split(".")[0] in text


def test_question_sentinel_rejected_elsewhere(tmp_path, monkeypatch):
    """'?' sentinel is rejected for non-device/identity keys."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)
    with pytest.raises(BriefcaseConfigError):
        cmd(key="author.email", value="?", global_scope=True)


def test_list_empty_file_prints_empty_marker(tmp_path, monkeypatch):
    """Listing an empty (or non-existent) config prints the '(empty)' marker."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # Ensure file not there / empty
    path = global_scope_path(tmp_path)
    if path.exists():
        path.unlink()

    cmd(list=True, global_scope=True)
    out = cmd.console.getvalue()
    assert "(empty)" in out and str(path) in out


def test_get_missing_key_warns_or_says_nothing(tmp_path, monkeypatch):
    """Getting a missing key should not crash; ensure graceful behavior."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # write some other content
    path = global_scope_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        tomli_w.dumps({"author": {"name": "Jane Developer"}}), encoding="utf-8"
    )

    # get a key that isn't present
    cmd(get="author.email", global_scope=True)
    out = cmd.console.getvalue()
    # Accept either a warning or no output, but it must not include a bogus value
    assert "jane@example.com" not in out


def test_unset_missing_key_warns_not_crash(tmp_path, monkeypatch):
    """Unsetting a missing key logs a warning, not a crash."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # Start with empty file
    path = global_scope_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tomli_w.dumps({}), encoding="utf-8")

    cmd(unset="author.email", global_scope=True)
    out = cmd.console.getvalue()
    # Warning text should mention the key (implementation emits a 'not present' line)
    assert "author.email" in out


def test_read_toml_invalid_raises(tmp_path, monkeypatch):
    """Invalid TOML is converted into a BriefcaseConfigError."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # Create a syntactically invalid TOML
    path = global_scope_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("author = { email = 'missing_quote }", encoding="utf-8")

    # Listing forces a read
    with pytest.raises(BriefcaseConfigError):
        cmd(list=True, global_scope=True)


def test_write_error_surfaces_as_error(tmp_path, monkeypatch):
    """Write failures are surfaced (write_toml raising propagates)."""
    cmd = make_cmd()
    patch_scope_for_global(monkeypatch, tmp_path)

    # Monkeypatch write_toml to raise OSError
    def boom_write(path: Path, data: dict):
        raise OSError("disk full")

    monkeypatch.setattr("briefcase.commands.config.write_toml", boom_write)

    with pytest.raises(OSError):
        cmd(key="author.email", value="user@example.com", global_scope=True)


def test_project_scope_outside_project_requires_global(tmp_path, monkeypatch):
    """Outside a project, attempting project-scope operations errors."""
    cmd = make_cmd()

    # Simulate 'not in a project' for project scope
    def _raise():
        raise BriefcaseConfigError("No Briefcase project found")

    monkeypatch.setattr("briefcase.commands.config.find_project_root", _raise)
    monkeypatch.setattr(
        "briefcase.commands.config.scope_path",
        lambda project_root, is_global: project_scope_path(tmp_path),
    )

    with pytest.raises(BriefcaseConfigError):
        cmd(key="author.email", value="user@example.com", global_scope=False)
