# The package command inherits most of its behavior from the common base
# implementation. Do a surface-level verification here, but the app
# tests provide the actual test coverage.
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.wix import WiX
from briefcase.platforms.windows.visualstudio import WindowsVisualStudioPackageCommand

from ....integrations.wix.conftest import WIX_EXE_PATH, WIX_UI_PATH


@pytest.fixture
def package_command(tmp_path):
    command = WindowsVisualStudioPackageCommand(
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

    assert package_command.tools.subprocess.run.mock_calls == [
        # Compile MSI
        mock.call(
            [
                tmp_path / "wix" / WIX_EXE_PATH,
                "build",
                "-ext",
                tmp_path / "wix" / WIX_UI_PATH,
                "-arch",
                "x64",
                "first-app.wxs",
                "-loc",
                "unicode.wxl",
                "-o",
                tmp_path / "base_path/dist/First App-0.0.1.msi",
            ],
            check=True,
            cwd=tmp_path / "base_path/build/first-app/windows/visualstudio",
        ),
    ]
