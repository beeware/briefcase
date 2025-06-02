from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from briefcase.commands.config import ConfigCommand
from briefcase.exceptions import BriefcaseConfigError


@pytest.fixture
def config_command(tmp_path):
    tools = Mock()
    tools.base_path = None
    tools.host_os = "Windows"
    tools.input = Mock()
    console = Mock()
    return ConfigCommand(tools=tools, console=console)


def test_invalid_key_format(tmp_path, config_command):
    config_command.tools.base_path = tmp_path

    with pytest.raises(BriefcaseConfigError):
        config_command(key="invalidkey", value="value", global_config=False)


def test_permission_error_on_read(tmp_path, config_command):
    config_path = tmp_path / ".briefcase" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()

    config_command.tools.base_path = tmp_path

    # Simulate a read permission error
    with patch("briefcase.commands.config.tomli.load", side_effect=PermissionError):
        with pytest.raises(BriefcaseConfigError):
            config_command(key="iOS.device", value="iPhone 15", global_config=False)


def test_permission_error_on_write(tmp_path, config_command):
    # Setup base path and ensure config directory exists
    config_path = tmp_path / ".briefcase" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_path.write_text('[iOS]\nexisting = "yes"\n', encoding="utf-8")

    config_command.tools.base_path = tmp_path

    # Patch Path.open used during writing to raise a PermissionError
    with patch.object(Path, "open", side_effect=PermissionError):
        with pytest.raises(BriefcaseConfigError):
            config_command(key="iOS.device", value="iPhone 15", global_config=False)
