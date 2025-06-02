from unittest.mock import Mock, patch

import pytest
import tomli
import tomli_w

from briefcase.commands.config import ConfigCommand


@pytest.fixture
def config_command(tmp_path):
    tools = Mock()
    tools.base_path = None
    tools.host_os = "Windows"
    tools.input = Mock()
    console = Mock()
    return ConfigCommand(tools=tools, console=console)


@patch("briefcase.commands.config.PlatformDirs")
def test_write_global_config(mock_platform_dirs, tmp_path, config_command):
    # Set up a fake global config directory
    global_config_dir = tmp_path / "user_config"
    config_path = global_config_dir / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(tomli_w.dumps({}), encoding="utf-8")

    # Patch PlatformDirs instance to return our custom path
    mock_instance = Mock()
    mock_instance.user_config_dir = str(global_config_dir)
    mock_platform_dirs.return_value = mock_instance

    config_command.tools.path = mock_instance

    config_command(
        key="android.sdk_path", value="/usr/local/android-sdk", global_config=True
    )

    assert config_path.exists()
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert "android" in config
    assert config["android"]["sdk_path"] == "/usr/local/android-sdk"
