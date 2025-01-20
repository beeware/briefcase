import subprocess
import time
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import DeviceState
from briefcase.platforms.iOS.xcode import iOSXcodeRunCommand
from briefcase.platforms.macOS import macOS_log_clean_filter


@pytest.fixture
def run_command(tmp_path):
    command = iOSXcodeRunCommand(
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()

    # To satisfy coverage, the stop function must be invoked
    # at least once when streaming app logs.
    def mock_stream_app_logs(app, stop_func, **kwargs):
        stop_func()

    command._stream_app_logs.side_effect = mock_stream_app_logs

    return command


def test_device_option(run_command):
    """The -d option can be parsed."""
    options, overrides = run_command.parse_options(["-d", "myphone"])

    assert options == {
        "udid": "myphone",
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "update_support": False,
        "update_stub": False,
        "no_update": False,
        "test_mode": False,
        "passthrough": [],
        "appname": None,
    }
    assert overrides == {}


def test_run_multiple_devices_input_disabled(run_command, first_app_config):
    """If input is disabled, but there are multiple devices, an error is raised."""
    # Multiple devices are available
    run_command.get_simulators = mock.MagicMock(
        return_value={
            "iOS 13.2": {
                "C9A005C8-9468-47C5-8376-68A6E3408209": "iPhone 8",
                "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D": "iPhone 11",
                "EEEBA06C-81F9-407C-885A-2261306DB2BE": "iPhone 11 Pro Max",
            }
        }
    )

    # Disable console input.
    run_command.tools.console.input_enabled = False

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Input has been disabled; can't select a device to target.",
    ):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_booted(run_command, first_app_config, tmp_path):
    """An iOS App can be started when the simulator is already booted."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )
    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # slept 4 times for uninstall/install and 1 time for log stream start
    assert time.sleep.call_count == 4 + 1

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_booted_underscore(
    run_command,
    underscore_app_config,
    tmp_path,
):
    """An iOS App can be started when the simulator is already booted.

    This test is specific to app names that have underscores since those are not
    supported by Apple within app identifiers.
    """
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    run_command.run_app(underscore_app_config, test_mode=False, passthrough=[])

    # slept 4 times for uninstall/install and 1 time for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )
    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first_app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        underscore_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_with_passthrough(run_command, first_app_config, tmp_path):
    """An iOS App can be started with passthrough args."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app with passthrough args.
    run_command.run_app(
        first_app_config,
        test_mode=False,
        passthrough=["foo", "--bar"],
    )

    # slept 4 times for uninstall/install and 1 time for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )
    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
            "foo",
            "--bar",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_shut_down(
    run_command,
    first_app_config,
    tmp_path,
):
    """An iOS App can be started when the simulator is shut down."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # slept 4 times for uninstall/install and 1 time for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_shutting_down(run_command, first_app_config, tmp_path):
    """An iOS App can be started when the simulator is shutting down."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shutting down. This will be returned a couple of times,
    # as the simulator will take a few seconds before it is fully shut down.
    # There will be a sleep between each call, so we need to mock sleep as well.
    run_command.get_device_state = mock.MagicMock(
        side_effect=[
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTDOWN,
        ]
    )

    run_command.sleep = mock.MagicMock()
    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # We should have slept 4 times for shutting down and 4 time for uninstall/install
    assert time.sleep.call_count == 4 + 4

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=False,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_boot_failure(run_command, first_app_config):
    """If the simulator fails to boot, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "simclt", "boot", "..."], returncode=1
    )

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # No sleeps
    assert time.sleep.call_count == 0

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
        ]
    )

    # The log will not be tailed
    run_command.tools.subprocess.Popen.assert_not_called()
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_open_failure(run_command, first_app_config):
    """If the simulator can't be opened, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot succeeds, but open fails.
    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = [
        0,
        subprocess.CalledProcessError(
            cmd=["open", "-a", "Simulator", "..."],
            returncode=1,
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # No sleeps
    assert time.sleep.call_count == 0

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )
    # The log will not be tailed
    run_command.tools.subprocess.Popen.assert_not_called()
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_uninstall_failure(run_command, first_app_config):
    """If the old app can't be uninstalled, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call uninstall fails
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 1]
    run_command.tools.subprocess.Popen.side_effect = [uninstall_popen]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Sleep twice for uninstall failure
    assert time.sleep.call_count == 2

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )
    # Start the uninstall
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
        ]
    )

    # The log will not be tailed
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_install_failure(run_command, first_app_config, tmp_path):
    """If the app fails to install in the simulator, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to install fails
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 1]
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Sleep twice for uninstall and twice for install failure
    assert time.sleep.call_count == 4

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Start the uninstall and install
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
        ]
    )

    # The log will not be tailed
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_launch_failure(run_command, first_app_config, tmp_path):
    """If the app fails to launch, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.side_effect = (
        subprocess.CalledProcessError(
            cmd=["xcrun", "simctl", "launch", "..."], returncode=1
        )
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream failed, so it won't be monitored
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_no_pid(run_command, first_app_config, tmp_path):
    """If the app fails to provide a meaningful PID on launch, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Mock a bad return value for the PID
    run_command.tools.subprocess.check_output.return_value = "No PID returned"

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # PID detection failed, so it won't be monitored
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_non_integer_pid(run_command, first_app_config, tmp_path):
    """If the PID returned isn't an integer, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Mock a bad process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: NOT A PID\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, test_mode=False, passthrough=[])

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Boot the device
            mock.call(
                ["xcrun", "simctl", "boot", "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D"],
                check=True,
            ),
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    "Simulator",
                    "--args",
                    "-CurrentDeviceUDID",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                ],
                check=True,
            ),
        ]
    )

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # PID detection failed, so it won't be called
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_test_mode(run_command, first_app_config, tmp_path):
    """An iOS App can be started in test mode."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app
    run_command.run_app(first_app_config, test_mode=True, passthrough=[])

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # Open command was not called
    run_command.tools.subprocess.run.assert_not_called()

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=True,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_test_mode_with_passthrough(run_command, first_app_config, tmp_path):
    """An iOS App can be started in test mode with passthrough args."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    # Mock a process ID for the app
    run_command.tools.subprocess.check_output.return_value = (
        "com.example.first-app: 1234\n"
    )

    # Mock the uninstall, install, and log stream Popen processes
    uninstall_popen = mock.MagicMock(spec_set=subprocess.Popen)
    uninstall_popen.__enter__.return_value = uninstall_popen
    uninstall_popen.poll.side_effect = [None, None, 0]
    install_popen = mock.MagicMock(spec_set=subprocess.Popen)
    install_popen.__enter__.return_value = install_popen
    install_popen.poll.side_effect = [None, None, 0]
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.side_effect = [
        uninstall_popen,
        install_popen,
        log_stream_process,
    ]

    # Run the app with args.
    run_command.run_app(
        first_app_config,
        test_mode=True,
        passthrough=["foo", "--bar"],
    )

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # Open command was not called
    run_command.tools.subprocess.run.assert_not_called()

    # Launch the new app
    run_command.tools.subprocess.check_output.assert_called_once_with(
        [
            "xcrun",
            "simctl",
            "launch",
            "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            "com.example.first-app",
            "foo",
            "--bar",
        ],
    )

    # Start the uninstall, install, and  log stream
    run_command.tools.subprocess.Popen.assert_has_calls(
        [
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path/build/first-app/ios/xcode/build/Debug-iphonesimulator/First App.app",
                ],
            ),
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "log",
                    "stream",
                    "--style",
                    "compact",
                    "--predicate",
                    'senderImagePath ENDSWITH "/First App"'
                    ' OR (processImagePath ENDSWITH "/First App"'
                    ' AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                    ' OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                    ' OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"))',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_config,
        popen=log_stream_process,
        test_mode=True,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )
