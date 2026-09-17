import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.gnupg import GnuPG
from briefcase.integrations.subprocess import Subprocess


def test_gpg_verified(mock_tools):
    """GnuPG.verify() creates a tool instance if gpg is available."""
    mock_tools.host_os = "Linux"
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    gpg = GnuPG.verify(tools=mock_tools)

    assert isinstance(gpg, GnuPG)
    assert mock_tools.gnupg == gpg
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["gpg", "--version"],
        quiet=1,
    )


def test_gpg_short_circuit(mock_tools, gpg):
    """If gpg is already verified, it is returned without re-checking."""
    mock_tools.gnupg = gpg
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    assert GnuPG.verify(tools=mock_tools) == gpg
    mock_tools.subprocess.check_output.assert_not_called()


def test_gpg_not_installed(mock_tools):
    """If gpg isn't installed, an error with an install hint is raised."""
    mock_tools.host_os = "Linux"
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError("gpg not found")

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't find the gpg tool\. Install the `gnupg` package",
    ):
        GnuPG.verify(tools=mock_tools)


def test_gpg_unable_to_invoke(mock_tools):
    """If gpg can't be invoked, an error is raised."""
    mock_tools.host_os = "Linux"
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["gpg", "--version"],
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to invoke gpg\.",
    ):
        GnuPG.verify(tools=mock_tools)
