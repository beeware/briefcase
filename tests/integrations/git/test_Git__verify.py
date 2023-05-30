import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.git import Git


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.git = "tool"

    tool = Git.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.git


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{Git.name} is not supported on wonky",
    ):
        Git.verify(mock_tools)
