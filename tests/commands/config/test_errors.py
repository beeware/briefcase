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


def test_missing_pyproject_toml(config_command, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # No pyproject.toml

    with pytest.raises(BriefcaseConfigError) as exc:
        config_command(key="author.name", value="Jane Smith", global_config=False)

    assert "Not a valid Briefcase project" in str(exc.value)


def test_permission_error_on_read(tmp_path, config_command, monkeypatch):
    config_path = tmp_path / ".briefcase" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.touch()

    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n", encoding="utf-8"
    )
    config_command.tools.base_path = tmp_path
    monkeypatch.chdir(tmp_path)

    # Simulate a read permission error
    with patch("briefcase.commands.config.tomli.load", side_effect=PermissionError):
        with pytest.raises(BriefcaseConfigError):
            config_command(key="iOS.device", value="iPhone 15", global_config=False)


def test_permission_error_on_write(tmp_path, config_command, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n", encoding="utf-8"
    )
    config_command.tools.base_path = tmp_path

    # Patch just the internal write method to simulate a failure
    with patch.object(config_command, "write_config", side_effect=PermissionError):
        with pytest.raises(BriefcaseConfigError) as exc:
            config_command(key="iOS.device", value="iPhone 15", global_config=False)

        assert "Unable to write configuration file" in str(exc.value)


def test_double_dot_key(config_command, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.briefcase]\nproject_name = 'test'\n", encoding="utf-8"
    )

    with pytest.raises(BriefcaseConfigError) as exc:
        config_command(key="author..name", value="Jane", global_config=False)

    assert "Invalid configuration key" in str(exc.value)
