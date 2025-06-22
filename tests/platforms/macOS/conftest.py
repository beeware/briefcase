from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.console import Console
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppMixin, macOSCreateMixin
from tests.utils import DummyConsole, create_file, create_plist_file


class DummyInstallCommand(macOSAppMixin, macOSCreateMixin, BaseCommand):
    """A dummy command to expose package installation capabilities."""

    command = "install"

    def __init__(self, base_path, **kwargs):
        kwargs.setdefault("console", Console())
        super().__init__(base_path=base_path / "base_path", **kwargs)
        self.tools.console = DummyConsole()


@pytest.fixture
def dummy_command(tmp_path):
    cmd = DummyInstallCommand(base_path=tmp_path)

    cmd.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    return cmd


@pytest.fixture
def first_app_templated(first_app_config, tmp_path):
    app_path = tmp_path / "base_path/build/first-app/macos/app/First App.app"

    # Create the briefcase.toml file
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/briefcase.toml",
        """
[briefcase]
target_version = "0.3.20"

[paths]
app_packages_path="First App.app/Contents/Resources/app_packages"
support_path="First App.app/Contents/Frameworks"
runtime_path="Python.xcframework/macos-arm64_x86_64/Python.framework"
info_plist_path="First App.app/Contents/Info.plist"
entitlements_path="Entitlements.plist"
""",
    )

    # Create the plist file for the app
    create_plist_file(
        app_path / "Contents/Info.plist",
        {
            "MainModule": "first_app",
        },
    )

    # Create the entitlements file for the app
    create_plist_file(
        tmp_path / "base_path/build/first-app/macos/app/Entitlements.plist",
        {
            "com.apple.security.cs.allow-unsigned-executable-memory": True,
            "com.apple.security.cs.disable-library-validation": True,
        },
    )

    # Create some folders that need to exist.
    (app_path / "Contents/Resources/app_packages").mkdir(parents=True)
    (app_path / "Contents/Frameworks").mkdir(parents=True)

    # Create an installer Distribution.xml
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/installer/Distribution.xml",
        """<?xml?>\n<installer-script></installer-script>""",
    )

    # Create the support package VERSIONS file
    # with a deliberately weird min macOS version
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/support/VERSIONS",
        "\n".join(
            [
                "Python version: 3.10.15",
                "Build: b11",
                "Min macOS version: 10.12",
                "",
            ]
        ),
    )

    # Select dmg packaging by default
    first_app_config.packaging_format = "dmg"

    return first_app_config
