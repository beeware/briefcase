import subprocess
from unittest import mock

import pytest

from briefcase.console import Console, Log
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import DeviceState
from briefcase.platforms.iOS.xcode import iOSXcodeRunCommand


@pytest.fixture
def run_command(tmp_path):
    return iOSXcodeRunCommand(
        logger=Log(),
        console=Console(),
        base_path=tmp_path / "base_path",
        data_path=tmp_path / "briefcase",
    )


def test_run_multiple_devices_input_disabled(run_command, first_app_config):
    """If input is disabled, but there are multiple devices, an error is
    raised."""
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
    run_command.tools.input.enabled = False

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Input has been disabled; can't select a device to target.",
    ):
        run_command.run_app(first_app_config)


def test_run_app_simulator_booted(run_command, first_app_config, tmp_path):
    """An iOS App can be started when the simulator is already booted."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is already booted
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Run the app
    run_command.run_app(first_app_config)

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path"
                    / "iOS"
                    / "Xcode"
                    / "First App"
                    / "build"
                    / "Debug-iphonesimulator"
                    / "First App.app",
                ],
                check=True,
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
                check=True,
            ),
        ]
    )
    # The log is being tailed; no process cleanup is triggered
    run_command.tools.subprocess.Popen.assert_called_with(
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
            ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    run_command.tools.subprocess.stream_output.assert_called_with(
        "log stream", log_stream_process
    )
    run_command.tools.subprocess.cleanup.assert_called_with(
        "log stream", log_stream_process
    )


def test_run_app_simulator_shut_down(run_command, first_app_config, tmp_path):
    """An iOS App can be started when the simulator is shut down."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Run the app
    run_command.run_app(first_app_config)

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path"
                    / "iOS"
                    / "Xcode"
                    / "First App"
                    / "build"
                    / "Debug-iphonesimulator"
                    / "First App.app",
                ],
                check=True,
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
                check=True,
            ),
        ]
    )
    # The log is being tailed; no process cleanup is triggered
    run_command.tools.subprocess.Popen.assert_called_with(
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
            ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    run_command.tools.subprocess.stream_output.assert_called_with(
        "log stream", log_stream_process
    )
    run_command.tools.subprocess.cleanup.assert_called_with(
        "log stream", log_stream_process
    )


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
    log_stream_process = mock.MagicMock(spec_set=subprocess.Popen)
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Run the app
    run_command.run_app(first_app_config)

    # We should have slept 4 times
    assert run_command.sleep.call_count == 4

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path"
                    / "iOS"
                    / "Xcode"
                    / "First App"
                    / "build"
                    / "Debug-iphonesimulator"
                    / "First App.app",
                ],
                check=True,
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
                check=True,
            ),
        ]
    )
    # The log is being tailed; no process cleanup has occurred
    run_command.tools.subprocess.Popen.assert_called_with(
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
            ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    run_command.tools.subprocess.stream_output.assert_called_with(
        "log stream", log_stream_process
    )
    run_command.tools.subprocess.cleanup.assert_called_with(
        "log stream", log_stream_process
    )


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
        run_command.run_app(first_app_config)

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
    run_command.tools.subprocess.stream_output.assert_not_called()
    run_command.tools.subprocess.cleanup.assert_not_called()


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
        run_command.run_app(first_app_config)

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
    run_command.tools.subprocess.stream_output.assert_not_called()
    run_command.tools.subprocess.cleanup.assert_not_called()


def test_run_app_simulator_uninstall_failure(run_command, first_app_config):
    """If the old app can't be uninstalled, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator succeed, but uninstall fails.
    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = [
        0,
        0,
        subprocess.CalledProcessError(
            cmd=["xcrun", "simctl", "uninstall", "..."], returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
        ]
    )
    # The log will not be tailed
    run_command.tools.subprocess.Popen.assert_not_called()
    run_command.tools.subprocess.stream_output.assert_not_called()
    run_command.tools.subprocess.cleanup.assert_not_called()


def test_run_app_simulator_install_failure(run_command, first_app_config, tmp_path):
    """If the app fails to install in the simulator, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator, and uninstall succeed, but install fails.
    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = [
        0,
        0,
        0,
        subprocess.CalledProcessError(
            cmd=["xcrun", "simctl", "uninstall", "..."], returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path"
                    / "iOS"
                    / "Xcode"
                    / "First App"
                    / "build"
                    / "Debug-iphonesimulator"
                    / "First App.app",
                ],
                check=True,
            ),
        ]
    )
    # The log will not be tailed
    run_command.tools.subprocess.Popen.assert_not_called()
    run_command.tools.subprocess.stream_output.assert_not_called()
    run_command.tools.subprocess.cleanup.assert_not_called()


def test_run_app_simulator_launch_failure(run_command, first_app_config, tmp_path):
    """If the app fails to launch, raise an error."""
    # A valid target device will be selected.
    run_command.select_target_device = mock.MagicMock(
        return_value=("2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D", "13.2", "iPhone 11")
    )

    # Simulator is shut down
    run_command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator, uninstall and install succeed, but launch fails.
    run_command.tools.subprocess = mock.MagicMock(spec_set=Subprocess)
    run_command.tools.subprocess.run.side_effect = [
        0,
        0,
        0,
        0,
        subprocess.CalledProcessError(
            cmd=["xcrun", "simctl", "launch", "..."], returncode=1
        ),
    ]
    log_stream_process = mock.MagicMock()
    run_command.tools.subprocess.Popen.return_value = log_stream_process

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        run_command.run_app(first_app_config)

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
            # Uninstall the old app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "uninstall",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    "com.example.first-app",
                ],
                check=True,
            ),
            # Install the new app
            mock.call(
                [
                    "xcrun",
                    "simctl",
                    "install",
                    "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D",
                    tmp_path
                    / "base_path"
                    / "iOS"
                    / "Xcode"
                    / "First App"
                    / "build"
                    / "Debug-iphonesimulator"
                    / "First App.app",
                ],
                check=True,
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
                check=True,
            ),
        ]
    )
    # The log stream process will have been started; but will not be tailed
    run_command.tools.subprocess.Popen.assert_called_with(
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
            ' AND senderImagePath ENDSWITH "-iphonesimulator.so")',
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    run_command.tools.subprocess.stream_output.assert_not_called()

    # The log process was cleaned up.
    run_command.tools.subprocess.cleanup.assert_called_once_with(
        "log stream", log_stream_process
    )
