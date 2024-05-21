from briefcase.integrations.files import Files


def test_short_circuit(mock_tools):
    """Tool is not created if already cached."""
    mock_tools.files = "tool"

    tool = Files.verify(mock_tools)

    assert tool == "tool"
    assert tool == mock_tools.files
