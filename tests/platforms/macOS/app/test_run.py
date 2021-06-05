import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppRunCommand


def test_run_app(first_app_config, tmp_path):
    "A macOS App can be started"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.check_output.return_value = "3742"

    command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    command.subprocess.run.assert_has_calls([
        mock.call(
            ['open', '-n', str(command.binary_path(first_app_config))],
            check=True
        ),
        mock.call(
            ['log', 'stream', '--process', '3742', '--style', 'compact', '--type', 'log'],
            check=True,
        )
    ])

    # A call to pgrep was also made
    command.subprocess.check_output.assert_called_with(
        ['pgrep', '-n', 'First App'],
        universal_newlines=True
    )


def test_run_app_failed(first_app_config, tmp_path):
    "If there's a problem started the app, an exception is raised"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['open', '-n', str(command.binary_path(first_app_config))],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, though
    command.subprocess.run.assert_called_with(
        ['open', '-n', str(command.binary_path(first_app_config))],
        check=True
    )

    # but no attempt was made to find the PID
    command.subprocess.check_output.assert_not_called()


def test_run_app_no_pid(first_app_config, tmp_path):
    "If there's a problem finding the PID of the app, an exception is raised"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['pgrep', '-n', 'invalid app'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The run command was still invoked, but the log stream wasn't
    command.subprocess.run.assert_has_calls([
        mock.call(
            ['open', '-n', str(command.binary_path(first_app_config))],
            check=True
        ),
    ])

    # and an attempt was made to but no attempt was made to find the PID
    command.subprocess.check_output.assert_called_with(
        ['pgrep', '-n', 'First App'],
        universal_newlines=True
    )


def test_run_app_log_failed(first_app_config, tmp_path):
    "If the log can't be streamed, the app still starts"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    command.subprocess.check_output.return_value = "3742"
    command.subprocess.run.side_effect = [
        None,
        subprocess.CalledProcessError(
            cmd=['log', 'stream'],
            returncode=1
        )
    ]

    # The run command raises an error because the log stream couldn't start
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    command.subprocess.run.assert_has_calls([
        mock.call(
            ['open', '-n', str(command.binary_path(first_app_config))],
            check=True
        ),
        mock.call(
            ['log', 'stream', '--process', '3742', '--style', 'compact', '--type', 'log'],
            check=True,
        )
    ])

    # A call to pgrep was also made
    command.subprocess.check_output.assert_called_with(
        ['pgrep', '-n', 'First App'],
        universal_newlines=True
    )
