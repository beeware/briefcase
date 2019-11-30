import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import DeviceState, get_device_state


def simctl_result(name):
    """Load a simctl result file from the sample directory, and return the content"""
    filename = Path(__file__).parent / 'simctl' / '{name}.json'.format(name=name)
    with filename.open() as f:
        return f.read()


def test_simctl_missing():
    "If simctl is missing or fails to start, an exception is raised."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcrun', 'simctl', 'list', '-j'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        get_device_state('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', sub=sub)


def test_unknown_device():
    "If you ask for an invalid device UDID, an exception is raised."
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('no-devices')

    with pytest.raises(BriefcaseCommandError):
        get_device_state('dead-beef-dead-beef', sub=sub)


def test_known_device_booted():
    "A valid, booted device can be inspected"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('single-device-booted')

    state = get_device_state('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', sub=sub)

    assert state == DeviceState.BOOTED


def test_known_device_shutdown():
    "A valid, shut down device can be inspected"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('single-device-shutdown')

    state = get_device_state('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', sub=sub)

    assert state == DeviceState.SHUTDOWN


def test_known_device_shutting_down():
    "A valid device that is shutting down can be inspected"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('single-device-shutting-down')

    state = get_device_state('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', sub=sub)

    assert state == DeviceState.SHUTTING_DOWN


def test_known_device_unknown_status():
    "If simctl returns something unexpected as status, we can recover"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('single-device-unknown')

    state = get_device_state('2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D', sub=sub)

    assert state == DeviceState.UNKNOWN
