import re
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

    # mock the system Python's 'sys.version'
    system_version = "3.13.3 (main, Aug 14 2025, 11:53:40) [GCC 14.2.0]"
    system_python_check_output = MagicMock(return_value=f"{system_version}\n")
    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )

    # mock the running Python's 'sys.version'
    monkeypatch.setattr(create_command.tools.sys, "version", system_version)

    # System Python can be verified
    create_command.verify_system_python()


def test_bad_python3(monkeypatch, create_command):
    """If Briefcase's Python version differs from system Python, verification fails."""
    # /usr/bin/python3 exists
    existing_python3 = MagicMock()
    existing_python3.exists.return_value = True
    monkeypatch.setattr(system, "Path", MagicMock(return_value=existing_python3))

    # mock the system Python's 'sys.version'
    system_version = "3.13.3 (main, Aug 14 2025, 11:53:40) [GCC 14.2.0]"
    system_python_check_output = MagicMock(return_value=f"{system_version}\n")
    monkeypatch.setattr(
        create_command.tools.subprocess, "check_output", system_python_check_output
    )

    # mock the running Python's 'sys.version'. Even though the major.minor.micro version
    # is the same, the release fingerprint is different.
    briefcase_version = "3.13.3 (main, Apr  9 2025, 04:03:52) [Clang 20.1.0]"
    monkeypatch.setattr(create_command.tools.sys, "version", briefcase_version)

    expected_error = re.escape(
        "The version of Python being used to run Briefcase "
        "('3.13.3 (main, Apr  9 2025, 04:03:52) [Clang 20.1.0]') "
        "is not the system python3 "
        "('3.13.3 (main, Aug 14 2025, 11:53:40) [GCC 14.2.0]')."
    )
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()


def test_missing_python3(monkeypatch, create_command):
    """If Briefcase can't find the system Python, verification fails."""
    # /usr/bin/python3 does not exist
    missing_python3 = MagicMock()
    missing_python3.exists.return_value = False
    monkeypatch.setattr(system, "Path", MagicMock(return_value=missing_python3))

    expected_error = re.escape(
        "Can't determine the system python version ('/usr/bin/python3' does not exist)"
    )
    with pytest.raises(BriefcaseCommandError, match=expected_error):
        create_command.verify_system_python()
