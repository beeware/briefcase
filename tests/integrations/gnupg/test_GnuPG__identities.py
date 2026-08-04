import subprocess
from unittest import mock

from briefcase.integrations.subprocess import Subprocess

from .conftest import BOB, GPG_OUTPUT, JANE


def test_identities(gpg):
    """Secret keys are parsed into a dictionary of identities."""
    gpg.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    gpg.tools.subprocess.check_output.return_value = GPG_OUTPUT

    identities = gpg.identities()

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }
    gpg.tools.subprocess.check_output.assert_called_once_with(
        ["gpg", "--list-secret-keys", "--with-colons"],
        quiet=1,
    )


def test_identities_multiple_keys(gpg):
    """Multiple secret keys are all returned, and subkey fingerprints are ignored."""
    gpg.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    gpg.tools.subprocess.check_output.return_value = (
        GPG_OUTPUT
        + """sec:u:3072:1:4D68E1A93D2F47FB:1785485980:::u:::scESC:::::::
fpr:::::::::B6C8B38C96FFE1E6A1C66C9F4D68E1A93D2F47FB:
uid:u::::1785485980::89A2D4C6E5F8B3E7::Bob Builder <bob@example.com>::::::::::0:
"""
    )

    identities = gpg.identities()

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
        BOB: "Bob Builder <bob@example.com>",
    }


def test_identities_multiple_uids(gpg):
    """If a key has multiple user IDs, the first is used."""
    gpg.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    gpg.tools.subprocess.check_output.return_value = (
        GPG_OUTPUT
        + """uid:u::::1785485940::E70814C3C8DC3AC3940E8BFBA0288F0CE55F2120::Jane <jane@example.com>::::::::::0:
"""
    )

    identities = gpg.identities()

    assert identities == {
        JANE: "Jane Doe <jane@example.com>",
    }


def test_identities_no_keys(gpg):
    """If gpg reports no secret keys, no identities are returned."""
    gpg.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    gpg.tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=2,
        cmd=["gpg", "--list-secret-keys"],
    )

    assert gpg.identities() == {}


def test_identities_not_installed(gpg):
    """If gpg isn't installed, no identities are returned."""
    gpg.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    gpg.tools.subprocess.check_output.side_effect = FileNotFoundError("gpg not found")

    assert gpg.identities() == {}
