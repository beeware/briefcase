from unittest.mock import MagicMock

import pytest

from ...utils import NoMatchString, PartialMatchString


def test_override_is_used(convert_command):
    """The override value is used even if PEP621 data is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test-name"', encoding="utf-8"
    )
    assert convert_command.input_app_name("OVERRIDE") == "OVERRIDE"


@pytest.mark.parametrize(
    ("dir_name", "expected_suggestion"),
    [
        ("test-app-name", "test-app-name"),
        ("test_app-name", "test-app-name"),
    ],
)
def test_no_pep621_data(convert_command, monkeypatch, dir_name, expected_suggestion):
    """The app directory is used if there is no PEP621-name."""
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
    convert_command.base_path /= dir_name
    convert_command.input_app_name(None)

    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(
            "Based on your canonicalized directory name, we suggest an app name of"
            f" '{expected_suggestion}'"
        ),
        description="App Name",
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


def test_pep621_name_is_canonicalized(convert_command, monkeypatch):
    """The canonicalized version of the PEP621-name is used if the name is present and
    is not valid, but its canonicalized version is."""
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test.name"', encoding="utf-8"
    )
    convert_command.input_app_name(None)

    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(
            "Based on the project name from your PEP621 formatted pyproject.toml, "
            "we suggest an app name of 'test-name'"
        ),
        description="App Name",
        default="test-name",
        validator=convert_command.validate_app_name,
        override_value=None,
    )


def test_invalid_hint_app_name(convert_command, monkeypatch):
    """A placeholder is used if there's no PEP621 name and the app directory is an
    invalid name."""
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
    convert_command.base_path /= "!app_name"
    convert_command.input_app_name(None)

    mock_text_question.assert_called_once_with(
        intro=NoMatchString(
            "Based on your canonicalized directory name, we suggest an app name of"
            " 'test-app-name'"
        ),
        description="App Name",
        default="hello-world",
        validator=convert_command.validate_app_name,
        override_value=None,
    )


def test_hint_is_canonicalized(convert_command, monkeypatch):
    """The app directory name is canonicalized when used as a hint."""
    mock_text_question = MagicMock()
    monkeypatch.setattr(convert_command.console, "text_question", mock_text_question)
    convert_command.base_path /= "test-app_name"
    convert_command.input_app_name(None)

    mock_text_question.assert_called_once_with(
        intro=PartialMatchString(
            "Based on your canonicalized directory name, we suggest an app name of"
            " 'test-app-name'"
        ),
        description="App Name",
        default="test-app-name",
        validator=convert_command.validate_app_name,
        override_value=None,
    )
