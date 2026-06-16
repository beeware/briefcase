import os
import subprocess
import uuid
from unittest import mock
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError, NotarizationInterrupted
from briefcase.integrations.subprocess import Subprocess, json_parser
from briefcase.platforms.macOS.app import macOSAppPackageCommand

try:
    import tomllib
except ImportError:  # pragma: no-cover-if-gte-py311
    import tomli as tomllib  # type: ignore[no-redef]


@pytest.fixture
def package_command(dummy_console, tmp_path):
    command = macOSAppPackageCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.os = MagicMock(spec_set=os)

    command.tools.subprocess = MagicMock(spec_set=Subprocess)

    return command


@pytest.fixture
def first_app_zip(first_app_with_binaries, tmp_path):
    first_app_with_binaries.packaging_format = "zip"

    return first_app_with_binaries


@pytest.fixture
def first_app_dmg(first_app_with_binaries, tmp_path):
    first_app_with_binaries.packaging_format = "dmg"

    dmg_path = tmp_path / "base_path/dist/First App.dmg"
    dmg_path.parent.mkdir(parents=True)
    with dmg_path.open("w", encoding="utf-8") as f:
        f.write("DMG content here")

    return first_app_with_binaries


@pytest.fixture
def first_app_pkg(first_app_with_binaries, tmp_path):
    first_app_with_binaries.packaging_format = "pkg"

    dmg_path = tmp_path / "base_path/dist/First App-0.0.1.pkg"
    dmg_path.parent.mkdir(parents=True)
    with dmg_path.open("w", encoding="utf-8") as f:
        f.write("PKG content here")

    return first_app_with_binaries


@pytest.mark.parametrize(
    ("packaging_format", "needs_archive", "needs_installer"),
    [
        ("zip", True, False),
        ("dmg", False, False),
        ("pkg", False, True),
    ],
)
def test_notarize(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    sleep_zero,
    packaging_format,
    needs_archive,
    needs_installer,
):
    """A package can be notarized across different formats."""
    first_app_with_binaries.packaging_format = packaging_format

    app_path = tmp_path / "base_path/build/first-app/macos/app/First App.app"
    archive_path = tmp_path / "base_path/build/first-app/macos/app/First App.app.zip"
    dist_path = tmp_path / "base_path/dist" / f"First App-0.0.1.{packaging_format}"
    if packaging_format == "zip":
        dist_path = tmp_path / "base_path/dist/First App-0.0.1.app.zip"

    if not needs_archive:
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_text("distribution file", encoding="utf-8")

    package_command.ditto_archive = MagicMock()

    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        {"id": submission_id},
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        {"status": "Accepted"},
    ]

    notarize_kwargs = {"identity": sekrit_identity}
    if needs_installer:
        notarize_kwargs["installer_identity"] = sekrit_installer_identity
    package_command.notarize(first_app_with_binaries, **notarize_kwargs)

    if needs_archive:
        assert package_command.ditto_archive.mock_calls == [
            mock.call(app_path, archive_path),
            mock.call(
                app_path,
                tmp_path / "base_path/dist/First App-0.0.1.app.zip",
            ),
        ]
        package_command.tools.os.unlink.assert_called_with(archive_path)
    else:
        package_command.ditto_archive.assert_not_called()
        package_command.tools.os.unlink.assert_not_called()

    submit_path = archive_path if needs_archive else dist_path
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                submit_path,
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
    ]

    staple_path = app_path if needs_archive else dist_path
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            staple_path,
        ],
        check=True,
    )

    marker_suffix = (
        "First App-0.0.1.app.zip.notarization-request"
        if packaging_format == "zip"
        else f"First App-0.0.1.{packaging_format}.notarization-request"
    )
    marker_path = tmp_path / "base_path" / "dist" / marker_suffix
    assert not marker_path.exists(), (
        "Marker should have been deleted after successful notarization"
    )


def test_notarize_unknown_credentials(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """When notarizing, if credentials haven't been stored, the user will be prompted to
    store them."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        # notarytool submit success
        {"id": submission_id},
        # notarytool log; 2 failures, then a successful result.
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        {"status": "Accepted"},
    ]

    package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Submit dmg for notarization; this attempt will fail
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        # Submit dmg for notarization; this attempt succeeds
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        # Check status 3 times
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
    ]

    assert package_command.tools.subprocess.run.mock_calls == [
        # Submit credentials
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
            stream_output=False,
        ),
        # Staple credentials
        mock.call(
            [
                "xcrun",
                "stapler",
                "staple",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
            ],
            check=True,
        ),
    ]


def test_credential_storage_failure_app(
    package_command,
    first_app_zip,
    sekrit_identity,
    tmp_path,
):
    """When submitting an app, if credentials haven't been stored, and storage fails, an
    error is raised."""
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    archive_path = tmp_path / "base_path/build/first-app/macos/app/First App.app.zip"

    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]

    package_command.tools.subprocess.run.side_effect = [
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
        package_command.notarize(first_app_zip, identity=sekrit_identity)

    # As a result of mocking ditto, the zip archive won't *actually* be created;
    # and as a result of mocking os, it won't *actually* be deleted either - but we can
    # verify that it *would* have been deleted.
    package_command.ditto_archive.assert_called_once_with(app_path, archive_path)
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    # Submit *archive* for notarization
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            archive_path,
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # Store credentials in the keychain
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "notarytool",
            "store-credentials",
            "--team-id",
            "DEADBEEF",
            "briefcase-macOS-DEADBEEF",
        ],
        check=True,
        stream_output=False,
    )


def test_credential_storage_failure_dmg(
    package_command,
    first_app_dmg,
    sekrit_identity,
    tmp_path,
):
    """If credentials haven't been stored, and storage fails, an error is raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]

    package_command.tools.subprocess.run.side_effect = [
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
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    # Submit *archive* for notarization
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            tmp_path / "base_path/dist/First App-0.0.1.dmg",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # Store credentials in the keychain
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "notarytool",
            "store-credentials",
            "--team-id",
            "DEADBEEF",
            "briefcase-macOS-DEADBEEF",
        ],
        check=True,
        stream_output=False,
    )


def test_credential_storage_disabled_input_app(
    package_command,
    first_app_zip,
    sekrit_identity,
    tmp_path,
):
    """When packaging an app, if credentials haven't been stored, and input is disabled,
    an error is raised."""
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    archive_path = tmp_path / "base_path/build/first-app/macos/app/First App.app.zip"

    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]

    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xcrun", "notarytool", "store-credentials"],
        ),  # Credential verification failed
    ]

    # Disable console input
    package_command.tools.console.input_enabled = False

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The keychain does not contain credentials for the profile briefcase-macOS-DEADBEEF.",
    ):
        package_command.notarize(first_app_zip, identity=sekrit_identity)

    # As a result of mocking ditto, the zip archive won't *actually* be created;
    # and as a result of mocking os, it won't *actually* be deleted either - but we can
    # verify that it *would* have been deleted.
    package_command.ditto_archive.assert_called_once_with(app_path, archive_path)
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    # Submit *archive* for notarization
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            archive_path,
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # No call is made to store credentials on the keychain
    package_command.tools.subprocess.run.assert_not_called()


def test_credential_storage_disabled_input_dmg(
    package_command,
    first_app_dmg,
    sekrit_identity,
    tmp_path,
):
    """When packaging a DMG, if credentials haven't been stored, and input is disabled,
    an error is raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt,
    # then fail on the storage of credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]

    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["xcrun", "notarytool", "store-credentials"],
        ),  # Credential verification failed
    ]

    # Disable console input
    package_command.tools.console.input_enabled = False

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"The keychain does not contain credentials for the profile briefcase-macOS-DEADBEEF.",
    ):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    # Submit *archive* for notarization
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            tmp_path / "base_path/dist/First App-0.0.1.dmg",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # No attempt was made to store credentials in the keychain
    package_command.tools.subprocess.run.assert_not_called()


def test_notarize_unknown_credentials_after_storage(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """If we get a credential failure after an attempt to store, an error is raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to succeed on storing credentials, but fail on the second
    # notarization attempt
    package_command.tools.subprocess.parse_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Unknown credential failure
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit dist[/\\]First App-0.0.1.dmg for notarization.",
    ):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    # Submit for notarization twice
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
    ]

    # Store credentials in the keychain
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "notarytool",
            "store-credentials",
            "--team-id",
            "DEADBEEF",
            "briefcase-macOS-DEADBEEF",
        ],
        check=True,
        stream_output=False,
    )


def test_app_submit_notarization_failure_with_credentials(
    package_command,
    first_app_zip,
    sekrit_identity,
    tmp_path,
):
    """If the notarization process for an app fails for a reason other than credentials,
    an error is raised."""
    app_path = (
        tmp_path
        / "base_path"
        / "build"
        / "first-app"
        / "macos"
        / "app"
        / "First App.app"
    )
    archive_path = tmp_path / "base_path/build/first-app/macos/app/First App.app.zip"

    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt
    # for a reason other than credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Notarization failure; error code 42 is a fake value
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit build[/\\]first-app[/\\]macos[/\\]app[/\\]First App.app for notarization.",
    ):
        package_command.notarize(first_app_zip, identity=sekrit_identity)

    # As a result of mocking ditto, the zip archive won't *actually* be created;
    # and as a result of mocking os, it won't *actually* be deleted either - but we can
    # verify that it *would* have been deleted.
    package_command.ditto_archive.assert_called_once_with(app_path, archive_path)
    package_command.tools.os.unlink.assert_called_with(archive_path)

    # The calls to notarize were made
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            archive_path,
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # No calls to submit credentials
    package_command.tools.subprocess.run.assert_not_called()


def test_dmg_submit_notarization_failure_with_credentials(
    package_command,
    first_app_dmg,
    sekrit_identity,
    tmp_path,
):
    """If the notarization process for a DMG fails for a reason other than credentials,
    an error is raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Set up subprocess to fail on the first notarization attempt
    # for a reason other than credentials
    package_command.tools.subprocess.parse_output.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "notarytool", "submit"],
        ),  # Notarization failure; error code 42 is a fake value
    ]

    # The notarization call will fail with an error
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to submit dist[/\\]First App-0.0.1.dmg for notarization.",
    ):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarize were made
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "submit",
            tmp_path / "base_path/dist/First App-0.0.1.dmg",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
        quiet=1,
    )

    # No calls to submit credentials
    package_command.tools.subprocess.run.assert_not_called()


def test_unknown_notarization_status_failure(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """If the notarization log process fails with an unexpected status code, an error is
    raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit
        {"id": submission_id},
        # notarytool log; a failure with an unknown status code.
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "notarytool", "log"],
        ),
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unknown problem retrieving notarization status.",
    ):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Submit dmg for notarization
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        # One attempt to check status is made
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
    ]

    # No staple attempt is made.
    package_command.tools.subprocess.run.assert_not_called()


def test_stapling_failure(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """If the stapling process fails, an error is raised."""
    # Mock the creation of the ditto archive
    package_command.ditto_archive = MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit
        {"id": submission_id},
        # notarytool log; 2 failures, then a successful result.
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        {"status": "Accepted"},
    ]

    # Set up a failure in the stapling process
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "stapler"],
        ),  # Stapling failure; error code 42 is a fake value
    ]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to staple notarization onto dist[/\\]First App-0.0.1.dmg",
    ):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    # The DMG didn't require an archive file, so ditto and unlink weren't invoked.
    package_command.ditto_archive.assert_not_called()
    package_command.tools.os.unlink.assert_not_called()

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Submit dmg for notarization
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        # Check status 3 times
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
    ]

    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            tmp_path / "base_path/dist/First App-0.0.1.dmg",
        ],
        check=True,
    )


def test_interrupt_notarization(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
    capsys,
):
    """If notarization is interrupted, the submission ID is output for the user."""
    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool submit
        {"id": submission_id},
        # notarytool log; 2 failures, then a keyboard interrupt
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        KeyboardInterrupt,
    ]

    with pytest.raises(NotarizationInterrupted):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    assert "rerunning the same briefcase package" in capsys.readouterr().out

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Submit dmg for notarization
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "submit",
                tmp_path / "base_path/dist/First App-0.0.1.dmg",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
            quiet=1,
        ),
        # Check status 3 times
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "log",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                submission_id,
            ],
            quiet=1,
        ),
    ]

    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    assert marker_path.exists()

    with marker_path.open("rb") as f:
        data = tomllib.load(f)

    assert data["identity"] == sekrit_identity.id
    assert data["submission_id"] == submission_id

    # No stapling occurred
    package_command.tools.subprocess.run.assert_not_called()


def test_notarize_interrupt_leaves_marker(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """If notarization is interrupted by the user, the marker file is left in place."""
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        {"id": submission_id},
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        KeyboardInterrupt,
    ]

    with pytest.raises(NotarizationInterrupted):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    assert marker_path.exists()

    with marker_path.open("rb") as f:
        data = tomllib.load(f)

    assert data["identity"] == sekrit_identity.id
    assert data["submission_id"] == submission_id


def test_notarize_staple_failure_leaves_marker(
    package_command,
    first_app_dmg,
    sekrit_identity,
    sleep_zero,
    tmp_path,
):
    """If stapling fails, the marker file is left in place."""
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        {"id": submission_id},
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        {"status": "Accepted"},
    ]
    package_command.tools.subprocess.run.side_effect = [
        subprocess.CalledProcessError(
            returncode=42,
            cmd=["xcrun", "stapler"],
        ),
    ]

    with pytest.raises(BriefcaseCommandError, match=r"Unable to staple"):
        package_command.notarize(first_app_dmg, identity=sekrit_identity)

    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    assert marker_path.exists()

    with marker_path.open("rb") as f:
        data = tomllib.load(f)

    assert data["identity"] == sekrit_identity.id
    assert data["submission_id"] == submission_id


@pytest.mark.parametrize(
    ("packaging_format", "expected_suffix"),
    [
        ("zip", "First App-0.0.1.app.zip.notarization-request"),
        ("dmg", "First App-0.0.1.dmg.notarization-request"),
        ("pkg", "First App-0.0.1.pkg.notarization-request"),
    ],
)
def test_notarization_request_path(
    package_command,
    first_app_with_binaries,
    tmp_path,
    packaging_format,
    expected_suffix,
):
    """Notarization request marker path is computed correctly for each format."""
    first_app_with_binaries.packaging_format = packaging_format
    path = package_command.notarization_request_path(first_app_with_binaries)
    assert path == tmp_path / "base_path" / "dist" / expected_suffix


@pytest.mark.parametrize("packaging_format", ["dmg", "pkg"])
def test_write_notarization_request(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    packaging_format,
):
    """Notarization request marker is written with correct content."""
    first_app_with_binaries.packaging_format = packaging_format

    submission_id = str(uuid.uuid4())
    kwargs = {
        "identity": sekrit_identity,
        "submission_id": submission_id,
    }
    if packaging_format == "pkg":
        kwargs["installer_identity"] = sekrit_installer_identity

    package_command.write_notarization_request(
        first_app_with_binaries,
        **kwargs,
    )

    expected_path = (
        tmp_path
        / "base_path"
        / "dist"
        / f"First App-0.0.1.{packaging_format}.notarization-request"
    )
    assert expected_path.exists()

    with expected_path.open("rb") as f:
        data = tomllib.load(f)

    assert data["identity"] == sekrit_identity.id
    assert data["submission_id"] == submission_id
    if packaging_format == "pkg":
        assert data["installer_identity"] == sekrit_installer_identity.id
    else:
        assert "installer_identity" not in data


def test_read_notarization_request(
    package_command,
    first_app_dmg,
    tmp_path,
):
    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        'identity = "CAFEBEEF"\n'
        'submission_id = "00000000-0000-0000-0000-000000000000"\n',
        encoding="utf-8",
    )

    data = package_command.read_notarization_request(first_app_dmg)
    assert data == {
        "identity": "CAFEBEEF",
        "submission_id": "00000000-0000-0000-0000-000000000000",
    }


def test_read_notarization_request_with_installer(
    package_command,
    first_app_pkg,
    tmp_path,
):
    marker_path = tmp_path / "base_path/dist/First App-0.0.1.pkg.notarization-request"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        'identity = "CAFEBEEF"\n'
        'submission_id = "00000000-0000-0000-0000-000000000000"\n'
        'installer_identity = "CAFEFACE"\n',
        encoding="utf-8",
    )

    data = package_command.read_notarization_request(first_app_pkg)
    assert data == {
        "identity": "CAFEBEEF",
        "submission_id": "00000000-0000-0000-0000-000000000000",
        "installer_identity": "CAFEFACE",
    }


def test_read_notarization_request_missing_file(
    package_command,
    first_app_dmg,
    tmp_path,
):
    with pytest.raises(BriefcaseCommandError, match=r"does not exist"):
        package_command.read_notarization_request(first_app_dmg)


def test_read_notarization_request_malformed_toml(
    package_command,
    first_app_dmg,
    tmp_path,
):
    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("this is not valid toml = {{", encoding="utf-8")

    with pytest.raises(BriefcaseCommandError, match=r"malformed"):
        package_command.read_notarization_request(first_app_dmg)


def test_read_notarization_request_missing_identity(
    package_command,
    first_app_dmg,
    tmp_path,
):
    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        'submission_id = "00000000-0000-0000-0000-000000000000"\n', encoding="utf-8"
    )

    with pytest.raises(BriefcaseCommandError, match=r"identity"):
        package_command.read_notarization_request(first_app_dmg)


def test_read_notarization_request_missing_submission_id(
    package_command,
    first_app_dmg,
    tmp_path,
):
    marker_path = tmp_path / "base_path/dist/First App-0.0.1.dmg.notarization-request"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text('identity = "CAFEBEEF"\n', encoding="utf-8")

    with pytest.raises(BriefcaseCommandError, match=r"submission_id"):
        package_command.read_notarization_request(first_app_dmg)
