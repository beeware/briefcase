import os
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = GradleBuildCommand(
        base_path=tmp_path / "base_path", apps={"first": first_app_config},
    )

    # Mock-out the `sys` module so we can mock out the Python version in some tests.
    command.sys = mock.MagicMock()

    # Use the `tmp_path` in `dot_briefcase_path` to ensure tests don't interfere
    # with each other.
    command.dot_briefcase_path = tmp_path / ".briefcase"

    # Use a dummy JAVA HOME
    command.java_home_path = tmp_path / "java"

    # Override the `os` module so the app has an environment with JAVA_HOME
    command.os = mock.MagicMock(environ={
        'JAVA_HOME': str(command.java_home_path)
    })
    # Enable the command to use `os.access()` and `os.X_OK`.
    command.os.access = os.access
    command.os.X_OK = os.X_OK

    # Override the requests` and `subprocess` modules so we can test side-effects.
    command.requests = mock.MagicMock()
    command.subprocess = mock.MagicMock()

    return command


def test_permit_python_37(build_command):
    "Validate that Python 3.7 is accepted." ""
    # Mock out the currently-running Python version to be 3.7.
    build_command.sys.version_info.major = 3
    build_command.sys.version_info.minor = 7
    build_command.verify_python_version()


@pytest.mark.parametrize("major,minor", [(3, 5), (3, 6), (3, 8)])
def test_require_python_37(build_command, major, minor):
    "Validate that Python versions other than 3.7 are rejected."
    # Mock out the Python version to check that version.
    build_command.sys.version_info.major = major
    build_command.sys.version_info.minor = minor
    with pytest.raises(BriefcaseCommandError):
        build_command.verify_python_version()
