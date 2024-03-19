from unittest.mock import MagicMock


def test_default_without_http_protocol(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_bundle("http://www.some_url.no", "test-app-name", None)
    mock_input_text.assert_called_once()
    assert mock_input_text.call_args.kwargs["default"] == "no.some_url.www"
    assert "test-app-name" in mock_input_text.call_args.kwargs["intro"]


def test_default_without_https_protocol(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_bundle("https://www.some_url.no", "test-app-name", None)
    mock_input_text.assert_called_once()
    assert mock_input_text.call_args.kwargs["default"] == "no.some_url.www"
    assert "test-app-name" in mock_input_text.call_args.kwargs["intro"]


def test_override_is_used(convert_command):
    assert (
        convert_command.input_bundle("", "test-app-name", "com.overridden.project")
        == "com.overridden.project"
    )
