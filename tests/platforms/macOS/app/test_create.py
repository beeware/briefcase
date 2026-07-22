import json
import os
import shutil
import sys
import time
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError, RequirementsInstallError
from briefcase.integrations.virtual_environment import VenvVirtualEnvironment
from briefcase.platforms.macOS.app import macOSAppCreateCommand

from ....utils import (
    create_file,
    create_installed_package,
    create_plist_file,
    mock_tgz_download,
)


@pytest.fixture
def create_command(dummy_console, mock_other_venv, tmp_path, first_app_templated):
    command = macOSAppCreateCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    command.generate_template = mock.MagicMock()
    command.verify_not_on_icloud = mock.MagicMock()
    command.create_app_environment = mock.MagicMock(return_value=mock_other_venv)
    command.tools.sys = mock.MagicMock(spec_set=sys)
    command.tools.sys.version_info = (3, "X", 0)

    return command


@pytest.mark.parametrize(
    ("permissions", "info", "entitlements", "context"),
    [
        # No permissions
        (
            {},
            {},
            {},
            {
                "info": {},
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                },
            },
        ),
        # Only custom permissions
        (
            {},
            {
                "NSCustomPermission": "Custom message",
            },
            {
                "com.apple.vm.networking": True,
            },
            {
                "info": {
                    "NSCustomPermission": "Custom message",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.vm.networking": True,
                },
            },
        ),
        # Bluetooth permissions
        (
            {
                "bluetooth": "I need to connect to bluetooth device.",
            },
            {},
            {},
            {
                "info": {
                    "NSBluetoothAlwaysUsageDescription": "I need to connect to bluetooth device."
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.device.bluetooth": True,
                },
            },
        ),
        # Camera permissions
        (
            {
                "camera": "I need to see you",
            },
            {},
            {},
            {
                "info": {
                    "NSCameraUsageDescription": "I need to see you",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.device.camera": True,
                },
            },
        ),
        # Microphone permissions
        (
            {
                "microphone": "I need to hear you",
            },
            {},
            {},
            {
                "info": {
                    "NSMicrophoneUsageDescription": "I need to hear you",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.device.microphone": True,
                },
            },
        ),
        # Coarse location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I need to know roughly where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Fine location permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I need to know exactly where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Background location permissions
        (
            {
                "background_location": "I always need to know where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I always need to know where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Coarse location background permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I always need to know where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Fine location background permissions
        (
            {
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I always need to know where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Coarse and fine location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I need to know exactly where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Coarse and fine background location permissions
        (
            {
                "coarse_location": "I need to know roughly where you are",
                "fine_location": "I need to know exactly where you are",
                "background_location": "I always need to know where you are",
            },
            {},
            {},
            {
                "info": {
                    "NSLocationUsageDescription": "I always need to know where you are",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.location": True,
                },
            },
        ),
        # Photo library permissions
        (
            {
                "photo_library": "I need to see your library",
            },
            {},
            {},
            {
                "info": {
                    "NSPhotoLibraryUsageDescription": "I need to see your library",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": True,
                    "com.apple.security.personal-information.photo_library": True,
                },
            },
        ),
        # Override and augment by cross-platform definitions
        (
            {
                "fine_location": "I need to know where you are",
            },
            {
                "NSCustomMessage": "Custom message",
                "NSLocationUsageDescription": "Platform specific",
            },
            {
                "com.apple.security.personal-information.location": False,
                "com.apple.security.cs.disable-library-validation": False,
                "com.apple.vm.networking": True,
            },
            {
                "info": {
                    "NSLocationUsageDescription": "Platform specific",
                    "NSCustomMessage": "Custom message",
                },
                "entitlements": {
                    "com.apple.security.cs.allow-unsigned-executable-memory": True,
                    "com.apple.security.cs.disable-library-validation": False,
                    "com.apple.security.personal-information.location": False,
                    "com.apple.vm.networking": True,
                },
            },
        ),
    ],
)
def test_permissions_context(
    create_command, first_app, permissions, info, entitlements, context
):
    """Platform-specific permissions can be added to the context."""
    # Set the permission, info and entitlement values
    first_app.permission = permissions
    first_app.info = info
    first_app.entitlement = entitlements
    # Extract the cross-platform permissions
    x_permissions = create_command._x_permissions(first_app)
    # Check that the final platform permissions are rendered as expected.
    assert context == create_command.permissions_context(first_app, x_permissions)


def test_generate_app_template(create_command, first_app, tmp_path):
    """After the app is generated, the location is checked for iCloud markers."""
    create_command.generate_app_template(first_app)

    # The template was generated. Check some basic details, but not the full context.
    create_command.generate_template.assert_called_once_with(
        template="https://github.com/beeware/briefcase-macOS-app-template.git",
        branch=None,
        output_path=tmp_path / "base_path/build/first-app/macos",
        extra_context=mock.ANY,
    )

    # iCloud was verified, with cleanup.
    create_command.verify_not_on_icloud.assert_called_once_with(first_app, cleanup=True)


def test_universal_managed_python(monkeypatch, create_command, first_app):
    """If the app is universal but the environment manages python, an error is
    raised."""
    # Mock a universal app with an environment that provides Python
    monkeypatch.setattr(VenvVirtualEnvironment, "provides_python", True)
    first_app.universal_build = True

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Briefcase doesn't support creating universal apps "
            r"when the environment provides the Python library"
        ),
    ):
        create_command.verify_app(first_app)


def test_x86_64_managed_python(monkeypatch, create_command, first_app):
    """If the app is x86-64 but the environment manages python, an error is raised."""
    # Mock a universal app with an environment that provides Python
    monkeypatch.setattr(VenvVirtualEnvironment, "provides_python", True)
    first_app.universal_build = False
    create_command.tools.host_arch = "x86_64"

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Briefcase doesn't support creating x86_64 apps "
            r"when the environment provides the Python library"
        ),
    ):
        create_command.verify_app(first_app)


def test_arm64_managed_python(monkeypatch, create_command, first_app):
    """If the app is arm64 but the environment manages python, it can validate."""
    # Mock a universal app with an environment that provides Python
    monkeypatch.setattr(VenvVirtualEnvironment, "provides_python", True)
    first_app.universal_build = False
    create_command.tools.host_arch = "arm64"

    # Validates without error.
    create_command.verify_app(first_app)


def test_generate_app_template_formal_name_mismatch(
    create_command,
    first_app,
    tmp_path,
):
    """If the app's formal name doesn't match the external package path, an error is
    raised."""
    first_app.external_package_path = "output/Unexpected Name.app"

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"The app bundle referenced by external_package_path \(Unexpected Name.app\)\n"
            r"does not match the formal name of the app \('First App'\)."
        ),
    ):
        create_command.verify_app(first_app)


def test_install_app_resources(create_command, first_app_templated, tmp_path):
    """The app bundle's modification time is updated when app resources are
    installed."""
    # Get the initial app modification time
    initial_timestamp = os.path.getmtime(
        create_command.binary_path(first_app_templated)
    )

    # Add a small sleep to make sure that a touch will definitely result in an updated
    # modification time
    time.sleep(0.1)

    # Install resources
    create_command.install_app_resources(first_app_templated)

    # Modification time has been updated, and is newer
    assert (
        os.path.getmtime(create_command.binary_path(first_app_templated))
        > initial_timestamp
    )


@pytest.mark.parametrize(
    ("console_app", "provides_python", "revision", "expected_binary"),
    [
        (False, False, "37", "GUI-Stub-3.X-b37.zip"),
        (True, False, "37", "Console-Stub-3.X-b37.zip"),
        (False, True, "42", "GUI-LStub-3.X-b42.zip"),
        (True, True, "42", "Console-LStub-3.X-b42.zip"),
    ],
)
def test_stub_binary_filename(
    monkeypatch,
    create_command,
    first_app_templated,
    console_app,
    provides_python,
    revision,
    expected_binary,
):
    """A valid support package URL is created for a support revision."""
    first_app_templated.console_app = console_app

    # Mock a universal app with an environment that provides Python
    monkeypatch.setattr(VenvVirtualEnvironment, "provides_python", provides_python)

    create_command.tools.sys = mock.MagicMock(spec=sys)
    create_command.tools.sys.version_info = ("3", "X", "Y")

    assert (
        create_command.stub_binary_filename(revision, first_app_templated)
        == expected_binary
    )


@pytest.mark.parametrize(
    ("host_arch", "other_arch"),
    [
        ("arm64", "x86_64"),
        ("x86_64", "arm64"),
    ],
)
def test_install_app_packages(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    tmp_path,
    host_arch,
    other_arch,
):
    """A 2-pass install of app packages is performed."""
    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    create_command.tools.host_arch = host_arch
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Mock the result of finding the binary packages - 2 of the packages are binary;
    # the version on the loosely specified package doesn't match the lower bound.
    create_command.find_binary_packages = mock.Mock(
        return_value=[
            ("second", "1.2.3"),
            ("third", "3.4.5"),
        ]
    )

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / f"app_packages.{host_arch}",
        universal_suffix="_universal2",
        other_suffix=f"_{other_arch}",
    )

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / f"app_packages.{host_arch}",
        install_hint=(
            "\n\n"
            f"This may be because an {host_arch} wheel that is compatible with\n"
            "Python 3.X and a minimum macOS version of 10.12\n"
            "is not available.\n"
        ),
    )
    # A request was made to install requirements on the alternate environment
    mock_other_venv.install_requirements.assert_called_once_with(
        [
            "second==1.2.3",
            "third==3.4.5",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / f"app_packages.{other_arch}",
        install_hint=(
            "\n\n"
            f"This may be because an {other_arch} wheel that is compatible with\n"
            "Python 3.X and a minimum macOS version of 10.12\n"
            "is not available.\n"
            "\n"
            "You may need to build a non-universal app by setting:\n"
            "\n"
            "    universal_build = False\n"
            "\n"
            "in the macOS configuration section of your pyproject.toml.\n"
        ),
    )

    # The app packages folder has been created. The existence of the target and host
    # versions is validated as a result of the underlying install/merge methods.
    assert (bundle_path / f"app_packages.{other_arch}").is_dir()

    # An attempt was made thin the "other" arch packages.
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / f"app_packages.{other_arch}",
        arch=other_arch,
    )

    # An attempt was made to merge packages.
    create_command.merge_app_packages.assert_called_once_with(
        target_app_packages=bundle_path
        / "First App.app"
        / "Contents"
        / "Resources"
        / "app_packages",
        sources=[
            bundle_path / f"app_packages.{host_arch}",
            bundle_path / f"app_packages.{other_arch}",
        ],
    )


@pytest.mark.parametrize("old_config", [True, False])
def test_min_os_version(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    old_config,
    tmp_path,
):
    """If the app specifies a min OS version, it is used for wheel installs."""
    create_command.tools.host_arch = "arm64"

    if old_config:
        # Old support packages didn't contain an XCframework; but they did have a
        # VERSIONS file. Delete the xcframework, and create the support package VERSIONS
        # file with a deliberately weird min macOS version
        shutil.rmtree(
            tmp_path / "base_path/build/first-app/macos/app/support/Python.xcframework"
        )
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

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Set a minimum OS version.
    first_app_templated.min_os_version = "13.2"

    # Mock the result of finding the binary packages - 2 of the packages are binary;
    # the version on the loosely specified package doesn't match the lower bound.
    create_command.find_binary_packages = mock.Mock(
        return_value=[
            ("second", "1.2.3"),
            ("third", "3.4.5"),
        ]
    )

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / "app_packages.arm64",
        universal_suffix="_universal2",
        other_suffix="_x86_64",
    )

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="13.2",
        install_path=bundle_path / "app_packages.arm64",
        install_hint=mock.ANY,
    )
    # A request was made to install requirements on the alternate environment
    mock_other_venv.install_requirements.assert_called_once_with(
        [
            "second==1.2.3",
            "third==3.4.5",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="13.2",
        install_path=bundle_path / "app_packages.x86_64",
        install_hint=mock.ANY,
    )

    # The app packages folder has been created. The existence of the target and host
    # versions is validated as a result of the underlying install/merge methods.
    assert (bundle_path / "app_packages.x86_64").is_dir()

    # An attempt was made thin the "other" arch packages.
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / "app_packages.x86_64",
        arch="x86_64",
    )

    # An attempt was made to merge packages.
    create_command.merge_app_packages.assert_called_once_with(
        target_app_packages=bundle_path
        / "First App.app"
        / "Contents"
        / "Resources"
        / "app_packages",
        sources=[
            bundle_path / "app_packages.arm64",
            bundle_path / "app_packages.x86_64",
        ],
    )


@pytest.mark.parametrize("old_config", [True, False])
def test_default_min_os_version(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    old_config,
    tmp_path,
):
    """If the support package doesn't specify a min OS version, a default is used."""
    create_command.tools.host_arch = "arm64"

    if old_config:
        # Old support packages didn't contain an XCframework; but they did have a
        # VERSIONS file. Delete the xcframework, and create the support package VERSIONS
        # file with *no* min macOS version
        shutil.rmtree(
            tmp_path / "base_path/build/first-app/macos/app/support/Python.xcframework"
        )
        create_file(
            tmp_path / "base_path/build/first-app/macos/app/support/VERSIONS",
            "\n".join(
                [
                    "Python version: 3.10.15",
                    "Build: b11",
                    "",
                ]
            ),
        )
    else:
        # Replace the framework plist file with one without a min OS version.
        framework_plist = (
            tmp_path
            / "base_path/build/first-app/macos/app/support/Python.xcframework"
            / "macos-arm64_x86_64/Python.framework/Resources/Info.plist"
        )
        framework_plist.unlink()
        create_plist_file(
            framework_plist,
            {
                "CFBundleVersion": "3.10.15",
            },
        )

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Mock the result of finding the binary packages - 2 of the packages are binary;
    # the version on the loosely specified package doesn't match the lower bound.
    create_command.find_binary_packages = mock.Mock(
        return_value=[
            ("second", "1.2.3"),
            ("third", "3.4.5"),
        ]
    )

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / "app_packages.arm64",
        universal_suffix="_universal2",
        other_suffix="_x86_64",
    )

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="11.0",
        install_path=bundle_path / "app_packages.arm64",
        install_hint=mock.ANY,
    )
    # A request was made to install requirements on the alternate environment
    mock_other_venv.install_requirements.assert_called_once_with(
        [
            "second==1.2.3",
            "third==3.4.5",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="11.0",
        install_path=bundle_path / "app_packages.x86_64",
        install_hint=mock.ANY,
    )

    # The app packages folder has been created. The existence of the target and host
    # versions is validated as a result of the underlying install/merge methods.
    assert (bundle_path / "app_packages.x86_64").is_dir()

    # An attempt was made thin the "other" arch packages.
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / "app_packages.x86_64",
        arch="x86_64",
    )

    # An attempt was made to merge packages.
    create_command.merge_app_packages.assert_called_once_with(
        target_app_packages=bundle_path
        / "First App.app"
        / "Contents"
        / "Resources"
        / "app_packages",
        sources=[
            bundle_path / "app_packages.arm64",
            bundle_path / "app_packages.x86_64",
        ],
    )


def test_invalid_min_os_version(mock_venv, create_command, first_app_templated):
    """If the app defines a min OS version that is incompatible with the support
    package, an error is raised."""
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Set a min OS version that is incompatible with the support package.
    first_app_templated.min_os_version = "10.6"

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Your macOS app specifies a minimum macOS version of 10.6, "
            r"but the support package only supports 10.12"
        ),
    ):
        create_command.install_app_requirements(first_app_templated, mock_venv)

    # No request was made to install requirements
    mock_venv.install_requirements.assert_not_called()


def test_min_os_version_python_provided(
    mock_venv,
    create_command,
    first_app_templated,
    tmp_path,
):
    """If the environment provides Python, the min OS version can be extracted."""
    create_command.tools.host_arch = "arm64"

    # Mock a venv that provides python
    mock_venv.provides_python = True
    create_file(
        tmp_path / "mock_venvs/mock-venv/conda-meta/python-3.X.json",
        json.dumps(
            {
                "name": "python",
                "version": "3.14.6",
                "depends": [
                    "__osx >=12.1",
                    "bzip2 >=1.0.8,<2.0a0",
                    "libexpat >=2.8.1,<3.0a0",
                ],
            }
        ),
    )

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Configure a non-universal app with requirements.
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    first_app_templated.universal_build = False

    # Mock the find_binary_packages so we can confirm it was not invoked.
    create_command.find_binary_packages = mock.Mock()

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was not invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="12.1",
        install_path=bundle_path / "First App.app/Contents/Resources/app_packages",
        install_hint=mock.ANY,
    )

    # We didn't try to find binary packages
    create_command.find_binary_packages.assert_not_called()

    # An attempt was made thin the "other" arch packages.
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / "First App.app/Contents/Resources/app_packages",
        arch="arm64",
    )

    # An attempt was made to merge packages.
    create_command.merge_app_packages.assert_not_called()


def test_no_python_env_metadata(mock_venv, create_command, first_app_templated):
    """If the environment doesn't provide metadata an error is raised."""
    create_command.tools.host_arch = "arm64"

    # Mock a venv that provides python, but no Python metadata file.
    mock_venv.provides_python = True

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to find Python environment configuration file.",
    ):
        create_command.install_app_requirements(first_app_templated, mock_venv)


def test_invalid_python_env_metadata(
    mock_venv,
    create_command,
    first_app_templated,
    tmp_path,
):
    """If the environment provides unparsable metadata an error is raised."""
    create_command.tools.host_arch = "arm64"

    # Mock a venv that provides python
    mock_venv.provides_python = True
    create_file(
        tmp_path / "mock_venvs/mock-venv/conda-meta/python-3.X.json",
        "Not a valid metadata file",
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to parse Python environment configuration file.",
    ):
        create_command.install_app_requirements(first_app_templated, mock_venv)


def test_incomplete_python_env_metadata(
    mock_venv,
    create_command,
    first_app_templated,
    tmp_path,
):
    """If the environment provides unparsable metadata an error is raised."""
    create_command.tools.host_arch = "arm64"

    # Mock a venv that provides python, and Python environment metadata
    # that doesn't specify a minimum macOS version
    mock_venv.provides_python = True
    create_file(
        tmp_path / "mock_venvs/mock-venv/conda-meta/python-3.X.json",
        json.dumps(
            {
                "name": "python",
                "version": "3.14.6",
                "depends": [
                    "bzip2 >=1.0.8,<2.0a0",
                    "libexpat >=2.8.1,<3.0a0",
                ],
            }
        ),
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Could not extract minimum macOS version "
            r"from Python environment metadata."
        ),
    ):
        create_command.install_app_requirements(first_app_templated, mock_venv)


@pytest.mark.parametrize(
    ("host_arch", "other_arch"),
    [
        ("arm64", "x86_64"),
    ],
)
def test_install_app_packages_no_binary(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    tmp_path,
    host_arch,
    other_arch,
):
    """If there's no binaries in the first pass, the second pass isn't performed."""
    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create pre-existing other-arch content
    create_installed_package(bundle_path / f"app_packages.{other_arch}", "legacy")

    create_command.tools.host_arch = host_arch
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Mock the result of finding no binary packages.
    create_command.find_binary_packages = mock.Mock(return_value=[])

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / f"app_packages.{host_arch}",
        universal_suffix="_universal2",
        other_suffix=f"_{other_arch}",
    )

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / "app_packages.arm64",
        install_hint=mock.ANY,
    )
    # No binary packages means no install request on the other venv.
    create_command.create_app_environment.assert_not_called()
    mock_other_venv.install_requirements.assert_not_called()

    # The app packages folder for the other architecture has been created, even though
    # it isn't needed. The existence of the target and host versions is validated as a
    # result of the underlying install/merge methods.
    assert (bundle_path / f"app_packages.{other_arch}").is_dir()

    # We still need to thin and merge the app packages; this is effectively just a copy.
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / f"app_packages.{other_arch}",
        arch=other_arch,
    )
    create_command.merge_app_packages.assert_called_once_with(
        target_app_packages=bundle_path
        / "First App.app"
        / "Contents"
        / "Resources"
        / "app_packages",
        sources=[
            bundle_path / f"app_packages.{host_arch}",
            bundle_path / f"app_packages.{other_arch}",
        ],
    )


def test_install_app_packages_failure(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    tmp_path,
):
    """If the install of other-arch binaries fails, an exception is raised."""
    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    # Create pre-existing other-arch content
    create_installed_package(bundle_path / "app_packages.x86_64", "legacy")

    create_command.tools.host_arch = "arm64"
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]

    # Mock the result of finding the binary packages - 2 of the packages are binary;
    # the version on the loosely specified package doesn't match the lower bound.
    create_command.find_binary_packages = mock.Mock(
        return_value=[
            ("second", "1.2.3"),
            ("third", "3.4.5"),
        ]
    )

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it was invoked.
    create_command.merge_app_packages = mock.Mock()

    # Mock a failure on the second install
    mock_other_venv.install_requirements.side_effect = RequirementsInstallError()

    # Install the requirements; this will raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Unable to install requirements\. This may be because one of your\n"
            r"requirements is invalid, or because pip was unable to connect\n"
            r"to the PyPI server.\n"
        ),
    ):
        create_command.install_app_requirements(first_app_templated, mock_venv)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / "app_packages.arm64",
        universal_suffix="_universal2",
        other_suffix="_x86_64",
    )

    # A request was made to install requirements on the host arch
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / "app_packages.arm64",
        install_hint=mock.ANY,
    )
    # A request was made to install requirements on the alternate environment
    mock_other_venv.install_requirements.assert_called_once_with(
        [
            "second==1.2.3",
            "third==3.4.5",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / "app_packages.x86_64",
        install_hint=mock.ANY,
    )

    # The app packages folder for the other architecture has been created, even though
    # it isn't needed. The existence of the target and host versions is validated as a
    # result of the underlying install/merge methods.
    assert (bundle_path / "app_packages.x86_64").is_dir()

    # We didn't attempt to thin or  merge, because we didn't complete installing.
    create_command.thin_app_packages.assert_not_called()
    create_command.merge_app_packages.assert_not_called()


@pytest.mark.parametrize(
    ("host_arch", "other_arch"),
    [
        ("arm64", "x86_64"),
    ],
)
def test_install_app_packages_non_universal(
    mock_venv,
    mock_other_venv,
    create_command,
    first_app_templated,
    tmp_path,
    host_arch,
    other_arch,
):
    """If the app is non-universal, only a single install pass occurs, followed by
    thinning."""
    bundle_path = tmp_path / "base_path/build/first-app/macos/app"

    create_command.tools.host_arch = host_arch
    first_app_templated.requires = ["first", "second==1.2.3", "third>=3.2.1"]
    first_app_templated.universal_build = False

    # Mock the find_binary_packages command so we can confirm it wasn't invoked.
    create_command.find_binary_packages = mock.Mock()

    # Mock the thin command so we can confirm it was invoked.
    create_command.thin_app_packages = mock.Mock()

    # Mock the merge command so we can confirm it wasn't invoked.
    create_command.merge_app_packages = mock.Mock()

    create_command.install_app_requirements(first_app_templated, mock_venv)

    # We didn't search for binary packages
    create_command.find_binary_packages.assert_not_called()

    # A request was made to install requirements on the host arch,
    # directly into the final install location.
    mock_venv.install_requirements.assert_called_once_with(
        [
            "first",
            "second==1.2.3",
            "third>=3.2.1",
        ],
        allow_editable=False,
        require_binary=True,
        min_os_version="10.12",
        install_path=bundle_path / "First App.app/Contents/Resources/app_packages",
        install_hint=mock.ANY,
    )
    # No request was made to create an other environment, or install packages.
    create_command.create_app_environment.assert_not_called()
    mock_other_venv.install_requirements.assert_not_called()

    # An attempt was made to thin the app packages
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / "First App.app/Contents/Resources/app_packages",
        arch=host_arch,
    )

    # No attempt was made to merge packages.
    create_command.merge_app_packages.assert_not_called()


@pytest.mark.parametrize("pre_existing", [True, False])
def test_install_legacy_support_package(
    create_command,
    first_app_templated,
    tmp_path,
    pre_existing,
):
    """The legacy location for the standard library is used by default when installing
    the support package."""
    # Hard code the support revision
    first_app_templated.support_revision = "37"

    # Rewrite the app's briefcase.toml to use the legacy paths (i.e.,
    # a support path of Resources/support, and no stdlib_path)
    create_file(
        tmp_path / "base_path/build/first-app/macos/app/briefcase.toml",
        """
[paths]
app_packages_path="First App.app/Contents/Resources/app_packages"
support_path="First App.app/Contents/Resources/support"
info_plist_path="First App.app/Contents/Info.plist"
entitlements_path="Entitlements.plist"
""",
    )

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"
    runtime_support_path = bundle_path / "First App.app/Contents/Resources/support"

    if pre_existing:
        create_file(
            runtime_support_path / "python-stdlib/old-stdlib",
            "old stdlib file",
        )

    # Mock download.file to return a support package
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_tgz_download(
            f"Python-3.{sys.version_info.minor}-macOS-support.b37.tar.gz",
            [
                ("python-stdlib/stdlib.txt", "this is the standard library"),
                (
                    "platform-site/macosx.arm64/sitecustomize.py",
                    "this is the arm64 platform site",
                ),
                (
                    "platform-site/macosx.x86_64/sitecustomize.py",
                    "this is the x86_64 platform site",
                ),
                ("Python.xcframework/info.plist", "this is the xcframework"),
            ],
        )
    )

    # Install the support package
    create_command.install_app_support_package(first_app_templated)

    # Confirm that the support files have been unpacked into the bundle location
    assert (bundle_path / "support/python-stdlib/stdlib.txt").exists()
    assert (
        bundle_path / "support/platform-site/macosx.arm64/sitecustomize.py"
    ).exists()
    assert (
        bundle_path / "support/platform-site/macosx.x86_64/sitecustomize.py"
    ).exists()
    assert (bundle_path / "support/Python.xcframework/info.plist").exists()

    # The standard library has been copied to the app...
    assert (runtime_support_path / "python-stdlib/stdlib.txt").exists()
    # ... but the other support files have not.
    assert not (
        runtime_support_path / "platform-site/macosx.arm64/sitecustomize.py"
    ).exists()
    assert not (
        runtime_support_path / "platform-site/macosx.x86_64/sitecustomize.py"
    ).exists()
    assert not (runtime_support_path / "Python.xcframework/info.plist").exists()

    # The legacy content has been purged
    assert not (runtime_support_path / "python-stdlib/old-stdlib").exists()


@pytest.mark.parametrize("pre_existing", [True, False])
def test_install_support_package(
    create_command,
    first_app_templated,
    tmp_path,
    pre_existing,
):
    """The Python framework is copied out of the support package into the app bundle."""
    # Hard code the support revision
    first_app_templated.support_revision = "37"

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"
    runtime_support_path = bundle_path / "First App.app/Contents/Frameworks"

    if pre_existing:
        create_file(
            runtime_support_path / "Python.framework/old-Python",
            "Old library",
        )

    # Mock download.file to return a support package
    create_command.tools.file.download = mock.MagicMock(
        side_effect=mock_tgz_download(
            f"Python-3.{sys.version_info.minor}-macOS-support.b37.tar.gz",
            content=[
                (
                    "platform-site/macosx.arm64/sitecustomize.py",
                    "this is the arm64 platform site",
                ),
                (
                    "platform-site/macosx.x86_64/sitecustomize.py",
                    "this is the x86_64 platform site",
                ),
                ("Python.xcframework/Info.plist", "this is the xcframework"),
                (
                    "Python.xcframework/macos-arm64_x86_64/Python.framework/Versions/Current/Python",
                    "this is the library",
                ),
            ],
            links=[
                (
                    "Python.xcframework/macos-arm64_x86_64/Python.framework/Python",
                    "Versions/Current/Python",
                ),
            ],
        )
    )

    # Install the support package
    create_command.install_app_support_package(first_app_templated)

    # Confirm that the support files have been unpacked into the bundle location
    assert (
        bundle_path / "support/platform-site/macosx.arm64/sitecustomize.py"
    ).exists()
    assert (
        bundle_path / "support/platform-site/macosx.x86_64/sitecustomize.py"
    ).exists()
    assert (bundle_path / "support/Python.xcframework/Info.plist").exists()
    assert (
        bundle_path
        / "support/Python.xcframework/macos-arm64_x86_64/Python.framework/Versions/Current/Python"
    ).is_file()
    assert (
        bundle_path
        / "support/Python.xcframework/macos-arm64_x86_64/Python.framework/Python"
    ).is_symlink()

    # The standard library has been copied to the app...
    assert (runtime_support_path / "Python.framework/Versions/Current/Python").is_file()
    assert (runtime_support_path / "Python.framework/Python").is_symlink()
    # ... but the other support files have not.
    assert not (
        runtime_support_path / "platform-site/macosx.arm64/sitecustomize.py"
    ).exists()
    assert not (
        runtime_support_path / "platform-site/macosx.x86_64/sitecustomize.py"
    ).exists()

    # The legacy content has been purged
    assert not (runtime_support_path / "python-stdlib/old-Python").exists()


@pytest.mark.parametrize("reinstall", [True, False])
def test_install_managed_python_env(
    create_command,
    mock_venv,
    first_app_templated,
    reinstall,
    tmp_path,
):
    """A managed python environment will be copied into the final app."""
    # Make the app's template look like a managed environment app
    create_file(
        create_command.bundle_path(first_app_templated) / "briefcase.toml",
        """
[paths]
support_path="First App.app/Contents/Resources/python"
""",
    )

    resource_path = (
        create_command.bundle_path(first_app_templated)
        / "First App.app/Contents/Resources/python"
    )

    if reinstall:
        # Create some pre-existing managed Python content
        create_file(resource_path / "lib/libpython.so", "old Python lib")
        create_file(resource_path / "lib/old.so", "old lib")
        create_file(resource_path / "other/content.txt", "other file")

    # Create some mock content in the virtual environment
    create_file(tmp_path / "mock_venvs/mock-venv/base.txt", "Top level file")
    create_file(tmp_path / "mock_venvs/mock-venv/lib/libpython.so", "Python lib")
    create_file(tmp_path / "mock_venvs/mock-venv/lib/site-packages/test.py", "Stdlib")

    # Install the managed Python environment
    create_command.install_managed_python_env(first_app_templated, mock_venv)

    # The managed environment was copied to the final app.
    # Deep directory structure is preserved.
    assert (resource_path / "base.txt").exists()
    assert (resource_path / "lib/libpython.so").exists()
    assert (resource_path / "lib/site-packages/test.py").exists()

    # Old content no longer exists.
    assert not (resource_path / "lib/old.so").exists()
    assert not (resource_path / "other/content.txt").exists()
