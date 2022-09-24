import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import DeviceState, get_device_state


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.subprocess = Subprocess(mock_tools)
    mock_tools.subprocess._subprocess = mock.MagicMock(spec_set=subprocess)
    mock_tools.subprocess.check_output = mock.MagicMock()
    return mock_tools


def simctl_result(name):
    """Load a simctl result file from the sample directory, and return the
    content."""
    filename = Path(__file__).parent / "simctl" / f"{name}.json"
    with filename.open() as f:
        return f.read()


def test_simctl_missing(mock_tools):
    """If simctl is missing or fails to start, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "simctl", "list", "-j"], returncode=1
    )

    with pytest.raises(BriefcaseCommandError, match="Unable to run xcrun simctl."):
        get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")


def test_simctl_output_parse_error(mock_tools):
    """If parsing simctl JSON output fails, an exception is raised."""
    mock_tools.subprocess.check_output.return_value = "this is not JSON"

    with pytest.raises(
        BriefcaseCommandError, match="Unable to parse output of xcrun simctl"
    ):
        get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")


def test_unknown_device(mock_tools):
    """If you ask for an invalid device UDID, an exception is raised."""
    mock_tools.subprocess.check_output.return_value = simctl_result("no-devices")

    with pytest.raises(BriefcaseCommandError):
        get_device_state(mock_tools, "dead-beef-dead-beef")


def test_known_device_booted(mock_tools):
    """A valid, booted device can be inspected."""
    mock_tools.subprocess.check_output.return_value = simctl_result(
        "single-device-booted"
    )

    state = get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.BOOTED


def test_known_device_shutdown(mock_tools):
    """A valid, shut down device can be inspected."""
    mock_tools.subprocess.check_output.return_value = simctl_result(
        "single-device-shutdown"
    )

    state = get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.SHUTDOWN


def test_known_device_shutting_down(mock_tools):
    """A valid device that is shutting down can be inspected."""
    mock_tools.subprocess.check_output.return_value = simctl_result(
        "single-device-shutting-down"
    )

    state = get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.SHUTTING_DOWN


def test_known_device_unknown_status(mock_tools):
    """If simctl returns something unexpected as status, we can recover."""
    mock_tools.subprocess.check_output.return_value = simctl_result(
        "single-device-unknown"
    )

    state = get_device_state(mock_tools, "2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D")

    assert state == DeviceState.UNKNOWN
