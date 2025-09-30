from __future__ import annotations

import io

import pytest
import tomli
import tomli_w

import briefcase.commands.config as cfg_mod
from briefcase.commands.config import ConfigCommand


class DummyConsole:
    def __init__(self):
        self.buf = io.StringIO()

    def print(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")

    def info(self, *a, **k):
        self.buf.write(" ".join(map(str, a)) + "\n")


@pytest.fixture
def config_command():
    return ConfigCommand(console=DummyConsole())


def test_nested_key_merging(tmp_path, config_command, monkeypatch):
    # Existing nested structure + adding a sibling key preserves both.
    config_dir = tmp_path / ".briefcase"
    config_path = config_dir / "config.toml"
    config_dir.mkdir(parents=True)
    config_path.write_text(
        tomli_w.dumps({"iOS": {"existing": "yes"}}), encoding="utf-8"
    )

    # Recognize tmp_path as the project root
    monkeypatch.setattr(cfg_mod, "find_project_root", lambda start=None: tmp_path)

    # Add a new nested key
    config_command(key="iOS.device", value="My iPhone::iOS 16.0", global_scope=False)

    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config["iOS"]["existing"] == "yes"
    assert config["iOS"]["device"] == "My iPhone::iOS 16.0"
