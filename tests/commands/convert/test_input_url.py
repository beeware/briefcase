from unittest.mock import MagicMock


def test_multiple_pep621_options(convert_command, monkeypatch):
    m_select_option = MagicMock()
    m_select_option.return_value = "https://some_other_url.com/"
    monkeypatch.setattr(convert_command, "select_option", m_select_option)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    m_select_option.assert_called_once()
    assert m_select_option.call_args.kwargs["options"] == [
        "https://some_url.com/",
        "https://some_other_url.com/",
        "Other",
    ]


def test_multiple_pep621_options_select_other(convert_command, monkeypatch):
    m_select_option = MagicMock()
    m_select_option.return_value = "Other"
    monkeypatch.setattr(convert_command, "select_option", m_select_option)

    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n"
        'Homepage="https://some_url.com/"\n'
        'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    m_select_option.assert_called_once()
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "https://example.com/some-name"


def test_single_pep621_option(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    (convert_command.base_path / "pyproject.toml").write_text(
        "[project.urls]\n" 'Documentation="https://some_other_url.com/"',
        encoding="utf-8",
    )
    convert_command.input_url("some-name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "https://some_other_url.com/"


def test_no_pep621_options(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_url("some-name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "https://example.com/some-name"


def test_override(convert_command):
    assert (
        convert_command.input_url("some-name", "https://example.com/override")
        == "https://example.com/override"
    )
