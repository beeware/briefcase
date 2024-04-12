from unittest.mock import MagicMock

from ...utils import NoMatchString, PartialMatchString


def test_override_is_used(convert_command):
    """The override value is used even if PEP621 data is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test-name"', encoding="utf-8"
    )
    assert convert_command.input_app_name("OVERRIDE") == "OVERRIDE"


def test_no_pep621_data(convert_command, monkeypatch):
    """The app directory is used if there is no PEP621-name."""
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)
    convert_command.base_path /= "test-app-name"
    convert_command.input_app_name(None)

    mock_input_text.assert_called_once_with(
        intro=PartialMatchString(
            "Based on your PEP508 formatted directory name, we suggest an app name of 'test-app-name'"
        ),
        variable="app name",
        default="test-app-name",
        validator=convert_command.validate_app_name,
        override_value=None,
    )


def test_valid_pep621_app_name(convert_command):
    """The PEP621-name is used if present and valid."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test-name"', encoding="utf-8"
    )
    assert convert_command.input_app_name(None) == "test-name"


def test_pep621_name_is_canonicalized(convert_command):
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test.name"', encoding="utf-8"
    )
    assert convert_command.input_app_name(None) == "test-name"


def test_invalid_hint_app_name(convert_command, monkeypatch):
    """A placeholder is used if there's no PEP621 name and the app directory is an
    invalid name."""
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)
    convert_command.base_path /= "!app_name"
    convert_command.input_app_name(None)

    mock_input_text.assert_called_once_with(
        intro=NoMatchString(
            "Based on your PEP508 formatted directory name, we suggest an app name of 'test-app-name'"
        ),
        variable="app name",
        default="hello-world",
        validator=convert_command.validate_app_name,
        override_value=None,
    )


def test_hint_is_canonicalized(convert_command, monkeypatch):
    """The app directory name is canonicalized when used as a hint."""
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)
    convert_command.base_path /= "test-app_name"
    convert_command.input_app_name(None)

    mock_input_text.assert_called_once_with(
        intro=PartialMatchString(
            "Based on your PEP508 formatted directory name, we suggest an app name of 'test-app-name'"
        ),
        variable="app name",
        default="test-app-name",
        validator=convert_command.validate_app_name,
        override_value=None,
    )
