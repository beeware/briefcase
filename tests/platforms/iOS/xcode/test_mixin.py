from unittest.mock import MagicMock

import pytest

import briefcase.integrations.xcode
from briefcase.console import Console, Log
from briefcase.exceptions import NoDistributionArtefact
from briefcase.platforms.iOS.xcode import iOSXcodeCreateCommand


@pytest.fixture
def create_command(tmp_path):
    return iOSXcodeCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_binary_path(create_command, first_app_config, tmp_path):
    binary_path = create_command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "ios"
        / "xcode"
        / "build"
        / "Debug-iphonesimulator"
        / "First App.app"
    )


def test_distribution_path(create_command, first_app_config, tmp_path):
    with pytest.raises(
        NoDistributionArtefact,
        match=r"WARNING: No distributable artefact has been generated",
    ):
        create_command.distribution_path(first_app_config)


def test_verify(create_command, monkeypatch):
    """If you're on macOS, you can verify tools."""
    create_command.tools.host_os = "Darwin"

    mock_ensure_xcode_is_installed = MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.Xcode,
        "ensure_xcode_is_installed",
        mock_ensure_xcode_is_installed,
    )
    mock_ensure_command_line_tools_are_installed = MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "ensure_command_line_tools_are_installed",
        mock_ensure_command_line_tools_are_installed,
    )
    mock_confirm_xcode_license_accepted = MagicMock()
    monkeypatch.setattr(
        briefcase.integrations.xcode.XcodeCliTools,
        "confirm_xcode_license_accepted",
        mock_confirm_xcode_license_accepted,
    )

    create_command.verify_tools()

    assert create_command.tools.xcode_cli is not None
    mock_ensure_xcode_is_installed.assert_called_once_with(
        tools=create_command.tools,
        min_version=(13, 0, 0),
    )
    mock_ensure_command_line_tools_are_installed.assert_called_once_with(
        tools=create_command.tools
    )
    mock_confirm_xcode_license_accepted.assert_called_once_with(
        tools=create_command.tools
    )
