import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess

from .conftest import JANE


def test_export_public_key_success(mock_tools, gpg, tmp_path):
    """A public key can be exported to a file."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    output_path = tmp_path / "signing-public-key.gpg"

    gpg.export_public_key(JANE, output_path)

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "gpg",
            "--batch",
            "--output",
            output_path,
            "--export",
            JANE,
        ],
        check=True,
    )


def test_export_public_key_error(mock_tools, gpg, tmp_path):
    """If exporting the public key fails, an error is raised."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["gpg", "--batch", "--export"],
    )
    output_path = tmp_path / "signing-public-key.gpg"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Error exporting the GPG public key",
    ):
        gpg.export_public_key(JANE, output_path)


def test_agent_socket_path_success(mock_tools, gpg):
    """The host's GPG agent socket path can be queried."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.return_value = (
        "/run/user/1000/gnupg/S.gpg-agent\n"
    )

    socket_path = gpg.agent_socket_path()

    assert socket_path == Path(
        "/run/user/1000/gnupg/S.gpg-agent",
    )
    mock_tools.subprocess.check_output.assert_called_once_with(
        ["gpgconf", "--list-dirs", "agent-socket"],
        quiet=1,
    )


def test_agent_socket_path_error(mock_tools, gpg):
    """If the socket path can't be determined, an error is raised."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.check_output.side_effect = FileNotFoundError(
        "gpgconf not found"
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Can't determine the path of the GPG agent socket",
    ):
        gpg.agent_socket_path()
