import json
import platform
import subprocess
import time
from unittest import mock

import pytest
from packaging.version import Version

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import DeviceState
from briefcase.platforms.iOS.xcode import (
    iOSDevice,
    iOSSigningIdentity,
    iOSXcodeRunCommand,
)
from briefcase.platforms.macOS import macOS_log_clean_filter
from briefcase.platforms.macOS.filters import nslog_clean_filter


@pytest.fixture
def run_command(dummy_console, tmp_path):
    command = iOSXcodeRunCommand(
        console=dummy_console,
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )
    command.tools.home_path = tmp_path / "home"
    command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    command._stream_app_logs = mock.MagicMock()

    command.tools.xcode = mock.MagicMock()
    command.tools.xcode.version = Version("27.0")

    # By default, no physical devices are connected.
    command.get_physical_devices = mock.MagicMock(return_value={})

    # To satisfy coverage, the stop function must be invoked
    # at least once when streaming app logs.
    def mock_stream_app_logs(app, stop_func, **kwargs):
        stop_func()

    command._stream_app_logs.side_effect = mock_stream_app_logs

    return command


def test_device_option(run_command):
    """The -d and -i options can be parsed."""
    options, overrides = run_command.parse_options(
        ["-d", "myphone", "-i", "Apple Development: jane@example.com (MEMBER1234)"]
    )

    assert options == {
        "udid": "myphone",
        "identity": "Apple Development: jane@example.com (MEMBER1234)",
        "update": False,
        "update_requirements": False,
        "update_resources": False,
        "update_support": False,
        "update_stub": False,
        "no_update": False,
        "test_mode": False,
        "passthrough": [],
        "debugger": None,
        "debugger_host": "localhost",
        "debugger_port": 5678,
        "appname": None,
    }
    assert overrides == {}


def test_prepare_target_simulator(run_command, first_app_config):
    """If a simulator is selected, no signing identity is required."""
    simulator = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
    )
    run_command.select_target_device = mock.MagicMock(return_value=simulator)
    run_command.select_identity = mock.MagicMock()

    build_required = run_command.prepare_target(
        first_app_config,
        udid="iPhone 11",
        identity=None,
    )

    # The simulator is the target, and no build is forced.
    assert run_command.target_device == simulator
    assert run_command.signing_identity is None
    assert not build_required
    run_command.select_target_device.assert_called_once_with("iPhone 11")
    run_command.select_identity.assert_not_called()


def test_prepare_target_physical_device(run_command, first_app_config):
    """If a physical device is selected, a signing identity is selected, and the app
    must be built."""
    device = iOSDevice(
        "00008110-001122334455667E",
        "26.0.1",
        "Test iPhone",
        physical=True,
    )
    identity = iOSSigningIdentity(
        id="22222222222222222222222222222222222222BB",
        name="Apple Development: jane@example.com (MEMBER1234)",
        team_id="TEAM123456",
    )
    run_command.select_target_device = mock.MagicMock(return_value=device)
    run_command.select_identity = mock.MagicMock(return_value=identity)

    build_required = run_command.prepare_target(
        first_app_config,
        udid="Test iPhone",
        identity="22222222222222222222222222222222222222BB",
    )

    # The device and identity are the target, and a build is required.
    assert run_command.target_device == device
    assert run_command.signing_identity == identity
    assert build_required
    run_command.select_identity.assert_called_once_with(
        "22222222222222222222222222222222222222BB"
    )


def test_target_cloned_to_build_command(run_command):
    """The selected device and signing identity are used by the build command."""
    run_command.target_device = iOSDevice(
        "00008110-001122334455667E",
        "26.0.1",
        "Test iPhone",
        physical=True,
    )
    run_command.signing_identity = iOSSigningIdentity(
        id="22222222222222222222222222222222222222BB",
        name="Apple Development: jane@example.com (MEMBER1234)",
        team_id="TEAM123456",
    )

    build_command = run_command.build_command

    assert build_command.target_device == run_command.target_device
    assert build_command.signing_identity == run_command.signing_identity


def test_prepare_target_input_disabled(run_command, first_app_config):
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
        match=r"Input has been disabled; can't select a device or signing identity\.",
    ):
        run_command.prepare_target(first_app_config, udid=None, identity=None)


@pytest.mark.usefixtures("sleep_zero")
@pytest.mark.parametrize(
    ("xcode_version", "sim_start_args"),
    [
        (
            "16.4",
            [
                "Simulator",
                "--args",
                "-CurrentDeviceUDID",
                "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
            ],
        ),
        ("27.0", ["Device Hub"]),
    ],
)
def test_run_app_simulator_booted(
    run_command,
    first_app_config,
    xcode_version,
    sim_start_args,
    tmp_path,
):
    """An iOS App can be started when the simulator is already booted."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
    )

    # Set up the Xcode version
    run_command.tools.xcode.version = Version(xcode_version)

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
    run_command.run_app(first_app_config, passthrough=[])

    # The correct sequence of commands was issued.
    run_command.tools.subprocess.run.assert_has_calls(
        [
            # Open the simulator
            mock.call(
                [
                    "open",
                    "-a",
                    *sim_start_args,
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
    run_command.run_app(underscore_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first_app/ios/xcode/build"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_with_passthrough(run_command, first_app_config, tmp_path):
    """An iOS App can be started with passthrough args."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
    run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_shutting_down(run_command, first_app_config, tmp_path):
    """An iOS App can be started when the simulator is shutting down."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
    run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_boot_failure(run_command, first_app_config):
    """If the simulator fails to boot, raise an error."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "simclt", "boot", "..."], returncode=1
    )

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config, passthrough=[])

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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
                ],
            ),
        ]
    )

    # The log will not be tailed
    run_command._stream_app_logs.assert_not_called()


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_simulator_launch_failure(run_command, first_app_config, tmp_path):
    """If the app fails to launch, raise an error."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
        run_command.run_app(first_app_config, passthrough=[])

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
                    "Device Hub",
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
    first_app_config.test_mode = True

    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
    run_command.run_app(first_app_config, passthrough=[])

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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_test_mode_with_passthrough(run_command, first_app_config, tmp_path):
    """An iOS App can be started in test mode with passthrough args."""
    first_app_config.test_mode = True

    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
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
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


@pytest.mark.usefixtures("sleep_zero")
def test_run_app_debugger(run_command, first_app_generated, tmp_path, dummy_debugger):
    """An iOS App can be started in debug mode."""
    # A simulator has been selected as the target device.
    run_command.target_device = iOSDevice(
        "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
        "13.2",
        "iPhone 11",
        physical=False,
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

    first_app_generated.debugger = dummy_debugger
    first_app_generated.debugger_host = "somehost"
    first_app_generated.debugger_port = 9999

    # Run the app
    run_command.run_app(first_app_generated, passthrough=[])

    # Sleep four times for uninstall/install and once for log stream start
    assert time.sleep.call_count == 4 + 1

    # Set the environment variables for the debugger and launch the app
    run_command.tools.subprocess.check_output.assert_has_calls(
        [
            # Set the environment variables for the debugger
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "launchctl",
                    "setenv",
                    "BRIEFCASE_DEBUGGER",
                    json.dumps(
                        {
                            "debugger": "dummy",
                            "host": "somehost",
                            "port": 9999,
                            "host_os": platform.system(),
                            "app_path_mappings": {
                                "device_sys_path_regex": "app$",
                                "device_subfolders": ["first_app"],
                                "host_folders": [
                                    str(tmp_path / "base_path/src/first_app")
                                ],
                            },
                            "app_packages_path_mappings": {
                                "sys_path_regex": "app_packages$",
                                "host_folder": str(
                                    tmp_path
                                    / "base_path/build/first-app/ios/xcode/"
                                    / "app_packages.iphonesimulator"
                                ),
                            },
                        }
                    ),
                ],
            ),
            # Launch the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "launch",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
            ),
            # Remove the environment variables for the debugger
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "spawn",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "launchctl",
                    "unsetenv",
                    "BRIEFCASE_DEBUGGER",
                ],
            ),
        ]
    )

    # Start the uninstall, install, and log stream
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
                    / "base_path/build/first-app/ios/xcode/build/"
                    / "Debug-iphonesimulator/First App.app",
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
                    (
                        'senderImagePath ENDSWITH "/First App"'
                        'OR (processImagePath ENDSWITH "/First App"'
                        '  AND (senderImagePath ENDSWITH "-iphonesimulator.so"'
                        '    OR senderImagePath ENDSWITH "-iphonesimulator.dylib"'
                        '    OR senderImagePath ENDSWITH "_ctypes.framework/_ctypes"'
                        '    OR senderImagePath ENDSWITH "/Python"'
                        "  )"
                        ")"
                    ),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
            ),
        ]
    )

    # Log stream monitoring was started
    run_command._stream_app_logs.assert_called_with(
        first_app_generated,
        popen=log_stream_process,
        clean_filter=macOS_log_clean_filter,
        clean_output=True,
        stop_func=mock.ANY,
        log_stream=True,
    )


def test_run_app_physical_device(
    run_command,
    first_app_generated,
    tmp_path,
    dummy_debugger,
):
    """An iOS App can be installed and started on a physical device, with its console
    output streamed."""
    run_command.target_device = iOSDevice(
        "00008110-001122334455667E",
        "26.0.1",
        "Test iPhone",
        physical=True,
    )
    launch_popen = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = launch_popen
    run_command._stream_app_logs.side_effect = None

    first_app_generated.debugger = dummy_debugger
    first_app_generated.debugger_host = "somehost"
    first_app_generated.debugger_port = 9999

    state = run_command.run_app(first_app_generated, passthrough=["foo", "--bar"])

    # The app was installed on the device
    run_command.tools.subprocess.run.assert_called_once_with(
        [
            "xcrun",
            "devicectl",
            "device",
            "install",
            "app",
            "-q",
            "--device",
            "00008110-001122334455667E",
            tmp_path
            / "base_path/build/first-app/ios/xcode/build/"
            / "Debug-iphoneos/First App.app",
        ],
        check=True,
    )

    # The app was launched with the console attached, sending Python output to
    # the console, and using the device's app packages for the debugger.
    run_command.tools.subprocess.Popen.assert_called_once_with(
        [
            "xcrun",
            "devicectl",
            "device",
            "process",
            "launch",
            "-q",
            "--device",
            "00008110-001122334455667E",
            "--console",
            "--terminate-existing",
            "--environment-variables",
            json.dumps(
                {
                    "BRIEFCASE_CONSOLE_OUTPUT": "1",
                    "BRIEFCASE_DEBUGGER": json.dumps(
                        {
                            "debugger": "dummy",
                            "host": "somehost",
                            "port": 9999,
                            "host_os": platform.system(),
                            "app_path_mappings": {
                                "device_sys_path_regex": "app$",
                                "device_subfolders": ["first_app"],
                                "host_folders": [
                                    str(tmp_path / "base_path/src/first_app")
                                ],
                            },
                            "app_packages_path_mappings": {
                                "sys_path_regex": "app_packages$",
                                "host_folder": str(
                                    tmp_path
                                    / "base_path/build/first-app/ios/xcode/"
                                    / "app_packages.iphoneos"
                                ),
                            },
                        }
                    ),
                }
            ),
            "com.example.first-app",
            "foo",
            "--bar",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    # The console output was streamed
    run_command._stream_app_logs.assert_called_once_with(
        first_app_generated,
        popen=launch_popen,
        clean_filter=nslog_clean_filter,
        clean_output=True,
    )

    # The device selection is preserved as state
    assert state == {"udid": "00008110-001122334455667E"}


def test_run_app_physical_device_install_failure(run_command, first_app_generated):
    """If the app can't be installed on a physical device, an error is raised."""
    run_command.target_device = iOSDevice(
        "00008110-001122334455667E",
        "26.0.1",
        "Test iPhone",
        physical=True,
    )
    run_command.tools.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "devicectl", "device", "install", "app"],
        returncode=1,
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to install new version of app first-app\.",
    ):
        run_command.run_app(first_app_generated, passthrough=[])

    # The app wasn't launched
    run_command.tools.subprocess.Popen.assert_not_called()
