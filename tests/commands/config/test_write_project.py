from unittest.mock import Mock, patch

import pytest
import tomli

from briefcase.commands.config import ConfigCommand


@pytest.fixture
def config_command(tmp_path):
    tools = Mock()
    tools.base_path = None
    tools.host_os = "Windows"
    tools.input = Mock()
    console = Mock()
    return ConfigCommand(tools=tools, console=console)


def test_write_project_config(tmp_path, config_command):
    # Set up project directory structure
    project_dir = tmp_path / "myapp"
    config_path = project_dir / ".briefcase" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Set config_command base path
    config_command.tools.base_path = project_dir

    with patch("briefcase.commands.config.tomli.load", return_value={}):
        config_command(key="iOS.device", value="iPhone 15", global_config=False)

    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config["iOS"]["device"] == "iPhone 15"
