import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import get_team_id

# The output of `security find-certificate -a -c <name> -Z -p` when there are two
# certificates with the same name.
SECURITY_OUTPUT = """\
SHA-256 hash: 1F6B4C5F0D2B8A8E9C6E0A1D2F3B4C5D6E7F8091A2B3C4D5E6F708192A3B4C5D
SHA-1 hash: 11223344556677889900AABBCCDDEEFF00112233
-----BEGIN CERTIFICATE-----
MIIFIRSTCERTIFICATE
-----END CERTIFICATE-----
SHA-256 hash: 2A7C5D6E1E3C9B9F0D7F1B2E3A4C5D6E7F8091A2B3C4D5E6F708192A3B4C5D6E
SHA-1 hash: CAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEF
-----BEGIN CERTIFICATE-----
MIISECONDCERTIFICATE
-----END CERTIFICATE-----
"""


def test_team_id(mock_tools):
    """The team ID is read from the certificate matching the identity's fingerprint."""
    mock_tools.subprocess.check_output.side_effect = [
        SECURITY_OUTPUT,
        (
            "subject=C=US,O=Jane Developer,OU=TEAM123456,"
            "CN=Apple Development: jane@example.com (MEMBER1234),UID=ABCDE12345\n"
        ),
    ]

    team_id = get_team_id(
        mock_tools,
        "11223344556677889900AABBCCDDEEFF00112233",
        "Apple Development: jane@example.com (MEMBER1234)",
    )

    assert team_id == "TEAM123456"

    # The subject of the matching certificate was inspected.
    assert mock_tools.subprocess.check_output.mock_calls == [
        mock.call(
            [
                "security",
                "find-certificate",
                "-a",
                "-c",
                "Apple Development: jane@example.com (MEMBER1234)",
                "-Z",
                "-p",
            ],
        ),
        mock.call(
            ["openssl", "x509", "-noout", "-subject", "-nameopt", "RFC2253"],
            input=(
                "-----BEGIN CERTIFICATE-----\n"
                "MIIFIRSTCERTIFICATE\n"
                "-----END CERTIFICATE-----\n"
            ),
        ),
    ]


def test_security_failure(mock_tools):
    """If the certificate can't be inspected, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["security", "find-certificate"],
        returncode=1,
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to inspect the certificate for signing identity",
    ):
        get_team_id(
            mock_tools,
            "CAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEF",
            "Apple Development: jane@example.com (MEMBER1234)",
        )


@pytest.mark.parametrize(
    ("identity_id", "subject"),
    [
        # No certificate matches the fingerprint
        ("DEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF", None),
        # The certificate doesn't have an organizational unit
        (
            "CAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEFCAFEBEEF",
            "subject=C=US,O=Jane Developer,CN=Apple Development: jane@example.com\n",
        ),
    ],
)
def test_no_team_id(mock_tools, identity_id, subject):
    """If the team ID can't be determined, an error is raised."""
    mock_tools.subprocess.check_output.side_effect = [SECURITY_OUTPUT, subject]

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to determine the team ID for signing identity",
    ):
        get_team_id(
            mock_tools,
            identity_id,
            "Apple Development: jane@example.com (MEMBER1234)",
        )
