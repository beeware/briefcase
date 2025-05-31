from unittest.mock import Mock, patch

import pytest

from briefcase.integrations.config import Config


@pytest.fixture
def mock_tools():
    tools = Mock()
    tools.base_path = "project/root"
    tools.input.selection = Mock(return_value="prompt-val")
    tools.app_configs = {"myapp": Mock()}
    tools.app_configs["myapp"].author = "pyproject-val"
    return tools


@pytest.mark.parametrize(
    "cli_value, project_val, global_val, expect",
    [
        ("some-cli-val", None, None, "some-cli-val"),  # CLI wins
        (None, "proj-val", None, "proj-val"),  # Project wins
        (None, None, "globl-val", "global-val"),  # Global wins
        (None, None, None, "pyproject-val"),  # Pyproject wins
        (None, None, None, None),  # Nothing set
    ],
)
@patch("briefcase.integrations.config.Config.load_toml")
def test_config_resolution_order(
    mock_load_toml, mock_tools, cli_value, project_val, global_val, expect
):
    # Configure mock returns for project and global config
    mock_load_toml.side_effect = [
        {"author": project_val} if project_val else {},
        {"author": global_val} if global_val else {},
    ]
    config = Config(mock_tools)
    result = config.get("author", cli_value=cli_value)
    assert result == expect


@patch("briefcase.integrations.config.Config.load_toml")
def test_nested_key_access(mock_load_toml, mock_tools):
    mock_load_toml.side_effect = [{"ios": {"device": "iPhone 15"}}, {}]
    config = Config(mock_tools)
    result = config.get("ios.device")
    assert result == "iPhone 15"


@patch("briefcase.integrations.config.Config.load_toml")
def test_invalid_nested_key(mock_load_toml, mock_tools):
    mock_load_toml.side_effect = [{}, {}]
    config = Config(mock_tools)
    result = config.get("invalid.key")
    assert result is None
