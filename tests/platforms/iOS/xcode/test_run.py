import subprocess
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import DeviceState
from briefcase.platforms.iOS.xcode import iOSXcodeRunCommand


def test_run_app_simulator_booted(first_app_config, tmp_path):
    "An iOS App can be started when the simulator is already booted"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is already booted
    command.get_device_state = mock.MagicMock(return_value=DeviceState.BOOTED)

    command.subprocess = mock.MagicMock()

    # Run the app
    command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
        # Install the new app
        mock.call(
            [
                'xcrun', 'simctl', 'install',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
            ],
            check=True
        ),
        # Launch the new app
        mock.call(
            [
                'xcrun', 'simctl', 'launch',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        )
    ])


def test_run_app_simulator_shut_down(first_app_config, tmp_path):
    "An iOS App can be started when the simulator is shut down"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    command.subprocess = mock.MagicMock()

    # Run the app
    command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
        # Install the new app
        mock.call(
            [
                'xcrun', 'simctl', 'install',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
            ],
            check=True
        ),
        # Launch the new app
        mock.call(
            [
                'xcrun', 'simctl', 'launch',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        )
    ])


def test_run_app_simulator_shutting_down(first_app_config, tmp_path):
    "An iOS App can be started when the simulator is shutting down"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shutting down. This will be returned a couple of times,
    # as the simulator will take a few seconds before it is fully shut down.
    # There will be a sleep between each call, so we need to mock sleep as well.
    command.get_device_state = mock.MagicMock(
        side_effect=[
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTTING_DOWN,
            DeviceState.SHUTDOWN
        ]
    )

    command.sleep = mock.MagicMock()
    command.subprocess = mock.MagicMock()

    # Run the app
    command.run_app(first_app_config)

    # We should have slept 3 times
    assert command.sleep.call_count == 3

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
        # Install the new app
        mock.call(
            [
                'xcrun', 'simctl', 'install',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
            ],
            check=True
        ),
        # Launch the new app
        mock.call(
            [
                'xcrun', 'simctl', 'launch',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        )
    ])


def test_run_app_simulator_boot_failure(first_app_config, tmp_path):
    "If the simulator fails to boot, raise an error"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = subprocess.CalledProcessError(
        cmd=['xcrun', 'simclt', 'boot', '...'],
        returncode=1
    )

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
    ])


def test_run_app_simulator_open_failure(first_app_config, tmp_path):
    "If the simulator can't be opened, raise an error"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot succeeds, but open fails.
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = [
        0,
        subprocess.CalledProcessError(
            cmd=['open', '-a', 'Simulator', '...'],
            returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
    ])


def test_run_app_simulator_uninstall_failure(first_app_config, tmp_path):
    "If the old app can't be uninstalled, raise an error"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator succeed, but uninstall fails.
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = [
        0,
        0,
        subprocess.CalledProcessError(
            cmd=['xcrun', 'simctl', 'uninstall', '...'],
            returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
    ])


def test_run_app_simulator_install_failure(first_app_config, tmp_path):
    "If the app fails to install in the simulator, raise an error"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator, and uninstall succeed, but install fails.
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = [
        0,
        0,
        0,
        subprocess.CalledProcessError(
            cmd=['xcrun', 'simctl', 'uninstall', '...'],
            returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
        # Install the new app
        mock.call(
            [
                'xcrun', 'simctl', 'install',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
            ],
            check=True
        ),
    ])


def test_run_app_simulator_launch_failure(first_app_config, tmp_path):
    "If the app fails to launch, raise an error"
    command = iOSXcodeRunCommand(base_path=tmp_path)

    # A valid target device will be selected.
    command.select_target_device = mock.MagicMock(
        return_value=(
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', '13.2', 'iPhone 11'
        )
    )

    # Simulator is shut down
    command.get_device_state = mock.MagicMock(return_value=DeviceState.SHUTDOWN)

    # Call to boot and open simulator, uninstall and install succeed, but launch fails.
    command.subprocess = mock.MagicMock()
    command.subprocess.run.side_effect = [
        0,
        0,
        0,
        0,
        subprocess.CalledProcessError(
            cmd=['xcrun', 'simctl', 'uninstall', '...'],
            returncode=1
        ),
    ]

    # Run the app
    with pytest.raises(BriefcaseCommandError):
        command.run_app(first_app_config)

    # The correct sequence of commands was issued.
    command.subprocess.run.assert_has_calls([
        # Boot the device
        mock.call(
            ['xcrun', 'simctl', 'boot', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'],
            check=True,
        ),
        # Open the simulator
        mock.call(
            [
                'open',
                '-a', 'Simulator',
                '--args',
                '-CurrentDeviceUDID', '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D'
            ],
            check=True
        ),
        # Uninstall the old app
        mock.call(
            [
                'xcrun', 'simctl', 'uninstall',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        ),
        # Install the new app
        mock.call(
            [
                'xcrun', 'simctl', 'install',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                tmp_path / 'iOS' / 'First App' / 'build' / 'Debug-iphonesimulator' / 'First App.app'
            ],
            check=True
        ),
        # Launch the new app
        mock.call(
            [
                'xcrun', 'simctl', 'launch',
                '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D',
                'com.example.first-app'
            ],
            check=True
        )
    ])
