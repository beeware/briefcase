from __future__ import annotations

from unittest.mock import Mock

import pytest
import tomli

from briefcase.commands.config import ConfigCommand


@pytest.fixture
def config_command():
    return ConfigCommand(console=Mock())


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("author.name", "Jane Smith", {"author": {"name": "Jane Smith"}}),
        ("author.email", "jane@example.com", {"author": {"email": "jane@example.com"}}),
        (
            "iOS.device",
            "iPhone 15 Pro::iOS 17.5",
            {"iOS": {"device": "iPhone 15 Pro::iOS 17.5"}},
        ),
        ("android.device", "@Pixel_5", {"android": {"device": "@Pixel_5"}}),
    ],
)
def test_write_project_config(
    config_command, monkeypatch, tmp_path, key, value, expected
):
    # Make this tmp directory the Briefcase project root
    (tmp_path / "pyproject.toml").write_text("[tool.briefcase]\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    config_command(key=key, value=value, global_scope=False)

    # Load and verify the project-level config
    config_path = tmp_path / ".briefcase" / "config.toml"
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config == expected
