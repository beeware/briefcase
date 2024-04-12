from unittest.mock import MagicMock


def test_multiple_pep621_options(convert_command, monkeypatch):
    mock_select_option = MagicMock()
    mock_select_option.return_value = "https://some_other_url.com/"
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    mock_select_option.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? The "
            "following URLs are defined in your existing 'pyproject.toml'; "
            "select 'Other' to provide a different URL."
        ),
        variable="application URL",
        default=None,
        options=[
            "https://some_url.com/",
            "https://some_other_url.com/",
            "Other",
        ],
        override_value=None,
    )


def test_multiple_pep621_options_select_other(convert_command, monkeypatch):
    mock_select_option = MagicMock()
    mock_select_option.return_value = "Other"
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    mock_select_option.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? The "
            "following URLs are defined in your existing 'pyproject.toml'; "
            "select 'Other' to provide a different URL."
        ),
        variable="application URL",
        default=None,
        options=[
            "https://some_url.com/",
            "https://some_other_url.com/",
            "Other",
        ],
        override_value=None,
    )
    mock_input_text.assert_called_once_with(
        intro="What website URL do you want to use for the application?",
        variable="application URL",
        default="https://example.com/some-name",
        validator=convert_command.validate_url,
    )


def test_no_pep621_options(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_url("some-name", None)
    default = "https://example.com/some-name"
    mock_input_text.assert_called_once_with(
        intro=(
            "What website URL do you want to use for this application? Based "
            f"on your existing 'pyproject.toml', this might be {default}"
        ),
        variable="application URL",
        default=default,
        validator=convert_command.validate_url,
        override_value=None,
    )


def test_override(convert_command):
    assert (
        convert_command.input_url("some-name", "https://example.com/override")
        == "https://example.com/override"
    )


def test_prompted_url(convert_command):
    """You can type in the URL."""
    convert_command.input.values = ["https://example.com/some-name"]
    assert (
        convert_command.input_url("some-name", None) == "https://example.com/some-name"
    )
