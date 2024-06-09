import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.file import File


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.file = "tool"

    tool = File.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.file


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    # Delete download since it has already been verified
    delattr(mock_tools, "file")

    with pytest.raises(
        UnsupportedHostError,
        match=f"{File.name} is not supported on wonky",
    ):
        File.verify(mock_tools)


def test_verify(mock_tools):
    """Verifying Download always returns/set download tool."""
    file_tool = File.verify(mock_tools)
    assert isinstance(file_tool, File)
    assert file_tool is mock_tools.file
