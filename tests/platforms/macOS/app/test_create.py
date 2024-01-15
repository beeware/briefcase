import subprocess
import sys
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppCreateCommand

from ....utils import create_file, create_installed_package, mock_tgz_download


@pytest.fixture
def create_command(tmp_path, first_app_templated):
    command = macOSAppCreateCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )

    # mock subprocess app context for this app
    command.tools[first_app_templated].app_context = mock.MagicMock(spec_set=Subprocess)

    return command


@pytest.mark.parametrize(
    "permissions, info, entitlements, context",
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
        # Camera permissions
        (
            {
                "camera": "I need to see you",
            },
            {},
            {},
            {
                "info": {},
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
                "info": {},
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
                "info": {},
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


@pytest.mark.parametrize(
    "host_arch, other_arch",
    [
        ("arm64", "x86_64"),
        ("arm64", "x86_64"),
    ],
)
def test_install_app_packages(
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

    create_command.install_app_requirements(first_app_templated, test_mode=False)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / f"app_packages.{host_arch}",
        universal_suffix="_universal2",
    )

    # A request was made to install requirements
    assert create_command.tools[first_app_templated].app_context.run.mock_calls == [
        # First call is to install the initial packages on the host arch
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / ('app_packages.' + host_arch)}",
                "first",
                "second==1.2.3",
                "third>=3.2.1",
            ],
            check=True,
            encoding="UTF-8",
        ),
        # Second call installs the binary packages for the other architecture.
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / ('app_packages.' + other_arch)}",
                "--no-deps",
                "--only-binary",
                ":all:",
                "second==1.2.3",
                "third==3.4.5",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(
                    bundle_path / "support/platform-site" / f"macosx.{other_arch}"
                )
            },
        ),
    ]

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


@pytest.mark.parametrize(
    "host_arch, other_arch",
    [
        ("arm64", "x86_64"),
        ("arm64", "x86_64"),
    ],
)
def test_install_app_packages_no_binary(
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

    create_command.install_app_requirements(first_app_templated, test_mode=False)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / f"app_packages.{host_arch}",
        universal_suffix="_universal2",
    )

    # A request was made to install requirements
    assert create_command.tools[first_app_templated].app_context.run.mock_calls == [
        # Only call is to install the initial packages on the host arch
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / ('app_packages.' + host_arch)}",
                "first",
                "second==1.2.3",
                "third>=3.2.1",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

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


def test_install_app_packages_failure(create_command, first_app_templated, tmp_path):
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
    create_command.tools[first_app_templated].app_context.run.side_effect = [
        None,
        subprocess.CalledProcessError(returncode=1, cmd="pip"),
    ]

    # Install the requirements; this will raise an error
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Unable to install requirements\. This may be because one of your\n"
            r"requirements is invalid, or because pip was unable to connect\n"
            r"to the PyPI server.\n"
        ),
    ):
        create_command.install_app_requirements(first_app_templated, test_mode=False)

    # We looked for binary packages in the host app_packages
    create_command.find_binary_packages.assert_called_once_with(
        bundle_path / "app_packages.arm64",
        universal_suffix="_universal2",
    )

    # A request was made to install requirements
    assert create_command.tools[first_app_templated].app_context.run.mock_calls == [
        # First call is to install the initial packages on the host arch
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.arm64'}",
                "first",
                "second==1.2.3",
                "third>=3.2.1",
            ],
            check=True,
            encoding="UTF-8",
        ),
        # Second call installs the binary packages for the other architecture;
        # this is the call that failed.
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'app_packages.x86_64'}",
                "--no-deps",
                "--only-binary",
                ":all:",
                "second==1.2.3",
                "third==3.4.5",
            ],
            check=True,
            encoding="UTF-8",
            env={
                "PYTHONPATH": str(bundle_path / "support/platform-site/macosx.x86_64")
            },
        ),
    ]

    # The app packages folder for the other architecture has been created, even though
    # it isn't needed. The existence of the target and host versions is validated as a
    # result of the underlying install/merge methods.
    assert (bundle_path / "app_packages.x86_64").is_dir()

    # We didn't attempt to thin or  merge, because we didn't complete installing.
    create_command.thin_app_packages.assert_not_called()
    create_command.merge_app_packages.assert_not_called()


@pytest.mark.parametrize(
    "host_arch, other_arch",
    [
        ("arm64", "x86_64"),
        ("arm64", "x86_64"),
    ],
)
def test_install_app_packages_non_universal(
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

    create_command.install_app_requirements(first_app_templated, test_mode=False)

    # We didn't search for binary packages
    create_command.find_binary_packages.assert_not_called()

    # One request was made to install requirements
    assert create_command.tools[first_app_templated].app_context.run.mock_calls == [
        mock.call(
            [
                sys.executable,
                "-u",
                "-X",
                "utf8",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-python-version-warning",
                "--upgrade",
                "--no-user",
                f"--target={bundle_path / 'First App.app' / 'Contents' / 'Resources' / 'app_packages'}",
                "first",
                "second==1.2.3",
                "third>=3.2.1",
            ],
            check=True,
            encoding="UTF-8",
        ),
    ]

    # An attempt was made to thin the app packages
    create_command.thin_app_packages.assert_called_once_with(
        bundle_path / "First App.app/Contents/Resources/app_packages",
        arch=host_arch,
    )

    # No attempt was made to merge packages.
    create_command.merge_app_packages.assert_not_called()


@pytest.mark.parametrize("universal_build", [True, False])
@pytest.mark.parametrize("pre_existing", [True, False])
def test_install_support_package(
    create_command,
    first_app_templated,
    tmp_path,
    pre_existing,
    universal_build,
):
    """The standard library is copied out of the support package into the app bundle."""
    # Hard code the support revision
    first_app_templated.support_revision = "37"

    first_app_templated.universal_build = universal_build

    create_command.tools.host_arch = "gothic"

    # Mock the thin command so we can confirm if it was invoked.
    create_command.ensure_thin_binary = mock.Mock()

    bundle_path = tmp_path / "base_path/build/first-app/macos/app"
    runtime_support_path = bundle_path / "First App.app/Contents/Resources/support"

    if pre_existing:
        create_file(
            runtime_support_path / "python-stdlib/old-stdlib",
            "Legacy stdlib file",
        )

    # Mock download.file to return a support package
    create_command.tools.download.file = mock.MagicMock(
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

    # Only thin if this is a non-universal app
    if universal_build:
        create_command.ensure_thin_binary.assert_not_called()
    else:
        create_command.ensure_thin_binary.assert_called_once_with(
            bundle_path / "First App.app/Contents/MacOS/First App",
            arch="gothic",
        )
