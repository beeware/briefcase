import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.xcode import Xcode


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.xcode = "tool"

    tool = Xcode.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.xcode


@pytest.mark.parametrize("host_os", ["Linux", "Windows", "wonky"])
def test_unsupported_os(mock_tools, host_os):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = host_os

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Xcode.name} is not supported on {host_os}",
    ):
        Xcode.verify(mock_tools)
