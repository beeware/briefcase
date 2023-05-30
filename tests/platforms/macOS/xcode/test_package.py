from unittest import mock

import pytest

import briefcase.integrations.xcode
from briefcase.console import Console, Log
from briefcase.platforms.macOS.xcode import macOSXcodePackageCommand

# skip most tests since packaging uses the same code as app command


@pytest.fixture
def package_command(tmp_path):
    command = macOSXcodePackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    return command


def test_verify(package_command, monkeypatch):
    """If you're on macOS, you can verify tools."""
    package_command.tools.host_os = "Darwin"

    mock_ensure_xcode_is_installed = mock.MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.Xcode,
        "ensure_xcode_is_installed",
        mock_ensure_xcode_is_installed,
    )
    mock_ensure_command_line_tools_are_installed = mock.MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "ensure_command_line_tools_are_installed",
        mock_ensure_command_line_tools_are_installed,
    )
    mock_confirm_xcode_license_accepted = mock.MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "confirm_xcode_license_accepted",
        mock_confirm_xcode_license_accepted,
    )

    package_command.verify_tools()

    assert package_command.tools.xcode_cli is not None
    mock_ensure_xcode_is_installed.assert_called_once_with(
        tools=package_command.tools,
        min_version=(13, 0, 0),
    )
    mock_ensure_command_line_tools_are_installed.assert_called_once_with(
        tools=package_command.tools
    )
    mock_confirm_xcode_license_accepted.assert_called_once_with(
        tools=package_command.tools
    )
