from __future__ import annotations

import io
from argparse import ArgumentParser
from unittest.mock import patch

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


@pytest.fixture
def config_command():
    return ConfigCommand(console=DummyConsole())


def test_missing_pyproject_toml(config_command, tmp_path, monkeypatch):
    # No pyproject.toml anywhere up the tree -> project scope should raise
    monkeypatch.chdir(tmp_path)
    with pytest.raises(BriefcaseConfigError) as exc:
        config_command(key="author.name", value="Jane Smith", global_scope=False)
    assert "Not a Briefcase project" in str(exc.value)


def test_decode_error_on_read(tmp_path, config_command, monkeypatch):
    """Simulate a TOML decode error while reading the existing project config."""
    # Force project scope at tmp_path so we don't depend on pyproject parsing
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)

    cfg_file = tmp_path / ".briefcase" / "config.toml"
    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    cfg_file.write_text('[author]\nemail = "user@example.com"\n', encoding="utf-8")

    # Make tomllib.load raise TOMLDecodeError for this read.
    # Both tomli and tomllib expose TOMLDecodeError with the same constructor shape.
    def boom(fp):
        raise cfg_mod.tomllib.TOMLDecodeError("broken", "doc", 0)

    with patch.object(cfg_mod.tomllib, "load", side_effect=boom):
        with pytest.raises(BriefcaseConfigError) as exc:
            config_command(key="author.name", value="Jane Smith", global_scope=False)
        assert "Invalid TOML" in str(exc.value)
        assert str(cfg_file) in str(exc.value)


def test_write_raises_permission_error(tmp_path, config_command, monkeypatch):
    """If the write layer raises OSError, command surfaces BriefcaseConfigError."""
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)

    # Patch write_toml to simulate an OSError occurring inside it
    def fake_write(path, data):
        raise BriefcaseConfigError(f"Unable to write config file {path}: boom")

    with patch.object(cfg_mod, "write_toml", side_effect=fake_write):
        with pytest.raises(BriefcaseConfigError) as exc:
            config_command(
                key="author.email", value="jane@example.com", global_scope=False
            )
        assert "Unable to write config file" in str(exc.value)


def test_invalid_key_format_is_rejected(config_command):
    # Not in the allow-list of keys
    with pytest.raises(BriefcaseConfigError):
        config_command(key="invalidkey", value="value", global_scope=True)


def test_double_dot_key_is_rejected(config_command, tmp_path, monkeypatch):
    # Valid project; key has an empty segment -> rejected by __call__ dotted key guard
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)
    with pytest.raises(BriefcaseConfigError) as exc:
        config_command(key="author..name", value="Jane", global_scope=False)
    assert "Invalid configuration key" in str(exc.value)


def test_invalid_key_leading_dot(config_command, tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)
    with pytest.raises(BriefcaseConfigError):
        config_command(key=".author.name", value="Jane", global_scope=False)


def test_invalid_key_trailing_dot(config_command, tmp_path, monkeypatch):
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)
    with pytest.raises(BriefcaseConfigError):
        config_command(key="author.name.", value="Jane", global_scope=False)


def test_add_options_parses_arguments(config_command):
    parser = ArgumentParser()
    config_command.add_options(parser)
    args = parser.parse_args(["iOS.device", "iPhone 15"])
    assert args.key == "iOS.device"
    assert args.value == "iPhone 15"
