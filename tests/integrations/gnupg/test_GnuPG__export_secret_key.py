import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess

from .conftest import JANE


def test_export_secret_key(mock_tools, gpg):
    """A secret key is exported to a file."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    output_path = Path("/path/to/key.gpg")

    gpg.export_secret_key(JANE, output_path)

    mock_tools.subprocess.run.assert_called_once_with(
        [
            "gpg",
            "--batch",
            "--output",
            output_path,
            "--export-secret-keys",
            JANE,
        ],
        check=True,
    )


def test_export_secret_key_error(mock_tools, gpg):
    """If the key can't be exported, an error is raised."""
    mock_tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    mock_tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd=["gpg", "--batch", "--export-secret-keys", JANE],
    )
    output_path = Path("/path/to/key.gpg")

    with pytest.raises(
        BriefcaseCommandError,
        match=rf"Error exporting the GPG signing key for identity {JANE}\.",
    ):
        gpg.export_secret_key(JANE, output_path)
