import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppRunCommand


def test_run_app(first_app_config, tmp_path):
    "A macOS App can be started"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()

    command.run_app(first_app_config)

    command.subprocess.run.assert_called_with(
        ['open', str(command.binary_path(first_app_config))],
        check=True
    )


def test_run_app_failed(first_app_config, tmp_path):
    "If there's a problem started the app, an exception is raised"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['open', str(command.binary_path(first_app_config))],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.subprocess.run.assert_called_with(
        ['open', str(command.binary_path(first_app_config))],
        check=True
    )
