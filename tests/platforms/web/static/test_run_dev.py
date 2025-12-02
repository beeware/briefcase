from unittest import mock

import pytest

from briefcase.exceptions import UnsupportedCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.virtual_environment import VenvContext
from briefcase.platforms.web.static import StaticWebDevCommand


@pytest.fixture
def dev_command(dummy_console, tmp_path):
    command = StaticWebDevCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()
    return command


@pytest.fixture
def default_venv() -> VenvContext:
    """Create a venv mock for tests that require a venv parameter."""
    mock_venv = mock.MagicMock(spec=VenvContext)
    mock_venv.run.return_value = mock.MagicMock()
    mock_venv.check_output.return_value = ""
    mock_venv.Popen.return_value = mock.MagicMock()
    mock_venv.executable = "/mock/venv/bin/python"
    return mock_venv


def test_run_dev_app_raises_unsupported_command_error(dev_command, first_app_config):
    """Test that run_dev_app raises UnsupportedCommandError for web platform."""
    with pytest.raises(UnsupportedCommandError) as excinfo:
        dev_command.run_dev_app(
            first_app_config,
            env={},
            venv=mock.MagicMock(spec=VenvContext),
            passthrough=[],
        )

    assert excinfo.value.platform == "web"
    assert excinfo.value.output_format == "static"
    assert excinfo.value.command == "dev"


def test_venv_name_override(dev_command):
    """StaticWebDevCommand overrides venv_name to 'dev-web'."""
    assert dev_command.venv_name == "dev-web"
