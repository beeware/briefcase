from unittest import mock


def test_app_name_is_default(new_command, monkeypatch):
    """The app name is the default project name."""
    mock_text_question = mock.MagicMock(return_value="my-app")
    monkeypatch.setattr(new_command.console, "text_question", mock_text_question)

    assert new_command.input_project_name("my-app", None) == "my-app"

    mock_text_question.assert_called_once_with(
        intro=mock.ANY,
        description="Project Name",
        default="my-app",
        validator=new_command.validate_app_name,
        override_value=None,
    )
