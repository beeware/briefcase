import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import DeviceState, get_device_state


@pytest.fixture
def command():
    command = mock.MagicMock()
    command.subprocess = Subprocess(command)
    command.subprocess._subprocess = mock.MagicMock()
    command.subprocess.check_output = mock.MagicMock()
    return command


def simctl_result(name):
    """Load a simctl result file from the sample directory, and return the
    content."""
    filename = Path(__file__).parent / "simctl" / f"{name}.json"
    with filename.open() as f:
        return f.read()


def test_simctl_missing(command):
    """If simctl is missing or fails to start, an exception is raised."""
    command.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "simctl", "list", "-j"], returncode=1
    )

    with pytest.raises(BriefcaseCommandError, match="Unable to run xcrun simctl."):
        get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")


def test_simctl_output_parse_error(command):
    """If parsing simctl JSON output fails, an exception is raised."""
    command.subprocess.check_output.return_value = "this is not JSON"

    with pytest.raises(
        BriefcaseCommandError, match="Unable to parse output of xcrun simctl"
    ):
        get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")


def test_unknown_device(command):
    """If you ask for an invalid device UDID, an exception is raised."""
    command.subprocess.check_output.return_value = simctl_result("no-devices")

    with pytest.raises(BriefcaseCommandError):
        get_device_state(command, "dead-beef-dead-beef")


def test_known_device_booted(command):
    """A valid, booted device can be inspected."""
    command.subprocess.check_output.return_value = simctl_result("single-device-booted")

    state = get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.BOOTED


def test_known_device_shutdown(command):
    """A valid, shut down device can be inspected."""
    command.subprocess.check_output.return_value = simctl_result(
        "single-device-shutdown"
    )

    state = get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.SHUTDOWN


def test_known_device_shutting_down(command):
    """A valid device that is shutting down can be inspected."""
    command.subprocess.check_output.return_value = simctl_result(
        "single-device-shutting-down"
    )

    state = get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.SHUTTING_DOWN


def test_known_device_unknown_status(command):
    """If simctl returns something unexpected as status, we can recover."""
    command.subprocess.check_output.return_value = simctl_result(
        "single-device-unknown"
    )

    state = get_device_state(command, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.UNKNOWN
