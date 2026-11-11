import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.console import Console
from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.base import ToolCache
from briefcase.integrations.xcode import get_physical_devices


@pytest.fixture
def mock_tools(mock_tools) -> ToolCache:
    mock_tools.console = mock.MagicMock(spec_set=Console)
    return mock_tools


def devicectl_result(content):
    """Mock a devicectl invocation that writes `content` as its JSON output."""

    def _check_output(args, **kwargs):
        json_path = Path(args[args.index("--json-output") + 1])
        json_path.write_text(content, encoding="utf-8")
        return ""

    return _check_output


def devicectl_fixture(name):
    """Load a devicectl result file from the sample directory."""
    filename = Path(__file__).parent / "devicectl" / f"{name}.json"
    return filename.read_text(encoding="utf-8")


def test_physical_devices(mock_tools):
    """Usable physical devices for the requested OS are returned, keyed by OS version;
    unusable devices are reported."""
    mock_tools.subprocess.check_output.side_effect = devicectl_result(
        devicectl_fixture("multiple-devices")
    )

    devices = get_physical_devices(mock_tools, "iOS")

    assert devices == {
        "iOS 26.6.1": {"00008132-000A1B2C3D4E5F60": "Test iPad"},
        "iOS 26.0.1": {"00008110-001122334455667E": "Test iPhone"},
    }

    assert mock_tools.console.warning.mock_calls == [
        mock.call(
            "Ignoring Unpaired iPhone; it is not paired with this Mac. Connect the "
            "device, and tap Trust when prompted."
        ),
        mock.call(
            "Ignoring No Dev Mode iPhone; Developer Mode is not enabled. Enable it "
            "in Settings > Privacy & Security > Developer Mode on the device."
        ),
        mock.call(
            "Ignoring Offline iPhone; it can't be reached. Unlock the device, and "
            "connect it to this Mac with a cable, or to the same network as this Mac."
        ),
    ]


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
    mock_tools.subprocess.check_output.side_effect = devicectl_result(
        "this is not JSON"
    )

    with pytest.raises(
        BriefcaseCommandError,
        match=r"Unable to parse output of xcrun devicectl",
    ):
        get_physical_devices(mock_tools, "iOS")
