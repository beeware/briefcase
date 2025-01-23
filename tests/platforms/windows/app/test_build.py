import re
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest
import tomli_w

import briefcase.platforms.windows.app
from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.rcedit import RCEdit
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.windows_sdk import WindowsSDK
from briefcase.platforms.windows.app import WindowsAppBuildCommand

from ....utils import create_file


@pytest.fixture
def build_command(tmp_path):
    command = WindowsAppBuildCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.host_os = "Windows"
    command.tools.host_arch = "AMD64"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.shutil = mock.MagicMock(spec_set=shutil)
    command.tools.file.download = mock.MagicMock()
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

    mock_rcedit_verify = mock.MagicMock(wraps=RCEdit.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.app.RCEdit,
        "verify",
        mock_rcedit_verify,
    )

    build_command.verify_tools()

    # RCEdit tool was verified
    mock_rcedit_verify.assert_called_once_with(tools=build_command.tools)
    assert isinstance(build_command.tools.rcedit, RCEdit)
    # Windows SDK tool not created
    assert not hasattr(build_command.tools, "windows_sdk")


def test_verify_with_windows_sdk(build_command, windows_sdk, monkeypatch):
    """Verifying on Windows creates an RCEdit and Windows SDK wrapper."""
    build_command.tools.windows_sdk = windows_sdk

    mock_windows_sdk_verify = mock.MagicMock(wraps=WindowsSDK.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.app.WindowsSDK,
        "verify",
        mock_windows_sdk_verify,
    )

    mock_rcedit_verify = mock.MagicMock(wraps=RCEdit.verify)
    monkeypatch.setattr(
        briefcase.platforms.windows.app.RCEdit,
        "verify",
        mock_rcedit_verify,
    )

    build_command.verify_tools()

    # RCEdit tool was verified
    mock_rcedit_verify.assert_called_once_with(tools=build_command.tools)
    assert isinstance(build_command.tools.rcedit, RCEdit)
    # WindowsSDK tool was verified
    mock_windows_sdk_verify.assert_called_once_with(tools=build_command.tools)
    assert isinstance(build_command.tools.windows_sdk, WindowsSDK)


@pytest.mark.parametrize("pre_existing", [True, False])
@pytest.mark.parametrize("console_app", [True, False])
def test_build_app_without_windows_sdk(
    build_command,
    first_app_templated,
    pre_existing,
    console_app,
    tmp_path,
):
    """The stub binary will be updated when a Windows app is built."""
    first_app_templated.console_app = console_app

    exec_path = tmp_path / "base_path/build/first-app/windows/app/src"
    if pre_existing:
        # If this is a pre-existing app, the stub has already been renamed
        if console_app:
            (exec_path / "Stub.exe").rename(exec_path / "first-app.exe")
        else:
            (exec_path / "Stub.exe").rename(exec_path / "First App.exe")

    build_command.build_app(first_app_templated)

    # The stub binary has been renamed
    assert not (exec_path / "Stub.exe").is_file()
    if console_app:
        assert (exec_path / "first-app.exe").is_file()
    else:
        assert (exec_path / "First App.exe").is_file()

    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase/tools/rcedit-x64.exe",
            Path("src/first-app.exe") if console_app else Path("src/First App.exe"),
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
            "first-app.exe" if console_app else "First App.exe",
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
        cwd=tmp_path / "base_path/build/first-app/windows/app",
    )


@pytest.mark.parametrize("console_app", [True, False])
def test_build_app_with_windows_sdk(
    build_command,
    windows_sdk,
    first_app_templated,
    console_app,
    tmp_path,
):
    """The stub binary will be updated when a Windows app is built."""
    build_command.tools.windows_sdk = windows_sdk
    first_app_templated.console_app = console_app

    build_command.build_app(first_app_templated)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk/bin/86.1.1/x64/signtool.exe",
            "remove",
            "-s",
            Path("src/first-app.exe") if console_app else Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path/build/first-app/windows/app",
        quiet=1,
    )
    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase/tools/rcedit-x64.exe",
            Path("src/first-app.exe") if console_app else Path("src/First App.exe"),
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
            "first-app.exe" if console_app else "First App.exe",
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
        cwd=tmp_path / "base_path/build/first-app/windows/app",
    )


def test_build_app_without_any_digital_signatures(
    build_command,
    windows_sdk,
    first_app_templated,
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

    build_command.build_app(first_app_templated)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk/bin/86.1.1/x64/signtool.exe",
            "remove",
            "-s",
            Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path/build/first-app/windows/app",
        quiet=1,
    )
    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase/tools/rcedit-x64.exe",
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
        cwd=tmp_path / "base_path/build/first-app/windows/app",
    )


def test_build_app_error_remove_signature(
    build_command,
    windows_sdk,
    first_app_templated,
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
        build_command.build_app(first_app_templated)

    # remove any digital signatures on the app binary
    build_command.tools.subprocess.check_output.assert_called_once_with(
        [
            tmp_path / "win_sdk/bin/86.1.1/x64/signtool.exe",
            "remove",
            "-s",
            Path("src/First App.exe"),
        ],
        cwd=tmp_path / "base_path/build/first-app/windows/app",
        quiet=1,
    )
    # update the app binary resources not called
    build_command.tools.subprocess.run.assert_not_called()


def test_build_app_failure(build_command, first_app_templated):
    """If the stub binary cannot be updated, an error is raised."""

    build_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="rcedit-x64.exe",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to update details on stub app for first-app.",
    ):
        build_command.build_app(first_app_templated)


def test_build_app_with_support_package_update(
    build_command,
    first_app_templated,
    tmp_path,
    windows_sdk,
    capsys,
):
    """If a support package update is performed, the user is warned."""

    # To trigger the app package update logic, we need to invoke the full build
    # command, and fake being on a verified Windows install with a generated
    # app.
    build_command.tools.host_os = "Windows"
    build_command.tools.windows_sdk = windows_sdk

    # Hard code a support revision so that the download support package is fixed
    first_app_templated.support_revision = "1"

    # Fake the existence of some source files.
    create_file(
        tmp_path / "base_path/src/first_app/app.py",
        "print('an app')",
    )

    # Populate a briefcase.toml that mirrors a real Windows app
    with (build_command.bundle_path(first_app_templated) / "briefcase.toml").open(
        "wb"
    ) as f:
        index = {
            "paths": {
                "app_path": "src/app",
                "app_package_path": "src/app_packages",
                "support_path": "src",
            }
        }
        tomli_w.dump(index, f)

    # Build the app with a support package update
    build_command(first_app_templated, update_support=True)

    # update the app binary resources
    build_command.tools.subprocess.run.assert_called_once_with(
        [
            tmp_path / "briefcase/tools/rcedit-x64.exe",
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
        cwd=tmp_path / "base_path/build/first-app/windows/app",
    )

    # No attempt was made to clean up the support package.
    build_command.tools.shutil.rmtree.assert_not_called()

    # The user was warned that support package update may not work.
    assert "WARNING: Support package update may be imperfect" in capsys.readouterr().out
