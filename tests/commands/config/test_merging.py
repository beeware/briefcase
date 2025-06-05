from unittest.mock import Mock

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


def test_nested_key_merging(tmp_path, config_command, monkeypatch):
    # Create existing project config with partial section
    config_dir = tmp_path / ".briefcase"
    config_path = config_dir / "config.toml"
    config_dir.mkdir(parents=True)
    config_path.write_text(
        tomli_w.dumps({"iOS": {"existing": "yes"}}), encoding="utf-8"
    )

    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n", encoding="utf-8"
    )

    # Set tool base path
    config_command.tools.base_path = tmp_path
    monkeypatch.chdir(tmp_path)

    config_command(key="iOS.device", value="iPhone 15", global_config=False)

    # Read back and parse using tomli
    with config_path.open("rb") as f:
        config = tomli.load(f)

    assert config["iOS"]["existing"] == "yes"
    assert config["iOS"]["device"] == "iPhone 15"
