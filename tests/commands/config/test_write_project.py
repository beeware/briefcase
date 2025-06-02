from unittest.mock import Mock

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


def test_write_project_config(config_command, monkeypatch, tmp_path):
    # Simulate running inside a valid Briefcase project
    monkeypatch.chdir(tmp_path)

    # Create a minimal valid pyproject.toml
    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n"
    )

    config_command.__call__(key="iOS.device", value="iPhone 15", global_config=False)

    # Load and verify the project-level config
    config_path = tmp_path / ".briefcase" / "config.toml"
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config == {"iOS": {"device": "iPhone 15"}}
