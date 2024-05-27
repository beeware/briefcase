import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console, Log, LogLevel
from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.docker import Docker
from briefcase.integrations.subprocess import Subprocess
from briefcase.platforms.linux import parse_freedesktop_os_release, system
from briefcase.platforms.linux.system import LinuxSystemRunCommand

from ....utils import create_file


@pytest.fixture
def run_command(tmp_path, first_app, monkeypatch):
    command = LinuxSystemRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
        apps={"app": first_app},
    )
    command.tools.home_path = tmp_path / "home"

    # Default to running on Linux
    command.tools.host_os = "Linux"

    # Set the host architecture for test purposes.
    command.tools.host_arch = "wonky"

    # Provide Docker
    monkeypatch.setattr(
        Docker, "_is_user_mapping_enabled", mock.MagicMock(return_value=True)
    )
    command.tools.docker = Docker(tools=command.tools)

    # Mock x11 passthrough
    # Mock DISPLAY environment variable
    monkeypatch.setenv("DISPLAY", "66.0")
    # Mock Subprocess.cleanup()
    command.tools.subprocess.cleanup = mock.MagicMock()
    # Mock the proxy
    mock_proxy_popen = mock.MagicMock(spec_set=subprocess.Popen)
    command.tools.docker._x11_tcp_proxy = mock.MagicMock(
        return_value=(mock_proxy_popen, 66)
    )
    # Mock xauth database file path
    mock_xauth_file_path = Path("/tmp/subdir/xauth_file.db")
    command.tools.docker._x11_proxy_display_xauth_file_path = mock.MagicMock(
        return_value=mock_xauth_file_path
    )
    # Mock the xauth database file write
    command.tools.docker._x11_write_xauth_file = mock.MagicMock()

    # Disable Docker by default
    command.target_image = None
    command.extra_docker_build_args = []

    command.tools.subprocess._subprocess = mock.MagicMock(spec_set=subprocess)
    command.tools.subprocess.run = mock.MagicMock(spec_set=Subprocess.run)
    command.tools.subprocess.check_output = mock.MagicMock(
        spec_set=Subprocess.check_output
    )

    command._stream_app_logs = mock.MagicMock()

    mock_linux_env(command, tmp_path, monkeypatch)

    return command


def mock_linux_env(run_command, tmp_path, monkeypatch):
    """Mock a linux system environment."""
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
    monkeypatch.setattr(system, "Path", mock.MagicMock(return_value=python3))


@pytest.mark.parametrize("host_os", ["Darwin", "Windows", "WeirdOS"])
def test_unsupported_host_os(run_command, first_app, host_os):
    """Error raised for an unsupported OS."""
    run_command.tools.host_os = host_os

    # Parse the command line
    run_command.parse_options([])

    with pytest.raises(
        UnsupportedHostError,
        match="Linux system projects can only be executed on Linux.",
    ):
        run_command()


def test_supported_host_os(run_command, first_app, sub_kw, tmp_path):
    """A supported OS (linux) can invoke run."""
    # This also verifies that Run will call the Build command

    # Set up call to start the app to return a known app process
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen = mock.MagicMock(
        return_value=log_popen
    )

    # Parse the command line
    run_command.parse_options([])

    # The command runs without error
    run_command()

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app'}"
        ],
        cwd=f"{tmp_path / 'home'}",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows paths can't be dockerized")
def test_supported_host_os_docker(
    run_command,
    first_app,
    sub_kw,
    tmp_path,
    monkeypatch,
):
    """A supported OS (linux) can invoke run in Docker."""
    # This also verifies that Run will call Create and Build commands

    # Trigger to run in Docker
    run_command.target_image = first_app.target_image = "best/distro"

    # Python inside Docker is always newer
    run_command.tools.subprocess.check_output.return_value = "3.99"
    # Provide Docker app context
    run_command.verify_app_tools(app=first_app)

    # Set up call to start the app to return a known app process
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen = mock.MagicMock(
        return_value=log_popen
    )

    # Mock out the environment
    monkeypatch.setattr(
        run_command.tools.os, "environ", {"ENVVAR": "Value", "DISPLAY": ":99"}
    )

    # Parse the command line
    run_command.parse_options([])

    # The command runs without error
    run_command()

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/tmp/subdir/xauth_file.db:/tmp/xauth_file.db:z",
            "--volume",
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "XAUTHORITY=/tmp/xauth_file.db",
            "--env",
            "DISPLAY=host.docker.internal:66",
            "--workdir",
            f"{tmp_path / 'home'}",
            "--add-host",
            "host.docker.internal:host-gateway",
            "briefcase/com.example.first-app:somevendor-surprising",
            "/app/first-app-0.0.1/usr/bin/first-app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "DISPLAY": ":99", "DOCKER_CLI_HINTS": "false"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_gui_app(run_command, first_app, sub_kw, tmp_path):
    """A bootstrap binary for a GUI app can be started."""

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen = mock.MagicMock(
        return_value=log_popen
    )

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            )
        ],
        cwd=os.fsdecode(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_gui_app_passthrough(run_command, first_app, sub_kw, tmp_path):
    """A bootstrap binary for a GUI app can be started in debug mode with arguments."""
    run_command.logger.verbosity = LogLevel.DEBUG

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen = mock.MagicMock(
        return_value=log_popen
    )

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=["foo", "--bar"])

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            ),
            "foo",
            "--bar",
        ],
        cwd=os.fsdecode(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=mock.ANY,
        **sub_kw,
    )
    # As we're adding to the environment, all the local values will be present.
    # Check that we've definitely set the values we care about
    env = run_command.tools.subprocess._subprocess.Popen.call_args.kwargs["env"]
    assert env["BRIEFCASE_DEBUG"] == "1"

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


def test_run_gui_app_failed(run_command, first_app, sub_kw, tmp_path):
    """If there's a problem starting the GUI app, an exception is raised."""

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    run_command.tools.subprocess._subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            )
        ],
        cwd=os.fsdecode(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        **sub_kw,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app(run_command, first_app, tmp_path):
    """A bootstrap binary for a console app can be started."""
    first_app.console_app = True

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            ],
            cwd=tmp_path / "home",
            bufsize=1,
            stream_output=False,
        )
    ]

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_passthrough(run_command, first_app, tmp_path):
    """A console app can be started in debug mode with command line arguments."""
    run_command.logger.verbosity = LogLevel.DEBUG

    first_app.console_app = True

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=["foo", "--bar"])

    # The process was started
    run_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app",
                "foo",
                "--bar",
            ],
            cwd=tmp_path / "home",
            bufsize=1,
            stream_output=False,
            env={"BRIEFCASE_DEBUG": "1"},
        )
    ]

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


def test_run_console_app_failed(run_command, first_app, sub_kw, tmp_path):
    """If there's a problem starting the console app, an exception is raised."""
    first_app.console_app = True

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    run_command.tools.subprocess.run.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess.run.mock_calls == [
        mock.call(
            [
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            ],
            cwd=tmp_path / "home",
            bufsize=1,
            stream_output=False,
        )
    ]

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.skipif(sys.platform == "win32", reason="Windows paths can't be dockerized")
def test_run_app_docker(run_command, first_app, sub_kw, tmp_path, monkeypatch):
    """A bootstrap binary can be started in Docker."""
    # Trigger to run in Docker
    run_command.target_image = first_app.target_image = "best/distro"

    # Python inside Docker is always newer
    run_command.tools.subprocess.check_output.return_value = "3.99"
    # Provide Docker app context
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen = mock.MagicMock(
        return_value=log_popen
    )

    # Mock out the environment
    monkeypatch.setattr(
        run_command.tools.os, "environ", {"ENVVAR": "Value", "DISPLAY": ":99"}
    )

    # Run the app
    run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/tmp/subdir/xauth_file.db:/tmp/xauth_file.db:z",
            "--volume",
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "XAUTHORITY=/tmp/xauth_file.db",
            "--env",
            "DISPLAY=host.docker.internal:66",
            "--workdir",
            f"{tmp_path / 'home'}",
            "--add-host",
            "host.docker.internal:host-gateway",
            "briefcase/com.example.first-app:somevendor-surprising",
            "/app/first-app-0.0.1/usr/bin/first-app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "DISPLAY": ":99", "DOCKER_CLI_HINTS": "false"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=False,
        clean_output=False,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows paths can't be dockerized")
def test_run_app_failed_docker(run_command, first_app, sub_kw, tmp_path, monkeypatch):
    """If there's a problem starting the app in Docker, an exception is raised."""

    # Trigger to run in Docker
    run_command.target_image = first_app.target_image = "best/distro"

    # Python inside Docker is always newer
    run_command.tools.subprocess.check_output.return_value = "3.99"
    # Provide Docker app context
    run_command.verify_app_tools(app=first_app)

    # Mock out the environment
    monkeypatch.setattr(
        run_command.tools.os, "environ", {"ENVVAR": "Value", "DISPLAY": ":99"}
    )

    run_command.tools.subprocess._subprocess.Popen.side_effect = OSError

    with pytest.raises(OSError):
        run_command.run_app(first_app, test_mode=False, passthrough=[])

    # The run command was still invoked
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/tmp/subdir/xauth_file.db:/tmp/xauth_file.db:z",
            "--volume",
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "XAUTHORITY=/tmp/xauth_file.db",
            "--env",
            "DISPLAY=host.docker.internal:66",
            "--workdir",
            f"{tmp_path / 'home'}",
            "--add-host",
            "host.docker.internal:host-gateway",
            "briefcase/com.example.first-app:somevendor-surprising",
            "/app/first-app-0.0.1/usr/bin/first-app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "DISPLAY": ":99", "DOCKER_CLI_HINTS": "false"},
        **sub_kw,
    )

    # No attempt to stream was made
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode(
    run_command,
    first_app,
    is_console_app,
    sub_kw,
    tmp_path,
    monkeypatch,
):
    """A linux App can be started in test mode."""
    # Test mode apps are always streamed
    first_app.console_app = is_console_app

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen.return_value = log_popen

    # Mock out the environment
    monkeypatch.setattr(run_command.tools.os, "environ", {"ENVVAR": "Value"})

    # Run the app
    run_command.run_app(first_app, test_mode=True, passthrough=[])

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            )
        ],
        cwd=os.fsdecode(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "BRIEFCASE_MAIN_MODULE": "tests.first_app"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows paths can't be dockerized")
@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode_docker(
    run_command,
    first_app,
    is_console_app,
    sub_kw,
    tmp_path,
    monkeypatch,
):
    """A linux App can be started in Docker in test mode."""
    # Test mode apps are always streamed
    first_app.console_app = is_console_app

    # Trigger to run in Docker
    run_command.target_image = first_app.target_image = "best/distro"

    # Python inside Docker is always newer
    run_command.tools.subprocess.check_output.return_value = "3.99"
    # Provide Docker app context
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen.return_value = log_popen

    # Mock out the environment
    monkeypatch.setattr(
        run_command.tools.os, "environ", {"ENVVAR": "Value", "DISPLAY": ":99"}
    )

    # Run the app
    run_command.run_app(first_app, test_mode=True, passthrough=[])

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/tmp/subdir/xauth_file.db:/tmp/xauth_file.db:z",
            "--volume",
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "BRIEFCASE_MAIN_MODULE=tests.first_app",
            "--env",
            "XAUTHORITY=/tmp/xauth_file.db",
            "--env",
            "DISPLAY=host.docker.internal:66",
            "--workdir",
            f"{tmp_path / 'home'}",
            "--add-host",
            "host.docker.internal:host-gateway",
            "briefcase/com.example.first-app:somevendor-surprising",
            "/app/first-app-0.0.1/usr/bin/first-app",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "DISPLAY": ":99", "DOCKER_CLI_HINTS": "false"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )


@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode_with_args(
    run_command,
    first_app,
    is_console_app,
    sub_kw,
    tmp_path,
    monkeypatch,
):
    """A linux App can be started in test mode with args."""
    # Test mode apps are always streamed
    first_app.console_app = is_console_app

    # Set up tool cache
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen.return_value = log_popen

    # Mock out the environment
    monkeypatch.setattr(run_command.tools.os, "environ", {"ENVVAR": "Value"})

    # Run the app with args
    run_command.run_app(
        first_app,
        test_mode=True,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            os.fsdecode(
                tmp_path
                / "base_path/build/first-app/somevendor/surprising/first-app-0.0.1/usr/bin/first-app"
            ),
            "foo",
            "--bar",
        ],
        cwd=os.fsdecode(tmp_path / "home"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "BRIEFCASE_MAIN_MODULE": "tests.first_app"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="Windows paths can't be dockerized")
@pytest.mark.parametrize("is_console_app", [True, False])
def test_run_app_test_mode_with_args_docker(
    run_command,
    first_app,
    is_console_app,
    sub_kw,
    tmp_path,
    monkeypatch,
):
    """A linux App can be started in Docker in test mode with args."""
    # Test mode apps are always streamed
    first_app.console_app = is_console_app

    # Trigger to run in Docker
    run_command.target_image = first_app.target_image = "best/distro"

    # Python inside Docker is always newer
    run_command.tools.subprocess.check_output.return_value = "3.99"
    # Provide Docker app context
    run_command.verify_app_tools(app=first_app)

    # Set up the log streamer to return a known stream
    log_popen = mock.MagicMock()
    run_command.tools.subprocess._subprocess.Popen.return_value = log_popen

    # Mock out the environment
    monkeypatch.setattr(
        run_command.tools.os, "environ", {"ENVVAR": "Value", "DISPLAY": ":99"}
    )

    # Run the app with args
    run_command.run_app(
        first_app,
        test_mode=True,
        passthrough=["foo", "--bar"],
    )

    # The process was started
    run_command.tools.subprocess._subprocess.Popen.assert_called_with(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            "/tmp/subdir/xauth_file.db:/tmp/xauth_file.db:z",
            "--volume",
            f"{tmp_path / 'base_path/build/first-app/somevendor/surprising'}:/app:z",
            "--volume",
            f"{tmp_path / 'briefcase'}:/briefcase:z",
            "--env",
            "BRIEFCASE_MAIN_MODULE=tests.first_app",
            "--env",
            "XAUTHORITY=/tmp/xauth_file.db",
            "--env",
            "DISPLAY=host.docker.internal:66",
            "--workdir",
            f"{tmp_path / 'home'}",
            "--add-host",
            "host.docker.internal:host-gateway",
            "briefcase/com.example.first-app:somevendor-surprising",
            "/app/first-app-0.0.1/usr/bin/first-app",
            "foo",
            "--bar",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env={"ENVVAR": "Value", "DISPLAY": ":99", "DOCKER_CLI_HINTS": "false"},
        **sub_kw,
    )

    # The streamer was started
    run_command._stream_app_logs.assert_called_once_with(
        first_app,
        popen=log_popen,
        test_mode=True,
        clean_output=False,
    )
