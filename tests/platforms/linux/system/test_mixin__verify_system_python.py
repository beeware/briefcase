from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.linux import system


def test_valid_python3(monkeypatch, create_command):
    """If Briefcase is being run with the system python, verification passes."""
    system_python_check_output = MagicMock(return_value="(3, 12)\n")
    briefcase_version_info = (3, 12, 3, "final", 0)

    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )
    monkeypatch.setattr(
        create_command.tools.sys, "version_info", briefcase_version_info
    )

    # System Python can be verified
    create_command.verify_system_python()


def test_bad_python3(monkeypatch, create_command):
    """If Briefcase's Python version differs from system Python, verification fails."""
    system_python_check_output = MagicMock(return_value="(3, 10)\n")
    briefcase_version_info = (3, 12, 3, "final", 0)

    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )
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
    missing_python3 = MagicMock()
    missing_python3.exists.return_value = False
    monkeypatch.setattr(system, "Path", MagicMock(return_value=missing_python3))

    expected_error = (
        "Can't determine the system python version "
        r"\('/usr/bin/python3' does not exist\)"
    )
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()
