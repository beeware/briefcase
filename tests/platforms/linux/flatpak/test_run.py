from unittest import mock

import pytest

from briefcase.console import Console, LogLevel
from briefcase.integrations.flatpak import Flatpak
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.flatpak import LinuxFlatpakRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = LinuxFlatpakRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.flatpak = mock.MagicMock(spec_set=Flatpak)
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


def test_run_gui_app(run_command, first_app_config):
    """A GUI flatpak can be executed."""
    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=[],
        stream_output=True,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_with_passthrough(run_command, first_app_config):
    """A GUI flatpak can be executed in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # App is executed with args
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=["foo", "--bar"],
        stream_output=True,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


def test_run_gui_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the GUI app, an exception is raised."""
    run_command.tools.flatpak.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, passthrough=[])

    # The run command was still invoked
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=[],
        stream_output=True,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app(run_command, first_app_config):
    """A console flatpak can be executed."""
    first_app_config.console_app = True

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=[],
        stream_output=False,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_with_passthrough(run_command, first_app_config):
    """A console flatpak can be executed in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG
    first_app_config.console_app = True

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # App is executed with args
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=["foo", "--bar"],
        stream_output=False,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the console app, an exception is raised."""
    first_app_config.console_app = True

    run_command.tools.flatpak.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, passthrough=[])

    # The run command was still invoked
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=[],
        stream_output=False,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_test_mode(run_command, first_app_config, is_console_app):
    """A flatpak can be executed in test mode."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, passthrough=[])

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=[],
        stream_output=True,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_test_mode_with_args(run_command, first_app_config, is_console_app):
    """A flatpak can be executed in test mode with args."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app
    first_app_config.test_mode = True

    # Set up the log streamer to return a known stream and a good return code
    log_popen = mock.MagicMock()
    run_command.tools.flatpak.run.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        passthrough=["foo", "--bar"],
    )

    # App is executed
    run_command.tools.flatpak.run.assert_called_once_with(
        bundle_identifier="com.example.first-app",
        args=["foo", "--bar"],
        stream_output=True,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        clean_output=False,
    )
