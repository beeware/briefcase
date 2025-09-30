from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
import tomli
import tomli_w

from briefcase.commands.config import ConfigCommand


@pytest.fixture
def config_command():
    # No special console behavior needed here
    return ConfigCommand(console=Mock())


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("author.name", "Jane Smith", {"author": {"name": "Jane Smith"}}),
        ("author.email", "jane@example.com", {"author": {"email": "jane@example.com"}}),
        ("android.device", "@Pixel_5", {"android": {"device": "@Pixel_5"}}),
        (
            "iOS.device",
            "Alice's iPhone::iOS 16.0",
            {"iOS": {"device": "Alice's iPhone::iOS 16.0"}},
        ),
    ],
)
@patch("briefcase.commands.config.PlatformDirs")
def test_write_global_config(
    mock_platform_dirs, tmp_path, config_command, key, value, expected
):
    # Fake the platformdirs location
    global_config_dir = tmp_path / "user_config"
    config_path = global_config_dir / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(tomli_w.dumps({}), encoding="utf-8")

    mock_instance = Mock()
    mock_instance.user_config_dir = str(global_config_dir)
    mock_platform_dirs.return_value = mock_instance

    # Write
    config_command(key=key, value=value, global_scope=True)

    assert config_path.exists()
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config == expected


@patch("briefcase.commands.config.PlatformDirs")
def test_write_global_creates_file(mock_platform_dirs, tmp_path, config_command):
    global_dir = tmp_path / "user_config"
    config_path = global_dir / "config.toml"

    mock_instance = Mock()
    mock_instance.user_config_dir = str(global_dir)
    mock_platform_dirs.return_value = mock_instance

    config_command(key="author.email", value="enabled@example.com", global_scope=True)

    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config["author"]["email"] == "enabled@example.com"
