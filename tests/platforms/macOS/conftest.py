from pathlib import Path
from unittest import mock

import pytest

from briefcase.commands.base import BaseCommand
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import (
    macOSAppMixin,
    macOSCreateMixin,
    macOSMixin,
    macOSPackageMixin,
)
from tests.utils import create_file, create_plist_file


class DummyInstallCommand(macOSAppMixin, macOSCreateMixin, BaseCommand):
    """A dummy command to expose package installation capabilities."""

    command = "install"

    def __init__(self, base_path, **kwargs):
        super().__init__(base_path=base_path / "base_path", **kwargs)


@pytest.fixture
def dummy_command(dummy_console, tmp_path):
    cmd = DummyInstallCommand(
        console=dummy_console,
        base_path=tmp_path,
    )

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

    # Create the XCframework Info.plist file, with a deliberately weird min macOS version
    create_plist_file(
        (
            tmp_path
            / "base_path/build/first-app/macos/app/support/Python.xcframework"
            / "macos-arm64_x86_64/Python.framework/Resources/Info.plist"
        ),
        {
            "CFBundleVersion": "3.10.15",
            "MinimumOSVersion": "10.12",
        },
    )

    # Select dmg packaging by default
    first_app_config.packaging_format = "dmg"

    return first_app_config


class _DummyPathsCmd(macOSPackageMixin, macOSMixin, BaseCommand):
    """Concrete-enough command to exercise notarization_path()/distribution_path()."""

    command = "package"

    def __init__(self, base_path: Path, **kwargs):
        super().__init__(base_path=base_path / "base_path", **kwargs)
        # Ensure dist_path exists; distribution_path() uses it.
        self.dist_path = self.base_path / "dist"
        self.dist_path.mkdir(parents=True, exist_ok=True)

    # Used by notarization_path() when packaging_format == "zip"
    def package_path(self, app):
        return self.base_path / f"build/{app.app_name}/macos/app/{app.formal_name}.app"

    # Satisfy abstract requirement; not used by these tests.
    def binary_path(self, app):
        # Could be the app bundle itself or a plausible binary path.
        return self.package_path(app)  # or: / "Contents/MacOS" / app.formal_name


@pytest.fixture
def paths_cmd(dummy_console, tmp_path):
    return _DummyPathsCmd(console=dummy_console, base_path=tmp_path)
