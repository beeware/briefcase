from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import system


def test_valid_python3(monkeypatch, create_command):
    """If Briefcase is being run with the system python, verification passes."""
    # /usr/bin/python3 exists
    existing_python3 = MagicMock()
    existing_python3.exists.return_value = True
    monkeypatch.setattr(system, "Path", MagicMock(return_value=existing_python3))

    # /usr/bin/python3 is Python 3.12
    system_python_check_output = MagicMock(return_value="(3, 12)\n")
    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )

    # sys.version_info is 3.12
    briefcase_version_info = (3, 12, 3, "final", 0)
    monkeypatch.setattr(
        create_command.tools.sys, "version_info", briefcase_version_info
    )

    # System Python can be verified
    create_command.verify_system_python()


def test_bad_python3(monkeypatch, create_command):
    """If Briefcase's Python version differs from system Python, verification fails."""
    # /usr/bin/python3 exists
    existing_python3 = MagicMock()
    existing_python3.exists.return_value = True
    monkeypatch.setattr(system, "Path", MagicMock(return_value=existing_python3))

    # /usr/bin/python3 is Python 3.10
    system_python_check_output = MagicMock(return_value="(3, 10)\n")
    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )

    # sys.version_info is 3.12
    briefcase_version_info = (3, 12, 3, "final", 0)
    monkeypatch.setattr(
        create_command.tools.sys, "version_info", briefcase_version_info
    )

    expected_error = (
        r"The version of Python being used to run Briefcase \(3\.12\) "
        r"is not the system python3 \(3.10\)\."
    )
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()


def test_missing_python3(monkeypatch, create_command):
    """If Briefcase can't find the system Python, verification fails."""
    # /usr/bin/python3 does not exist
    missing_python3 = MagicMock()
    missing_python3.exists.return_value = False
    monkeypatch.setattr(system, "Path", MagicMock(return_value=missing_python3))

    expected_error = (
        "Can't determine the system python version "
        r"\('.*python3' does not exist\)"
    )
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()
