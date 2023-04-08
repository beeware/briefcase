import re
import subprocess
from pathlib import Path
from unittest import mock

import pytest

import briefcase.platforms.windows.app
from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.platforms.windows.app import WindowsAppBuildCommand


@pytest.fixture
def build_command(tmp_path):
    command = WindowsAppBuildCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.rcedit = RCEdit(command.tools)
    return command


@pytest.fixture
def windows_sdk(build_command, tmp_path):
    return WindowsSDK(
        tools=build_command.tools,
        root_path=tmp_path / "win_sdk",
        version="86.1.1",
        arch="x64",
    )


def test_verify_without_windows_sdk(build_command, monkeypatch):
    """Verifying on Windows creates an RCEdit wrapper."""
    mock_sdk = mock.MagicMock(spec_set=WindowsSDK)
    monkeypatch.setattr(briefcase.platforms.windows.app, "WindowsSDK", mock_sdk)
    mock_sdk.verify.side_effect = BriefcaseCommandError("Windows SDK")

    build_command.verify_tools()

    # No error and an SDK wrapper is created
    assert isinstance(build_command.tools.rcedit, RCEdit)
    # Windows SDK tool not created
    assert not hasattr(build_command.tools, "windows_sdk")


def test_verify_with_windows_sdk(build_command, windows_sdk, tmp_path):
    """Verifying on Windows creates an RCEdit and Windows SDK wrapper."""
    build_command.tools.windows_sdk = windows_sdk

    build_command.verify_tools()

    # No error and SDK wrappers are created
    assert isinstance(build_command.tools.rcedit, RCEdit)
    assert isinstance(build_command.tools.windows_sdk, WindowsSDK)


def test_build_app_without_windows_sdk(build_command, first_app_config, tmp_path):
    """The stub binary will be updated when a Windows app is built."""
    build_command.build_app(first_app_config)

    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase" / "tools" / "rcedit-x64.exe",
            Path("src/First App.exe"),
            "--set-version-string",
            "CompanyName",
            "Megacorp",
            "--set-version-string",
            "FileDescription",
            "First App",
            "--set-version-string",
            "FileVersion",
            "0.0.1",
            "--set-version-string",
            "InternalName",
            "first_app",
            "--set-version-string",
            "OriginalFilename",
            "First App.exe",
            "--set-version-string",
            "ProductName",
            "First App",
            "--set-version-string",
            "ProductVersion",
            "0.0.1",
            "--set-icon",
            "icon.ico",
        ],
        check=True,
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )


def test_build_app_with_windows_sdk(
    build_command,
    windows_sdk,
    first_app_config,
    tmp_path,
):
    """The stub binary will be updated when a Windows app is built."""
    build_command.tools.windows_sdk = windows_sdk

    build_command.build_app(first_app_config)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk" / "bin" / "86.1.1" / "x64" / "signtool.exe",
            "remove",
            "-s",
            Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )
    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase" / "tools" / "rcedit-x64.exe",
            Path("src/First App.exe"),
            "--set-version-string",
            "CompanyName",
            "Megacorp",
            "--set-version-string",
            "FileDescription",
            "First App",
            "--set-version-string",
            "FileVersion",
            "0.0.1",
            "--set-version-string",
            "InternalName",
            "first_app",
            "--set-version-string",
            "OriginalFilename",
            "First App.exe",
            "--set-version-string",
            "ProductName",
            "First App",
            "--set-version-string",
            "ProductVersion",
            "0.0.1",
            "--set-icon",
            "icon.ico",
        ],
        check=True,
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )


def test_build_app_without_any_digital_signatures(
    build_command,
    windows_sdk,
    first_app_config,
    tmp_path,
):
    """If the app binary is not already signed, then attempt to remove signatures fails
    but app build succeeds."""
    build_command.tools.windows_sdk = windows_sdk

    build_command.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="signtool.exe remove -s app.exe",
        output="""
    Number of errors: 1
    SignTool Error: CryptSIPRemoveSignedDataMsg returned error: 0x00000057
            The parameter is incorrect.
""",
    )

    build_command.build_app(first_app_config)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk" / "bin" / "86.1.1" / "x64" / "signtool.exe",
            "remove",
            "-s",
            Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )
    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase" / "tools" / "rcedit-x64.exe",
            Path("src/First App.exe"),
            "--set-version-string",
            "CompanyName",
            "Megacorp",
            "--set-version-string",
            "FileDescription",
            "First App",
            "--set-version-string",
            "FileVersion",
            "0.0.1",
            "--set-version-string",
            "InternalName",
            "first_app",
            "--set-version-string",
            "OriginalFilename",
            "First App.exe",
            "--set-version-string",
            "ProductName",
            "First App",
            "--set-version-string",
            "ProductVersion",
            "0.0.1",
            "--set-icon",
            "icon.ico",
        ],
        check=True,
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )


def test_build_app_error_remove_signature(
    build_command,
    windows_sdk,
    first_app_config,
    tmp_path,
):
    """If the attempt to remove any exist digital signatures fails because signtool
    raises an unexpected error, then the build fails."""
    build_command.tools.windows_sdk = windows_sdk

    build_command.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="signtool.exe remove /s filepath",
        output="""
    Number of errors: 1
    Unknown and unexpected error
""",
    )

    error_message = (
        "Failed to remove any existing digital signatures from the stub app.\n"
        "\n"
        "Recreating the app layout may also help resolve this issue:\n"
        "\n"
        "    $ briefcase create windows app\n"
        "\n"
    )
    with pytest.raises(BriefcaseCommandError, match=re.escape(error_message)):
        build_command.build_app(first_app_config)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk" / "bin" / "86.1.1" / "x64" / "signtool.exe",
            "remove",
            "-s",
            Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path" / "build" / "first-app" / "windows" / "app",
    )
    # update the app binary resources not called
    build_command.tools.subprocess.run.assert_not_called()


def test_build_app_failure(build_command, first_app_config, tmp_path):
    """If the stub binary cannot be updated, an error is raised."""

    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="rcedit-x64.exe",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to update details on stub app for first-app.",
    ):
        build_command.build_app(first_app_config)
