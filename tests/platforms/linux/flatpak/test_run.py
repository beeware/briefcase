from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = LinuxFlatpakRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


def test_run(run_command, first_app_config):
    """A flatpak can be executed."""
    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=False)

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the app, an exception is raised."""
    run_command.tools.flatpak.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, test_mode=False)

    # The run command was still invoked
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_test_mode(run_command, first_app_config):
    """A flatpak can be executed in test mode."""
    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=True)

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle="com.example",
        app_name="first-app",
        main_module="tests.first_app",
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )
