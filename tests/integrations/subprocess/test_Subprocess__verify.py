from briefcase.integrations.subprocess import Subprocess


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.subprocess = "tool"

    tool = Subprocess.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.subprocess


def test_verify(mock_tools):
    """Subprocess verify always returns/sets subprocess tool."""
    subprocess_tool = Subprocess.verify(mock_tools)
    assert isinstance(subprocess_tool, Subprocess)
    assert subprocess_tool is mock_tools.subprocess
