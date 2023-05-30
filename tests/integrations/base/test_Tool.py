from unittest.mock import MagicMock

import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.base import Tool


class DummyTool(Tool):
    """Unmanaged Tool testing class."""

    name = "UnmanagedDummyTool"
    full_name = "Unmanaged Dummy Tool"
    supported_host_os = {"wonky"}

    @classmethod
    def verify_install(cls, tools, **kwargs):
        return f"i'm a {cls.name}"


@pytest.fixture
def unmanaged_tool(mock_tools) -> DummyTool:
    return DummyTool(tools=mock_tools)


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyTool, {}),
        (DummyTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify(mock_tools, klass, kwargs, monkeypatch):
    """Tool verification checks host OS and tool install."""
    # Wrap verify calls to confirm they were called
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    # Mock the dummy tool's supported OS
    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(tools=mock_tools, app=None, **kwargs)
    assert tool == f"i'm a {klass.name}"


@pytest.mark.parametrize(
    "klass, kwargs",
    [
        (DummyTool, {}),
        (DummyTool, {"one": "two", "three": "four"}),
    ],
)
def test_tool_verify_with_app(mock_tools, first_app_config, klass, kwargs, monkeypatch):
    """App-bound Tool verification checks host OS and tool install."""
    # Wrap verify calls to confirm they were called
    mock_verify_host = MagicMock(wraps=klass.verify_host)
    monkeypatch.setattr(klass, "verify_host", mock_verify_host)
    mock_verify_install = MagicMock(wraps=klass.verify_install)
    monkeypatch.setattr(klass, "verify_install", mock_verify_install)

    # Mock the dummy tool's supported OS
    mock_tools.host_os = "wonky"

    tool = klass.verify(tools=mock_tools, app=first_app_config, **kwargs)

    mock_verify_host.assert_called_once_with(tools=mock_tools)
    mock_verify_install.assert_called_once_with(
        tools=mock_tools,
        app=first_app_config,
        **kwargs,
    )
    assert tool == "i'm a UnmanagedDummyTool"


def test_tool_unsupported_host_os(mock_tools):
    """Tool verification fails for unsupported Host OS."""
    mock_tools.host_os = "not wonky"

    with pytest.raises(
        UnsupportedHostError,
        match="UnmanagedDummyTool is not supported on not wonky",
    ):
        DummyTool.verify(tools=mock_tools)
