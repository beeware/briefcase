import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.subprocess import Subprocess


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.subprocess = "tool"

    tool = Subprocess.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.subprocess


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    # Delete subprocess since it has already been verified
    delattr(mock_tools, "subprocess")

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Subprocess.name} is not supported on wonky",
    ):
        Subprocess.verify(mock_tools)


def test_verify(mock_tools):
    """Subprocess verify always returns/sets subprocess tool."""
    subprocess_tool = Subprocess.verify(mock_tools)
    assert isinstance(subprocess_tool, Subprocess)
    assert subprocess_tool is mock_tools.subprocess
