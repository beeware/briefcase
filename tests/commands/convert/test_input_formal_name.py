from unittest.mock import MagicMock


def test_app_name_is_formatted(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)
    convert_command.input_formal_name("test-app-name", None)

    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["variable"] == "formal name"
    assert m_input_text.call_args.kwargs["default"] == "Test App Name"
    assert m_input_text.call_args.kwargs["override_value"] is None


def test_override_is_used(convert_command):
    assert (
        convert_command.input_formal_name("test-app-name", "OVERRIDE_VALUE")
        == "OVERRIDE_VALUE"
    )
