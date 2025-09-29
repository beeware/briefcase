from unittest import mock

from briefcase.commands import DevCommand


def test_virtual_environment_isolated(dummy_console, tmp_path):
    """The base DevCommand.virtual_environment() method works with isolated=True."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    expected_venv_path = tmp_path / "base_path" / ".briefcase" / "test-app" / "venv"
    mock_dev_command.venv_path.return_value = expected_venv_path

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command, "test-app", isolated=True
        )

        mock_dev_command.venv_path.assert_called_once_with("test-app")

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

    expected_venv_path = tmp_path / "base_path" / ".briefcase" / "my-app" / "venv"
    mock_dev_command.venv_path.return_value = expected_venv_path

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command, "my-app", isolated=False
        )

        mock_dev_command.venv_path.assert_called_once_with("my-app")

        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=False,
        )
        assert result == mock_venv.return_value


def test_virtual_environment_uses_venv_path(dummy_console, tmp_path):
    """The virtual_environment method uses venv_path to determine the path."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.venv_path.return_value = tmp_path / "custom" / "path"

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        DevCommand.virtual_environment(mock_dev_command, "test-app", isolated=True)

        mock_dev_command.venv_path.assert_called_once_with("test-app")

        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=tmp_path / "custom" / "path",
            isolated=True,
        )
