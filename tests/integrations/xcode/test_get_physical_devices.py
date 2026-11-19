import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.subprocess import Subprocess
from briefcase.integrations.xcode import (
    DEVICE_DEVELOPER_MODE_DISABLED,
    DEVICE_NOT_PAIRED,
    DEVICE_UNREACHABLE,
    get_physical_devices,
)


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.console = mock.MagicMock(spec_set=Console)
    mock_tools.subprocess = Subprocess(mock_tools)
    mock_tools.subprocess._subprocess = mock.MagicMock(spec_set=subprocess)
    mock_tools.subprocess.check_output = mock.MagicMock()
    return mock_tools


def devicectl_fixture(name):
    """Load a devicectl result file from the sample directory."""
    filename = Path(__file__).parent / "devicectl" / f"{name}.json"
    return filename.read_text(encoding="utf-8")


def test_physical_devices(mock_tools):
    """All physical devices for the requested OS are returned, with the reason any
    device isn't ready for use."""
    mock_tools.subprocess.check_output.return_value = devicectl_fixture(
        "multiple-devices"
    )

    devices = get_physical_devices(mock_tools, "iOS")

    mock_tools.subprocess.check_output.assert_called_once_with(
        ["xcrun", "devicectl", "list", "devices", "--json-output", "-", "-q"],
    )
    assert devices == {
        "00008132-000A1B2C3D4E5F60": {
            "name": "Test iPad",
            "os_version": "26.6.1",
            "not_ready": None,
        },
        "00008110-001122334455667E": {
            "name": "Test iPhone",
            "os_version": "26.0.1",
            "not_ready": None,
        },
        "00008110-00AABBCCDDEEFF00": {
            "name": "Unpaired iPhone",
            "os_version": "26.0.1",
            "not_ready": DEVICE_NOT_PAIRED,
        },
        "00008110-00FFEEDDCCBBAA00": {
            "name": "No Dev Mode iPhone",
            "os_version": "26.0.1",
            "not_ready": DEVICE_DEVELOPER_MODE_DISABLED,
        },
        "00008110-00AAAAAAAAAAAA00": {
            "name": "Offline iPhone",
            "os_version": "26.0.1",
            "not_ready": DEVICE_UNREACHABLE,
        },
    }


def test_properties_layout(mock_tools):
    """Devices described by the `properties` dictionary introduced in Xcode 27 are
    returned."""
    mock_tools.subprocess.check_output.return_value = devicectl_fixture(
        "properties-layout"
    )

    assert get_physical_devices(mock_tools, "iOS") == {
        "00008120-000123456789ABCD": {
            "name": "New Layout iPhone",
            "os_version": "27.0",
            "not_ready": None,
        },
    }


def test_devicectl_failure(mock_tools):
    """If devicectl fails, an exception is raised."""
    mock_tools.subprocess.check_output.side_effect = subprocess.CalledProcessError(
        cmd=["xcrun", "devicectl", "list", "devices"],
        returncode=1,
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to run xcrun devicectl\.",
    ):
        get_physical_devices(mock_tools, "iOS")


def test_devicectl_output_parse_error(mock_tools):
    """If the devicectl JSON output can't be parsed, an exception is raised."""
    mock_tools.subprocess.check_output.return_value = "this is not JSON"

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to parse output of xcrun devicectl",
    ):
        get_physical_devices(mock_tools, "iOS")
