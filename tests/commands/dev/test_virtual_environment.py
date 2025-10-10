import sys
from unittest import mock

from briefcase.commands import DevCommand


def test_virtual_environment_isolated(dummy_console, tmp_path):
    """The base DevCommand.virtual_environment() method works with isolated=True."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    expected_venv_path = (
        tmp_path / "base_path" / ".briefcase" / "test-app" / f"dev-{python_version}"
    )
    mock_dev_command.venv_path.return_value = expected_venv_path

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command,
            "test-app",
            isolated=True,
            recreate=False,
        )

        mock_dev_command.venv_path.assert_called_once_with("test-app")

        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=True,
            recreate=False,
        )
        assert result == mock_venv.return_value


def test_virtual_environment_not_isolated(dummy_console, tmp_path):
    """The base DevCommand.virtual_environment() method works with isolated=False."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.tools = mock.MagicMock()
    mock_dev_command.console = dummy_console
    mock_dev_command.base_path = tmp_path / "base_path"

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    expected_venv_path = (
        tmp_path / "base_path" / ".briefcase" / "my-app" / f"dev-{python_version}"
    )
    mock_dev_command.venv_path.return_value = expected_venv_path

    with mock.patch("briefcase.commands.dev.virtual_environment") as mock_venv:
        result = DevCommand.virtual_environment(
            mock_dev_command,
            "my-app",
            isolated=False,
            recreate=True,
        )

        mock_dev_command.venv_path.assert_called_once_with("my-app")

        mock_venv.assert_called_once_with(
            tools=mock_dev_command.tools,
            console=mock_dev_command.console,
            venv_path=expected_venv_path,
            isolated=False,
            recreate=True,
        )
        assert result == mock_venv.return_value


def test_venv_path_construction(tmp_path):
    """The venv_path method constructs the correct path using venv_name."""
    mock_dev_command = mock.MagicMock(spec=DevCommand)
    mock_dev_command.base_path = tmp_path / "base_path"

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    mock_dev_command.venv_name = f"dev-{python_version}"

    result = DevCommand.venv_path(mock_dev_command, "test-app")

    expected = (
        tmp_path / "base_path" / ".briefcase" / "test-app" / f"dev-{python_version}"
    )
    assert result == expected


def test_venv_name_includes_python_version(tmp_path):
    """The venv_name includes the Python version."""
    dev_command = DevCommand(
        console=mock.MagicMock(),
        base_path=tmp_path,
    )

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert dev_command.venv_name == f"dev-{python_version}"
