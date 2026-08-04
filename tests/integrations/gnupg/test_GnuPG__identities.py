import subprocess
from unittest import mock

from briefcase.integrations.gnupg import GnuPG
from briefcase.integrations.subprocess import Subprocess

from .conftest import BOB, BOB_OUTPUT, GPG_OUTPUT, JANE, JANE_ALT_UID


def test_identities(mock_tools):
    """Secret keys are parsed into a dictionary of identities."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.return_value = GPG_OUTPUT

    identities = GnuPG.identities(tools=mock_tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["gpg", "--list-secret-keys", "--with-colons"],
        quiet=1,
    )


def test_identities_multiple_keys(mock_tools):
    """Multiple secret keys are all returned, and subkey fingerprints are ignored."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.return_value = GPG_OUTPUT + BOB_OUTPUT

    identities = GnuPG.identities(tools=mock_tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }


def test_identities_multiple_uids(mock_tools):
    """If a key has multiple user IDs, the first is used."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.return_value = GPG_OUTPUT + JANE_ALT_UID

    identities = GnuPG.identities(tools=mock_tools)

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }


def test_identities_no_keys(mock_tools):
    """If gpg reports no secret keys, no identities are returned."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=2,
        cmd=["gpg", "--list-secret-keys"],
    )

    assert GnuPG.identities(tools=mock_tools) == {}


def test_identities_not_installed(mock_tools):
    """If gpg isn't installed, no identities are returned."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError("gpg not found")

    assert GnuPG.identities(tools=mock_tools) == {}
