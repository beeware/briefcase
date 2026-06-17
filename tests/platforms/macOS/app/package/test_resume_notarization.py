import shutil
import subprocess
import uuid
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import json_parser

from .....utils import create_file

RESUME_FORMATS = [
    # (packaging_format, submission name in notarytool history, dist artefact, uses an installer identity)
    pytest.param("zip", "First App.app.zip", None, False, id="app"),
    pytest.param("dmg", "First App-0.0.1.dmg", "First App-0.0.1.dmg", False, id="dmg"),
    pytest.param("pkg", "First App-0.0.1.pkg", "First App-0.0.1.pkg", True, id="pkg"),
]


def test_resume_notarize_app(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    sleep_zero,
):
    """Notarization of an app bundle can be resumed."""
    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the creation of the ditto archive
    package_command.ditto_archive = mock.MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App.app.zip",
                    "status": "In Progress",
                },
            ]
        },
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

    # Resume notarizaton. Use the base command's interface to ensure the full cleanup
    # process is tested.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="zip",
        identity=sekrit_identity.id,
        submission_id=submission_id,
    )

    # Identity selection excluded adhoc identities
    package_command.select_identity.assert_called_once_with(
        identity=sekrit_identity.id,
        allow_adhoc=False,
    )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # Notarization is complete; we can staple.
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        check=True,
    )

    # As this is a .zip distribution, there's a finalization step to create the actual
    # distribution artefact with ditto.
    package_command.ditto_archive.assert_called_once_with(
        tmp_path / "base_path/build/first-app/macos/app/First App.app",
        tmp_path / "base_path/dist/First App-0.0.1.app.zip",
    )


def test_resume_notarize_dmg(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    sleep_zero,
):
    """Notarization of a DMG can be resumed."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the creation of the ditto archive
    package_command.ditto_archive = mock.MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App-0.0.1.dmg",
                    "status": "In Progress",
                },
            ]
        },
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

    # Resume notarizaton
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="dmg",
        identity=sekrit_identity.id,
        submission_id=submission_id,
    )

    # Identity selection excluded adhoc identities
    package_command.select_identity.assert_called_once_with(
        identity=sekrit_identity.id,
        allow_adhoc=False,
    )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # Notarization is complete; we can staple.
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            tmp_path / "base_path/dist/First App-0.0.1.dmg",
        ],
        check=True,
    )

    # The distribution artefact already exists, so there's no call to ditto.
    package_command.ditto_archive.assert_not_called()


def test_resume_notarize_pkg(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    sleep_zero,
):
    """Notarization of a PKG installer can be resumed."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.pkg",
        "distribution file",
    )

    # 2 calls are made to determine identity - the app identity, then the installer identity.
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    # Mock the creation of the ditto archive
    package_command.ditto_archive = mock.MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App-0.0.1.pkg",
                    "status": "In Progress",
                },
            ]
        },
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

    # Resume notarizaton
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="pkg",
        identity=sekrit_identity.id,
        installer_identity=sekrit_installer_identity.id,
        submission_id=submission_id,
    )

    # Identity selection excluded adhoc identities, but also confirmed notarization identity
    assert package_command.select_identity.mock_calls == [
        mock.call(
            identity=sekrit_identity.id,
            allow_adhoc=False,
        ),
        mock.call(
            identity=sekrit_installer_identity.id,
            app_identity=sekrit_identity,
        ),
    ]

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # Notarization is complete; we can staple.
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            tmp_path / "base_path/dist/First App-0.0.1.pkg",
        ],
        check=True,
    )

    # The distribution artefact already exists, so there's no call to ditto.
    package_command.ditto_archive.assert_not_called()


@pytest.mark.parametrize(
    ("packaging_format", "submission_name", "dist_artefact", "use_installer"),
    RESUME_FORMATS,
)
def test_resume_notarize_from_marker(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    sleep_zero,
    packaging_format,
    submission_name,
    dist_artefact,
    use_installer,
):
    """An interrupted notarization can be auto-resumed from its marker file."""
    # Set the packaging format, so the marker path can be determined.
    first_app_with_binaries.packaging_format = packaging_format

    # Create a pre-existing distribution artefact. A .zip is built from the app via
    # ditto as part of finalization, so it doesn't need a pre-existing artefact.
    if dist_artefact is not None:
        create_file(
            tmp_path / "base_path/dist" / dist_artefact,
            "distribution file",
        )

    # Mock the creation of the ditto archive (used to finalize a .app.zip distribution).
    package_command.ditto_archive = mock.MagicMock()

    # Select codesigning identities. A PKG needs both an app identity and an installer
    # identity; other formats only need an app identity.
    if use_installer:
        package_command.select_identity.side_effect = [
            sekrit_identity,
            sekrit_installer_identity,
        ]
    else:
        package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": submission_name,
                    "status": "In Progress",
                },
            ]
        },
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

    # Write a notarization request marker, simulating an interrupted notarization.
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id=submission_id,
        installer_identity=sekrit_installer_identity if use_installer else None,
    )
    marker_path = package_command.notarization_request_path(first_app_with_binaries)
    # The marker exists on disk, ready to be auto-detected.
    assert marker_path.exists()

    # Resume notarization. No explicit --resume is provided, so the marker is
    # auto-detected, and the identity/submission ID are read from it.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format=packaging_format,
    )

    # Identity selection excluded adhoc identities; PKG also resolves an installer identity.
    if use_installer:
        assert package_command.select_identity.mock_calls == [
            mock.call(
                identity=sekrit_identity.id,
                allow_adhoc=False,
            ),
            mock.call(
                identity=sekrit_installer_identity.id,
                app_identity=sekrit_identity,
            ),
        ]
    else:
        package_command.select_identity.assert_called_once_with(
            identity=sekrit_identity.id,
            allow_adhoc=False,
        )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # Notarization is complete; stapling occurs on the notarization artefact.
    if packaging_format == "zip":
        staple_path = tmp_path / "base_path/build/first-app/macos/app/First App.app"
    else:
        staple_path = tmp_path / "base_path/dist" / dist_artefact
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            staple_path,
        ],
        check=True,
    )

    # A .zip distribution is finalized by re-creating the archive with ditto; other
    # formats already have their distribution artefact.
    if packaging_format == "zip":
        package_command.ditto_archive.assert_called_once_with(
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
            tmp_path / "base_path/dist/First App-0.0.1.app.zip",
        )
    else:
        package_command.ditto_archive.assert_not_called()

    # Notarization succeeded, so the marker has been cleaned up.
    assert not marker_path.exists()


def test_resume_notarize_from_marker_explicit_identity(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    sleep_zero,
):
    """An interrupted PKG notarization can be resumed when the identity and installer
    identity are provided explicitly and match the marker."""
    first_app_with_binaries.packaging_format = "pkg"
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.pkg",
        "distribution file",
    )
    package_command.select_identity.side_effect = [
        sekrit_identity,
        sekrit_installer_identity,
    ]

    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App-0.0.1.pkg",
                    "status": "In Progress",
                },
            ]
        },
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

    # Write a marker recording the interrupted notarization.
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id=submission_id,
        installer_identity=sekrit_installer_identity,
    )
    marker_path = package_command.notarization_request_path(first_app_with_binaries)

    # Resume, providing the identity and installer identity explicitly. Both match the
    # values in the marker, so notarization proceeds.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="pkg",
        identity=sekrit_identity.id,
        installer_identity=sekrit_installer_identity.id,
    )

    # The explicit identities were used to resume notarization.
    assert package_command.select_identity.mock_calls == [
        mock.call(
            identity=sekrit_identity.id,
            allow_adhoc=False,
        ),
        mock.call(
            identity=sekrit_installer_identity.id,
            app_identity=sekrit_identity,
        ),
    ]

    # Notarization succeeded, so the marker has been cleaned up.
    assert not marker_path.exists()


@pytest.mark.parametrize(
    ("packaging_format", "submission_name", "dist_artefact", "use_installer"),
    RESUME_FORMATS,
)
def test_resume_notarize_from_marker_rejected(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
    packaging_format,
    submission_name,
    dist_artefact,
    use_installer,
):
    """If an auto-resumed notarization (read from the marker) is rejected, an error is
    raised and the marker is retained."""
    # Set the packaging format, so the marker path can be determined.
    first_app_with_binaries.packaging_format = packaging_format

    # Create a pre-existing distribution artefact.
    if dist_artefact is not None:
        create_file(
            tmp_path / "base_path/dist" / dist_artefact,
            "distribution file",
        )

    # Select codesigning identities. A PKG needs both an app identity and an installer
    # identity; other formats only need an app identity.
    if use_installer:
        package_command.select_identity.side_effect = [
            sekrit_identity,
            sekrit_installer_identity,
        ]
    else:
        package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": submission_name,
                    "status": "In Progress",
                },
            ]
        },
        # notarytool log reports a rejection.
        {"status": "Invalid", "statusSummary": "Bad mojo"},
    ]

    # Write a notarization request marker, simulating an interrupted notarization.
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id=submission_id,
        installer_identity=sekrit_installer_identity if use_installer else None,
    )
    marker_path = package_command.notarization_request_path(first_app_with_binaries)
    # The marker exists on disk, ready to be auto-detected.
    assert marker_path.exists()

    # Resume notarization. The marker is auto-detected, but the notarization is rejected.
    with pytest.raises(
        BriefcaseCommandError,
        match=r"Notarization was rejected: Bad mojo",
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format=packaging_format,
        )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
        ),
        # The notarization log reports a rejection.
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

    # Notarization didn't succeed, so the marker is retained for a future resume.
    assert marker_path.exists()


def test_read_notarization_request_missing(
    package_command,
    first_app_with_binaries,
):
    """A missing notarization request marker raises an error."""
    first_app_with_binaries.packaging_format = "dmg"

    with pytest.raises(BriefcaseCommandError, match="does not exist"):
        package_command.read_notarization_request(first_app_with_binaries)


def test_read_notarization_request_malformed(
    package_command,
    first_app_with_binaries,
):
    """A notarization request marker that isn't valid TOML raises an error."""
    first_app_with_binaries.packaging_format = "dmg"
    marker_path = package_command.notarization_request_path(first_app_with_binaries)
    create_file(marker_path, "[not-valid-toml")

    with pytest.raises(BriefcaseCommandError, match="is malformed"):
        package_command.read_notarization_request(first_app_with_binaries)


def test_read_notarization_request_missing_key(
    package_command,
    first_app_with_binaries,
):
    """A notarization request marker that is missing a required key raises an error."""
    first_app_with_binaries.packaging_format = "dmg"
    marker_path = package_command.notarization_request_path(first_app_with_binaries)
    create_file(marker_path, 'identity = "CAFEBEEF"\n')

    with pytest.raises(BriefcaseCommandError, match="is missing required key"):
        package_command.read_notarization_request(first_app_with_binaries)


def test_resume_notarization_marker_identity_mismatch(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """A marker identity that doesn't match the requested identity raises an error."""
    first_app_with_binaries.packaging_format = "dmg"
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id="submission-1",
    )

    with pytest.raises(
        BriefcaseCommandError, match="does not match the specified identity"
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            identity="someone-else",
        )


def test_resume_notarization_marker_installer_missing(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """An installer identity provided without one in the marker raises an error."""
    first_app_with_binaries.packaging_format = "dmg"
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id="submission-1",
    )

    with pytest.raises(
        BriefcaseCommandError, match="does not contain an installer identity"
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            installer_identity=sekrit_installer_identity.id,
        )


def test_resume_notarization_marker_installer_mismatch(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    sekrit_installer_identity,
    tmp_path,
):
    """A marker installer identity that doesn't match the requested one raises an
    error."""
    first_app_with_binaries.packaging_format = "dmg"
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )
    package_command.write_notarization_request(
        first_app_with_binaries,
        identity=sekrit_identity,
        submission_id="submission-1",
        installer_identity=sekrit_installer_identity,
    )

    with pytest.raises(
        BriefcaseCommandError, match="does not match the specified installer identity"
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            installer_identity="someone-else",
        )


def test_resume_notarize_app_artefact_missing(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """If the app binary doesn't exist, notarization of an app cannot be resumed."""
    # Delete the actual binary
    shutil.rmtree(tmp_path / "base_path/build/first-app/macos/app/First App.app")

    # Mock the command factory to prevent the binary from being rebuilt as part of
    # package dependencies.
    package_command._command_factory = mock.MagicMock()

    # Attempting to resume notarization when there's no pre-existing artefact raises an
    # error.
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Notarization cannot be resumed, as the notarization artefact "
            r"associated with this app \(.*First App.app\) does not exist."
        ),
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="zip",
            identity=sekrit_identity.id,
            submission_id=str(uuid.uuid4()),
        )


def test_resume_notarize_app_dist_artefact_exists(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    sleep_zero,
):
    """A *distribution* artefact of an app bundle will be cleaned up as part of resuming
    notarization."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.app.zip",
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the creation of the ditto archive
    package_command.ditto_archive = mock.MagicMock()

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App.app.zip",
                    "status": "In Progress",
                },
            ]
        },
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

    # Resume notarizaton. Use the base command's interface to ensure the full cleanup
    # process is tested.
    package_command._package_app(
        first_app_with_binaries,
        update=False,
        packaging_format="zip",
        identity=sekrit_identity.id,
        submission_id=submission_id,
    )

    # Identity selection excluded adhoc identities
    package_command.select_identity.assert_called_once_with(
        identity=sekrit_identity.id,
        allow_adhoc=False,
    )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # Notarization is complete; we can staple.
    package_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "stapler",
            "staple",
            tmp_path / "base_path/build/first-app/macos/app/First App.app",
        ],
        check=True,
    )

    # As this is a .zip distribution, there's a finalization step to create the actual
    # distribution artefact with ditto. This file won't actually be created though, as
    # we're mocking ditto. However, as a result of resuming with a pre-existing
    # distribution artefact, the pre-existing artefact will have been deleted.
    package_command.ditto_archive.assert_called_once_with(
        tmp_path / "base_path/build/first-app/macos/app/First App.app",
        tmp_path / "base_path/dist/First App-0.0.1.app.zip",
    )

    assert not (tmp_path / "base_path/dist/First App-0.0.1.app.zip").exists()


def test_resume_notarize_artefact_missing(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
):
    """If the distribution artefact doesn't exist, notarization cannot be resumed."""

    # Attempting to resume notarization when there's no pre-existing artefact raises an
    # error.
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Notarization cannot be resumed, as the notarization artefact "
            r"associated with this app \(.*First App-0.0.1.dmg\) does not exist."
        ),
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            identity=sekrit_identity.id,
            submission_id=str(uuid.uuid4()),
        )


def test_invalid_submission_id(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """If an invalid submission ID is provided, an error is raised."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with submission IDs that don't
        # match the expected submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "First App-0.0.1.dmg",
                    "status": "In Progress",
                },
            ]
        },
    ]

    # Attempt to resume notarizaton. The submission ID will be rejected.
    with pytest.raises(
        BriefcaseCommandError,
        match=rf"{submission_id} is not a known submission ID for this identity.",
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            identity=sekrit_identity.id,
            submission_id=submission_id,
        )

    # The history has been retrieved.
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "history",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
    )

    # No staple attempt is made
    package_command.tools.subprocess.run.assert_not_called()


def test_invalid_notarization_identity(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
):
    """If an invalid notarization identity is provided, an error is raised."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns an error
        subprocess.CalledProcessError(69, cmd="xcrun notarytool history")
    ]

    # Attempt to resume notarizaton. The submission ID will not be validated
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            r"Unable to invoke notarytool to determine validity of submission ID.\n"
            r"Are you sure this is the identity that was used to notarize the app\?"
        ),
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            identity=sekrit_identity.id,
            submission_id=submission_id,
        )

    # The history has been retrieved.
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "history",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
    )

    # No staple attempt is made
    package_command.tools.subprocess.run.assert_not_called()


@pytest.mark.parametrize(
    "dist_filename",
    [
        "First App-0.0.1.app.zip",
        "First App-0.0.1.dmg",
        "First App-0.0.1.pkg",
    ],
)
def test_filename_mismatch(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    dist_filename,
):
    """If the filename on a notarization submission doesn't match the current artefact,
    an error is raised."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist" / dist_filename,
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with a submission ID that matches,
        # but the filename won't.
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "Third App-0.0.1.dmg",
                    "status": "In Progress",
                },
            ]
        },
    ]

    # Attempt to resume notarizaton. The submission ID will be rejected.
    with pytest.raises(
        BriefcaseCommandError,
        match=(
            rf"{submission_id} is not a submission ID for this project. "
            r"It notarizes a file named Third App-0.0.1.dmg"
        ),
    ):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format=Path(dist_filename).suffix[1:],
            identity=sekrit_identity.id,
            submission_id=submission_id,
        )

    # The history has been retrieved.
    package_command.tools.subprocess.parse_output.assert_called_once_with(
        json_parser,
        [
            "xcrun",
            "notarytool",
            "history",
            "--keychain-profile",
            "briefcase-macOS-DEADBEEF",
            "--output-format",
            "json",
        ],
    )

    # No staple attempt is made
    package_command.tools.subprocess.run.assert_not_called()


@pytest.mark.parametrize(
    ("response", "error"),
    [
        # A response with an unknown status code.
        (
            {"status": "wibble"},
            r"Unexpected notarization status: wibble",
        ),
        # A bare bones response. This isn't something we've seen in practice, but we
        # protect against it anyway.
        (
            {"status": "Invalid"},
            r"Notarization was rejected: No details provided",
        ),
        # A failure with no issues provided.
        (
            {"status": "Invalid", "statusSummary": "Bad mojo"},
            r"Notarization was rejected: Bad mojo",
        ),
        # A failure with an empty list of issues.
        (
            {"status": "Invalid", "statusSummary": "Bad mojo", "issues": []},
            r"Notarization was rejected: Bad mojo",
        ),
        # A failure with a list of minimalist issues
        (
            {
                "status": "Invalid",
                "statusSummary": "Bad mojo",
                "issues": [
                    {
                        "path": "foo/bar",
                        "message": "This isn't good",
                    },
                    {
                        "path": "pork/ham",
                        "message": "This is fairly bad",
                    },
                ],
            },
            (
                r"Notarization was rejected: Bad mojo\n"
                r"\n"
                r"    \* \(\?\) foo/bar \[unknown architecture\]\n"
                r"      This isn't good\n"
                r"      \(No additional help available\)\n"
                r"\n"
                r"    \* \(\?\) pork/ham \[unknown architecture\]\n"
                r"      This is fairly bad\n"
                r"      \(No additional help available\)"
            ),
        ),
        # A failure with a fully populated list of issues
        (
            {
                "status": "Invalid",
                "statusSummary": "Bad mojo",
                "issues": [
                    {
                        "severity": "Error",
                        "path": "foo/bar",
                        "architecture": "arm64",
                        "message": "This isn't good",
                        "docUrl": "https://example.com/error",
                    },
                    {
                        "severity": "Warning",
                        "path": "pork/ham",
                        "architecture": "arm64",
                        "message": "This is fairly bad",
                        "docUrl": "https://example.com/warning",
                    },
                ],
            },
            (
                r"Notarization was rejected: Bad mojo\n"
                r"\n"
                r"    \* \(Error\) foo/bar \[arm64\]\n"
                r"      This isn't good\n"
                r"      https://example.com/error\n"
                r"\n"
                r"    \* \(Warning\) pork/ham \[arm64\]\n"
                r"      This is fairly bad\n"
                r"      https://example.com/warning"
            ),
        ),
    ],
)
def test_notarization_rejected(
    package_command,
    first_app_with_binaries,
    sekrit_identity,
    tmp_path,
    sleep_zero,
    response,
    error,
):
    """If notarization is rejected, an error is raised."""
    # Create a pre-existing distribution artefact
    create_file(
        tmp_path / "base_path/dist/First App-0.0.1.dmg",
        "distribution file",
    )

    # Select a codesigning identity
    package_command.select_identity.return_value = sekrit_identity

    # Mock the return values of subprocesses
    submission_id = str(uuid.uuid4())
    package_command.tools.subprocess.parse_output.side_effect = [
        # notarytool history returns list with the app's submission ID
        {
            "history": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Other App-1.2.3.dmg",
                    "status": "Accepted",
                },
                {
                    "id": submission_id,
                    "name": "First App-0.0.1.dmg",
                    "status": "In Progress",
                },
            ]
        },
        # notarytool log; 2 failures, then a successful result.
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        subprocess.CalledProcessError(
            returncode=69,
            cmd=["xcrun", "notarytool", "log"],
        ),
        response,
    ]

    # Resume notarizaton
    with pytest.raises(BriefcaseCommandError, match=error):
        package_command._package_app(
            first_app_with_binaries,
            update=False,
            packaging_format="dmg",
            identity=sekrit_identity.id,
            submission_id=submission_id,
        )

    # The calls to notarization tools were made
    assert package_command.tools.subprocess.parse_output.mock_calls == [
        # Retrieve notarization history to verify the submission ID
        mock.call(
            json_parser,
            [
                "xcrun",
                "notarytool",
                "history",
                "--keychain-profile",
                "briefcase-macOS-DEADBEEF",
                "--output-format",
                "json",
            ],
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

    # No staple attempt is made.
    package_command.tools.subprocess.run.assert_not_called()
