from unittest import mock

import pytest

from briefcase.console import Console, Log
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


def test_package_msi(package_command, first_app_config, tmp_path):
    """A Windows app can be packaged as an MSI."""

    package_command.package_app(first_app_config)

    package_command.tools.subprocess.run.assert_has_calls(
        [
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
    )
