import os
import subprocess
from unittest import mock
from unittest.mock import MagicMock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.macOS.app import macOSAppPackageCommand


@pytest.fixture
def package_command(tmp_path):
    command = macOSAppPackageCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)

    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    return command


@pytest.fixture
def first_app_dmg(tmp_path):
    dmg_path = tmp_path / "base_path" / "macOS" / "First App.dmg"
    dmg_path.parent.mkdir(parents=True)
    with dmg_path.open("w") as f:
        f.write("DMG content here")

    return dmg_path


def test_notarize_app(package_command, first_app_with_binaries, tmp_path):
    """An app can be notarized."""
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    archive_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "archive.zip"
    )
    package_command.notarize(app_path, team_id="DEADBEEF")

    # As a result of mocking os.unlink, the zip archive won't be
    # cleaned up, so we can test for its existence, but also
    # verify that it *would* have been deleted.
    assert archive_path.exists()
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit *archive* for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(archive_path),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Staple the result to the *app*
            mock.call(
                [
                    "xcrun",
                    "stapler",
                    "staple",
                    os.fsdecode(app_path),
                ],
                check=True,
            ),
        ]
    )


def test_notarize_dmg(package_command, first_app_dmg):
    """A DMG can be notarized."""

    package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Staple the result
            mock.call(
                [
                    "xcrun",
                    "stapler",
                    "staple",
                    os.fsdecode(first_app_dmg),
                ],
                check=True,
            ),
        ]
    )


def test_notarize_unknown_format(package_command, tmp_path):
    """Attempting to notarize a file of unknown format raises an error."""
    pkg_path = tmp_path / "base_path" / "macOS" / "First App.pkg"

    # The notarization call will fail with an error
    with pytest.raises(
        RuntimeError,
        match=r"Don't know how to notarize a file of type .pkg",
    ):
        package_command.notarize(pkg_path, team_id="DEADBEEF")


def test_notarize_dmg_unknown_credentials(package_command, first_app_dmg):
    """When notarizing a DMG, if credentials haven't been stored, the user will
    be prompted to store them."""
    # Set up subprocess to fail on the first notarization attempt
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        None,  # Successful credential storage
        None,  # Successful notarization
        None,  # Successful stapling
    ]

    package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Store credentials in the keychain
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "store-credentials",
                    "--team-id",
                    "DEADBEEF",
                    "briefcase-macOS-DEADBEEF",
                ],
                check=True,
            ),
            # Submit for notarization a second time
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Staple the result
            mock.call(
                [
                    "xcrun",
                    "stapler",
                    "staple",
                    os.fsdecode(first_app_dmg),
                ],
                check=True,
            ),
        ]
    )


def test_credential_storage_failure_app(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """When submitting an app, if credentials haven't been stored, and storage
    fails, an error is raised."""
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    archive_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "archive.zip"
    )

    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xcrun", "notarytool", "store-credentials"],
        ),  # Credential verification failed
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to store credentials for team ID DEADBEEF.",
    ):
        package_command.notarize(app_path, team_id="DEADBEEF")

    # As a result of mocking os.unlink, the zip archive won't be
    # cleaned up, so we can test for its existence, but also
    # verify that it *would* have been deleted.
    assert archive_path.exists()
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(archive_path),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Store credentials in the keychain
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "store-credentials",
                    "--team-id",
                    "DEADBEEF",
                    "briefcase-macOS-DEADBEEF",
                ],
                check=True,
            ),
        ]
    )


def test_credential_storage_failure_dmg(package_command, first_app_dmg):
    """If credentials haven't been stored, and storage fails, an error is
    raised."""
    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xcrun", "notarytool", "store-credentials"],
        ),  # Credential verification failed
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to store credentials for team ID DEADBEEF.",
    ):
        package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Store credentials in the keychain
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "store-credentials",
                    "--team-id",
                    "DEADBEEF",
                    "briefcase-macOS-DEADBEEF",
                ],
                check=True,
            ),
        ]
    )


def test_credential_storage_disabled_input_app(
    package_command, first_app_with_binaries, tmp_path
):
    """When packaging an app, if credentials haven't been stored, and input is
    disabled, an error is raised."""
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    archive_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "archive.zip"
    )

    # Set up subprocess to fail on the first notarization attempt.
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]
    # Disable console input
    package_command.tools.input.enabled = False

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The keychain does not contain credentials for the profile briefcase-macOS-DEADBEEF.",
    ):
        package_command.notarize(app_path, team_id="DEADBEEF")

    # As a result of mocking os.unlink, the zip archive won't be
    # cleaned up, so we can test for its existence, but also
    # verify that it *would* have been deleted.
    assert archive_path.exists()
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(archive_path),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
        ]
    )


def test_credential_storage_disabled_input_dmg(package_command, first_app_dmg):
    """When packaging a DMG, if credentials haven't been stored, and input is
    disabled, an error is raised."""
    # Set up subprocess to fail on the first notarization attempt.
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]
    # Disable console input
    package_command.tools.input.enabled = False

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The keychain does not contain credentials for the profile briefcase-macOS-DEADBEEF.",
    ):
        package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
        ]
    )


def test_notarize_unknown_credentials_after_storage(package_command, first_app_dmg):
    """If we get a credential failure after an attempt to store, an error is
    raised."""
    # Set up subprocess to fail on the second notarization attempt
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        None,  # Successful credential storage
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # A second unknown credential failure
        None,  # Successful stapling
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit macOS[/\\]First App.dmg for notarization.",
    ):
        package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Store credentials in the keychain
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "store-credentials",
                    "--team-id",
                    "DEADBEEF",
                    "briefcase-macOS-DEADBEEF",
                ],
                check=True,
            ),
            # Submit for notarization a second time
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
        ]
    )


def test_app_notarization_failure_with_credentials(
    package_command,
    first_app_with_binaries,
    tmp_path,
):
    """If the notarization process for an app fails for a reason other than
    credentials, an error is raised."""
    app_path = tmp_path / "base_path" / "macOS" / "app" / "First App" / "First App.app"
    archive_path = (
        tmp_path / "base_path" / "macOS" / "app" / "First App" / "archive.zip"
    )

    # Set up subprocess to fail on the first notarization attempt
    # for a reason other than credentials
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Notarization failure; error code 42 is a fake value
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit macOS[/\\]app[/\\]First App[/\\]First App.app for notarization.",
    ):
        package_command.notarize(app_path, team_id="DEADBEEF")

    # As a result of mocking os.unlink, the zip archive won't be
    # cleaned up, so we can test for its existence, but also
    # verify that it *would* have been deleted.
    assert archive_path.exists()
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(archive_path),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
        ]
    )


def test_dmg_notarization_failure_with_credentials(package_command, first_app_dmg):
    """If the notarization process for a DMG fails for a reason other than
    credentials, an error is raised."""
    # Set up subprocess to fail on the first notarization attempt
    # for a reason other than credentials
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Notarization failure; error code 42 is a fake value
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit macOS[/\\]First App.dmg for notarization.",
    ):
        package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
        ]
    )


def test_stapling_failure(package_command, first_app_dmg):
    """If the stapling process fails, an error is raised."""
    # Set up a failure in the stapling process
    package_command.tools.subprocess.run.side_effect = [
        None,
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "stapler"],
        ),  # Stapling failure; error code 42 is a fake value
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to staple notarization onto macOS[/\\]First App.dmg",
    ):
        package_command.notarize(first_app_dmg, team_id="DEADBEEF")

    # The DMG didn't require an archive file, so unlink wasn't invoked.
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.run.assert_has_calls(
        [
            # Submit for notarization
            mock.call(
                [
                    "xcrun",
                    "notarytool",
                    "submit",
                    os.fsdecode(first_app_dmg),
                    "--keychain-profile",
                    "briefcase-macOS-DEADBEEF",
                    "--wait",
                ],
                check=True,
            ),
            # Staple the result
            mock.call(
                [
                    "xcrun",
                    "stapler",
                    "staple",
                    os.fsdecode(first_app_dmg),
                ],
                check=True,
            ),
        ]
    )
