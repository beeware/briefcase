import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, LogLevel
from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux.appimage import LinuxAppImageRunCommand


@pytest.fixture
def run_command(tmp_path):
    command = LinuxAppImageRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "x86_64"

    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os(run_command, host_os):
    """Error raised for an unsupported OS."""
    run_command.tools.host_os = host_os
    # Mock the existence of a single app
    run_command.apps = {"app": None}

    with pytest.raises(
        UnsupportedHostError,
        match="Linux AppImages can only be executed on Linux.",
    ):
        run_command()


def test_run_gui_app(run_command, first_app_config, tmp_path):
    """A linux GUI App can be started."""
    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage"
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_gui_app_with_passthrough(run_command, first_app_config, tmp_path):
    """A linux GUI App can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_gui_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the GUI app, an exception is raised."""
    run_command.tools.subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage"
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app(run_command, first_app_config, tmp_path):
    """A linux console App can be started."""
    first_app_config.console_app = True

    # Run the app
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess.run.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage"
        ],
        cwd=tmp_path / "home",
        bufsize=1,
        stream_output=False,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_with_passthrough(run_command, first_app_config, tmp_path):
    """A linux console App can be started in debug mode with args."""
    run_command.console.verbosity = LogLevel.DEBUG

    first_app_config.console_app = True

    # Run the app with args
    run_command.run_app(
        first_app_config,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.run.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        bufsize=1,
        stream_output=False,
        env={"BRIEFCASE_DEBUG": "1"},
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_failed(run_command, first_app_config, tmp_path):
    """If there's a problem starting the console app, an exception is raised."""
    first_app_config.console_app = True

    run_command.tools.subprocess.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess.run.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage"
        ],
        cwd=tmp_path / "home",
        bufsize=1,
        stream_output=False,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode(run_command, first_app_config, is_console_app, tmp_path):
    """A linux App can be started in test mode."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app_config, test_mode=True, passthrough=[])

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage"
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode_with_args(
    run_command,
    first_app_config,
    is_console_app,
    tmp_path,
):
    """A linux App can be started in test mode with args."""
    # Test mode apps are always streamed
    first_app_config.console_app = is_console_app

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app_config,
        test_mode=True,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            tmp_path
            / "base_path/build/first-app/linux/appimage/First_App-0.0.1-x86_64.AppImage",
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app_config,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )
