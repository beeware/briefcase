import os
from unittest import mock

import pytest

from briefcase.platforms.android.gradle import GradleBuildCommand


@pytest.fixture
def build_command(tmp_path, first_app_config):
    command = GradleBuildCommand(
        base_path=tmp_path / "base_path",
        apps={"first": first_app_config},
    )

    # Mock-out the `sys` module so we can mock out the Python version in some tests.
    command.sys = mock.MagicMock()

    # Use the `tmp_path` in `dot_briefcase_path` to ensure tests don't interfere
    # with each other.
    command.dot_briefcase_path = tmp_path / ".briefcase"

    # Use a dummy JAVA HOME
    command.java_home_path = tmp_path / "java"

    # Override the `os` module so the app has an environment with JAVA_HOME
    command.os = mock.MagicMock(
        environ={"JAVA_HOME": os.fsdecode(command.java_home_path)}
    )
    # Enable the command to use `os.access()` and `os.X_OK`.
    command.os.access = os.access
    command.os.X_OK = os.X_OK

    # Override the requests` and `subprocess` modules so we can test side-effects.
    command.requests = mock.MagicMock()
    command.subprocess = mock.MagicMock()

    return command
