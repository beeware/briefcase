from unittest.mock import MagicMock


def test_default_without_url_protocol(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_bundle("www.some_url.no", "test-app-name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "no.some_url.www"
    assert "test-app-name" in m_input_text.call_args.kwargs["intro"]


def test_default_without_http_protocol(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_bundle("http://www.some_url.no", "test-app-name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "no.some_url.www"
    assert "test-app-name" in m_input_text.call_args.kwargs["intro"]


def test_default_without_https_protocol(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    convert_command.input_bundle("https://www.some_url.no", "test-app-name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["default"] == "no.some_url.www"
    assert "test-app-name" in m_input_text.call_args.kwargs["intro"]


def test_override_is_used(convert_command):
    assert (
        convert_command.input_bundle("", "test-app-name", "com.overridden.project")
        == "com.overridden.project"
    )
