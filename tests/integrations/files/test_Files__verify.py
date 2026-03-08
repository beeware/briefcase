from briefcase.integrations.files import File


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.file = "tool"

    tool = File.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.file
