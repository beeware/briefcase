from unittest.mock import MagicMock

from briefcase.config import validate_url


def test_multiple_pep621_options(convert_command, monkeypatch):
    mock_selection_question = MagicMock()
    mock_selection_question.return_value = "https://some_other_url.com/"
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    mock_selection_question.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? The "
            "following URLs are defined in your existing 'pyproject.toml'; "
            "select 'Other' to provide a different URL."
        ),
        description="Application URL",
        default="https://some_url.com/",
        options=[
            "https://some_url.com/",
            "https://some_other_url.com/",
            "Other",
        ],
        override_value=None,
    )


def test_multiple_pep621_options_select_other(convert_command, monkeypatch):
    mock_selection_question = MagicMock()
    mock_selection_question.return_value = "Other"
    monkeypatch.setattr(
        convert_command.console, "selection_question", mock_selection_question
    )

    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    mock_selection_question.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? The "
            "following URLs are defined in your existing 'pyproject.toml'; "
            "select 'Other' to provide a different URL."
        ),
        description="Application URL",
        default="https://some_url.com/",
        options=[
            "https://some_url.com/",
            "https://some_other_url.com/",
            "Other",
        ],
        override_value=None,
    )
    mock_text_question.assert_called_once_with(
        intro="What website URL do you want to use for the application?",
        description="Application URL",
        default="https://example.com/some-name",
        validator=validate_url,
    )


def test_no_pep621_options(convert_command, monkeypatch):
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)

    convert_command.input_url("some-name", None)
    default = "https://example.com/some-name"
    mock_text_question.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? Based "
            f"on your existing 'pyproject.toml', this might be {default}"
        ),
        description="Application URL",
        default=default,
        validator=validate_url,
        override_value=None,
    )


def test_override(convert_command):
    assert (
        convert_command.input_url("some-name", "https://example.com/override")
        == "https://example.com/override"
    )


def test_prompted_url(convert_command):
    """You can type in the URL."""
    convert_command.console.values = ["https://example.com/some-name"]
    assert (
        convert_command.input_url("some-name", None) == "https://example.com/some-name"
    )
