import pytest

from briefcase.exceptions import UnsupportedHostError
from briefcase.integrations.subprocess import NativeAppContext, Subprocess


def test_short_circuit(mock_tools, first_app_config):
    """Tool is not created if already cached."""
    mock_tools[first_app_config].app_context = "tool"

    tool = NativeAppContext.verify(mock_tools, first_app_config)

    assert tool == "tool"
    assert tool == mock_tools[first_app_config].app_context


def test_unsupported_os(mock_tools):
    """When host OS is not supported, an error is raised."""
    mock_tools.host_os = "wonky"

    with pytest.raises(
        UnsupportedHostError,
        match=f"{NativeAppContext.name} is not supported on wonky",
    ):
        NativeAppContext.verify(mock_tools, app=object())


def test_verify(mock_tools, first_app_config):
    """Subprocess verify always returns/sets subprocess tool."""
    native_app_context_tool = NativeAppContext.verify(mock_tools, first_app_config)

    assert isinstance(native_app_context_tool, Subprocess)
    assert native_app_context_tool is mock_tools[first_app_config].app_context
    # native app context should be the default subprocess tool
    assert native_app_context_tool is mock_tools.subprocess
