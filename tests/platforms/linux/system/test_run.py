import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux import parse_freedesktop_os_release, system
from briefcase.platforms.linux.system import LinuxSystemRunCommand

from ....utils import create_file


@pytest.fixture
def run_command(tmp_path):
    command = LinuxSystemRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    command._stream_app_logs = mock.MagicMock()

    return command


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os(run_command, first_app, host_os):
    """Error raised for an unsupported OS."""
    run_command.tools.host_os = host_os
    # Mock the existence of a single app
    run_command.apps = {"app": first_app}

    # Parse the command line
    run_command.parse_options([])

    with pytest.raises(
        UnsupportedHostError,
        match="Linux system projects can only be executed on Linux.",
    ):
        run_command()


def test_supported_host_os(monkeypatch, run_command, first_app, tmp_path):
    """A supported OS (linux) can invoke run."""
    # This also verifies that Run (which is a passive command) can generate
    # build/create commands (which are not passive).

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Mock the freedesktop ID environment
    os_release = "\n".join(
        [
            "ID=somevendor",
            "VERSION_CODENAME=surprising",
            "ID_LIKE=debian",
        ]
    )
    if sys.version_info >= (3, 10):
        # mock platform.freedesktop_os_release()
        run_command.tools.platform.freedesktop_os_release = mock.MagicMock(
            return_value=parse_freedesktop_os_release(os_release)
        )
    else:
        # For Pre Python3.10, mock the /etc/release file
        create_file(tmp_path / "os-release", os_release)
        run_command.tools.ETC_OS_RELEASE = tmp_path / "os-release"

    # Mock the glibc version
    run_command.target_glibc_version = mock.MagicMock(return_value="2.42")

    # Mock the existence of a valid non-docker system Python
    # with the same major/minor as the current Python
    python3 = mock.MagicMock()
    python3.resolve.return_value = Path(
        f"/usr/bin/python{sys.version_info.major}.{sys.version_info.minor}"
    )
    mock_Path = mock.MagicMock(return_value=python3)
    monkeypatch.setattr(system, "Path", mock_Path)

    run_command.tools.host_os = "Linux"

    # Mock the existence of a single app
    run_command.apps = {"app": first_app}

    # Parse the command line
    run_command.parse_options([])

    # The command runs without error
    run_command()

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_app(run_command, first_app, tmp_path):
    """A bootstrap binary can be started."""

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_app_with_passthrough(run_command, first_app, tmp_path):
    """A linux App can be started with args."""

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            ),
            "foo",
            "--bar",
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_app_failed(run_command, first_app, tmp_path):
    """If there's a problem starting the app, an exception is raised."""

    run_command.tools.subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_app_test_mode(run_command, first_app, tmp_path):
    """A linux App can be started in test mode."""

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app
    run_command.run_app(first_app, test_mode=True, passthrough=[])

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            )
        ],
        cwd=tmp_path / "home",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"BRIEFCASE_MAIN_MODULE": "tests.first_app"},
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )


def test_run_app_test_mode_with_args(run_command, first_app, tmp_path):
    """A linux App can be started in test mode with args."""

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_popen

    # Run the app with args
    run_command.run_app(
        first_app,
        test_mode=True,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path"
                / "build"
                / "first-app"
                / "somevendor"
                / "surprising"
                / "first-app-0.0.1"
                / "usr"
                / "bin"
                / "first-app"
            ),
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
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )
