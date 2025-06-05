from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import tomli

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.config import Config


@pytest.fixture
def mock_tools():
    tools = Mock()
    tools.base_path = Path("project/root")
    tools.input.selection = Mock(return_value="prompt-val")
    tools.app_configs = {"myapp": Mock()}
    tools.app_configs["myapp"].author = "pyproject-val"
    return tools


def test_cli_prompt(mock_tools):
    config = Config(mock_tools)
    result = config.get("author", cli_value="?", prompt="Choose", choices=["A", "B"])
    assert result == "prompt-val"
    mock_tools.input.selection.assert_called_once_with("Choose", ["A", "B"])


@patch("briefcase.integrations.config.Config.load_toml")
def test_missing_pyproject_attribute(mock_load_toml, mock_tools):
    mock_tools.app_configs = {"myapp": Mock(spec=[])}  # No attributes allowed
    mock_load_toml.side_effect = [{}, {}]
    config = Config(mock_tools)
    result = config.get("author")
    assert result is None


@patch("briefcase.integrations.config.Config.load_toml")
def test_toml_decode_error(mock_load_toml, mock_tools):
    mock_load_toml.side_effect = tomli.TOMLDecodeError(
        msg="Invalid TOML", doc="content", pos=1
    )

    config = Config(mock_tools)
    with pytest.raises(tomli.TOMLDecodeError):
        config.get("author")


@patch("briefcase.integrations.config.Config.load_toml")
def test_multiple_apps_suppresses_pyproject(mock_load_toml):
    tools = Mock()
    tools.base_path = Path("project/root")
    tools.input.selection = Mock(return_value="prompt-val")
    tools.app_configs = {"a": Mock(), "b": Mock()}  # Multiple apps
    mock_load_toml.side_effect = [{}, {}]

    config = Config(tools)
    with pytest.raises(BriefcaseCommandError) as excinfo:
        config.get("author")

    assert "specifies more than one application" in str(excinfo.value)


@patch("briefcase.integrations.config.Config.load_toml")
def test_project_config_reading(mock_load_toml, mock_tools):
    mock_load_toml.side_effect = [{"some": {"key": "project_val"}}, {}]
    config = Config(mock_tools)
    result = config.get("some.key")
    assert result == "project_val"


@patch("briefcase.integrations.config.PlatformDirs")
@patch("briefcase.integrations.config.Config.load_toml")
def test_global_config_reading(
    mock_load_toml, mock_platform_dirs, mock_tools, tmp_path
):
    mock_instance = mock_platform_dirs.return_value
    mock_instance.user_config_dir = str(tmp_path)

    mock_load_toml.side_effect = [{}, {"some": {"key": "global_val"}}]
    config = Config(mock_tools)
    result = config.get("some.key")
    assert result == "global_val"
