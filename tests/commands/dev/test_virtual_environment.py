from unittest import mock

from briefcase.commands import DevCommand


def test_virtual_environment_isolated(dummy_console, tmp_path):
    """The base DevCommand.virtual_environment() method works with isolated=True."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command, "test-app", isolated=True
        )

        expected_venv_path = tmp_path / "base_path" / ".briefcase" / "test-app" / "venv"
        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=True,
        )
        assert result == mock_venv.return_value


def test_virtual_environment_not_isolated(dummy_console, tmp_path):
    """The base DevCommand.virtual_environment() method works with isolated=False."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command, "my-app", isolated=False
        )

        expected_venv_path = tmp_path / "base_path" / ".briefcase" / "my-app" / "venv"
        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=False,
        )
        assert result == mock_venv.return_value
