from subprocess import CalledProcessError
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.wix import WiX
from briefcase.platforms.windows.app import WindowsAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = WindowsAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command.tools.wix = WiX(command.tools, wix_home=tmp_path / "wix")
    return command


def test_package_formats(package_command):
    "Packaging formats are as expected"
    assert package_command.packaging_formats == ["msi"]
    assert package_command.default_packaging_format == "msi"


def test_verify(package_command):
    """Verifying on Windows creates a WiX wrapper."""

    package_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    package_command.verify_tools()

    # No error, and an SDK wrapper is created
    assert isinstance(package_command.tools.wix, WiX)


def test_package_msi(package_command, first_app_config, tmp_path):
    """A Windows app can be packaged as an MSI."""

    package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix" / "bin" / "heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "windows" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
    ]


def test_package_msi_failed_manifest(package_command, first_app_config, tmp_path):
    """An error is raised if a manifest cannot be built."""
    # Mock a failure in the call to heat.exe
    package_command.tools.subprocess.run.side_effect = [
        CalledProcessError(cmd=["heat.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to generate manifest for app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix" / "bin" / "heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
    ]


def test_package_msi_failed_compile(package_command, first_app_config, tmp_path):
    """An error is raised if compilation failed."""
    # Mock a failure in the call to candle.exe
    package_command.tools.subprocess.run.side_effect = [
        None,  # heat.exe
        CalledProcessError(cmd=["candle.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to compile app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix" / "bin" / "heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
    ]


def test_package_msi_failed_link(package_command, first_app_config, tmp_path):
    """An error is raised if linking fails."""
    # Mock a failure in the call to light.exe
    package_command.tools.subprocess.run.side_effect = [
        None,  # heat.exe
        None,  # candle.exe
        CalledProcessError(cmd=["link.exe"], returncode=1),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to link app first-app.",
    ):
        package_command.package_app(first_app_config)

    assert package_command.tools.subprocess.run.mock_calls == [
        # Collect manifest
        mock.call(
            [
                tmp_path / "wix" / "bin" / "heat.exe",
                "dir",
                "src",
                "-nologo",
                "-gg",
                "-sfrag",
                "-sreg",
                "-srd",
                "-scom",
                "-dr",
                "first_app_ROOTDIR",
                "-cg",
                "first_app_COMPONENTS",
                "-var",
                "var.SourceDir",
                "-out",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "candle.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-arch",
                "x64",
                "-dSourceDir=src",
                "first-app.wxs",
                "first-app-manifest.wxs",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
        # Link MSI
        mock.call(
            [
                tmp_path / "wix" / "bin" / "light.exe",
                "-nologo",
                "-ext",
                "WixUtilExtension",
                "-ext",
                "WixUIExtension",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path" / "windows" / "First App-0.0.1.msi",
                "first-app.wixobj",
                "first-app-manifest.wixobj",
            ],
            check=True,
            cwd=tmp_path / "base_path" / "windows" / "app" / "First App",
        ),
    ]
