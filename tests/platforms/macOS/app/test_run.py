import os
import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.platforms.macOS.app import macOSAppRunCommand


def test_run_app(first_app_config, tmp_path):
    "A macOS app can be started"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    log_stream_process = mock.MagicMock()
    command.subprocess.Popen.return_value = log_stream_process

    command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    bin_path = command.binary_path(first_app_config)
    sender = bin_path / "Contents" / "MacOS" / "First App"
    command.subprocess.Popen.assert_called_with(
        [
            'log', 'stream',
            '--style', 'compact',
            '--predicate',
            f'senderImagePath=="{sender}"'
            f' OR (processImagePath=="{sender}"'
            ' AND senderImagePath=="/usr/lib/libffi.dylib")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    command.subprocess.run.assert_called_with(
        ['open', '-n', os.fsdecode(bin_path)],
        check=True
    )
    command.subprocess.stream_output.assert_called_with("log stream", log_stream_process)


def test_run_app_failed(first_app_config, tmp_path):
    "If there's a problem started the app, an exception is raised"
    command = macOSAppRunCommand(base_path=tmp_path)
    command.subprocess = mock.MagicMock()
    log_stream_process = mock.MagicMock()
    command.subprocess.Popen.return_value = log_stream_process
    command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['open', '-n', os.fsdecode(command.binary_path(first_app_config))],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # Calls were made to start the app and to start a log stream.
    bin_path = command.binary_path(first_app_config)
    sender = bin_path / "Contents" / "MacOS" / "First App"
    command.subprocess.Popen.assert_called_with(
        [
            'log', 'stream',
            '--style', 'compact',
            '--predicate',
            f'senderImagePath=="{sender}"'
            f' OR (processImagePath=="{sender}"'
            ' AND senderImagePath=="/usr/lib/libffi.dylib")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    command.subprocess.run.assert_called_with(
        ['open', '-n', os.fsdecode(bin_path)],
        check=True
    )

    # No attempt was made to stream the log; but there was a cleanup
    command.subprocess.stream_output.assert_not_called()
    command.subprocess.cleanup.assert_called_with("log stream", log_stream_process)
