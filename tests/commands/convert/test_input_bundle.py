from unittest.mock import MagicMock

from ...utils import PartialMatchString


def test_default_without_http_protocol(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_bundle("http://www.some_url.no", "test-app-name", None)
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString("no.some_url.www.test-app-name"),
        variable="bundle identifier",
        default="no.some_url.www",
        validator=convert_command.validate_bundle,
        override_value=None,
    )


def test_default_without_https_protocol(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    convert_command.input_bundle("https://www.some_url.no", "test-app-name", None)
    mock_input_text.assert_called_once_with(
        intro=PartialMatchString("no.some_url.www.test-app-name"),
        variable="bundle identifier",
        default="no.some_url.www",
        validator=convert_command.validate_bundle,
        override_value=None,
    )


def test_override_is_used(convert_command):
    assert (
        convert_command.input_bundle("", "test-app-name", "com.overridden.project")
        == "com.overridden.project"
    )


def test_prompted_bundle(convert_command):
    """You can type in the bundle name."""
    convert_command.input.values = ["com.some.project"]
    assert convert_command.input_bundle("", "test-app-name", None) == "com.some.project"
