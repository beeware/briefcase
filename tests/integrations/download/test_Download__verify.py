import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.download import Download


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.download = "tool"

    tool = Download.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.download


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    # Delete download since it has already been verified
    delattr(mock_tools, "download")

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Download.name} is not supported on wonky",
    ):
        Download.verify(mock_tools)


def test_verify(mock_tools):
    """Verifying Download always returns/set download tool."""
    download_tool = Download.verify(mock_tools)
    assert isinstance(download_tool, Download)
    assert download_tool is mock_tools.download
