import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import system


def test_valid_python3(monkeypatch, create_command):
    """If Briefcase is being run with the system python, verification passes."""

    # Mock the existence of a valid non-docker system Python
    # with the same major/minor as the current Python
    python3 = MagicMock()
    python3.resolve.return_value = Path(
        f"/usr/bin/python{sys.version_info.major}.{sys.version_info.minor}"
    )
    mock_Path = MagicMock(return_value=python3)
    monkeypatch.setattr(system, "Path", mock_Path)

    # System Python can be verified
    create_command.verify_system_python()


@pytest.mark.parametrize(
    "resolved_path, expected_error",
    [
        ("/usr/bin/pythonX", "Can't determine the system python version"),
        ("/usr/bin/python3", "Can't determine the system python version"),
        (
            "/usr/bin/python3.X",
            r"The version of Python being used to run Briefcase \(3\..*\) is not the system python3 \(3.X\)\.",
        ),
    ],
)
def test_bad_python3(monkeypatch, create_command, resolved_path, expected_error):
    """If the system Python3 isn't obviously a Python3, an error is raised."""
    # Mock a Python3 symlink that isn't the existence of a valid non-docker system Python
    # with the same major/minor as the current Python
    python3 = MagicMock()
    python3.resolve.return_value = Path(resolved_path)
    mock_Path = MagicMock(return_value=python3)
    monkeypatch.setattr(system, "Path", mock_Path)

    # Verifying python raises an error
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()
