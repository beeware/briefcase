from unittest.mock import MagicMock

from ...utils import PartialMatchString


def test_app_name_is_formatted(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
    convert_command.input_formal_name("test-app-name", None)

    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(
            "Based on the app name, we suggest a formal name of 'Test App Name',"
        ),
        description="Formal Name",
        default="Test App Name",
        override_value=None,
    )


def test_override_is_used(convert_command):
    assert (
        convert_command.input_formal_name("test-app-name", "OVERRIDE_VALUE")
        == "OVERRIDE_VALUE"
    )


def test_prompted_formal_name(convert_command):
    """You can type in the formal name."""
    convert_command.console.values = ["My Formal Name"]
    assert convert_command.input_formal_name("app-name", None) == "My Formal Name"
