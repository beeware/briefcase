from unittest.mock import MagicMock


def test_override_is_used(convert_command):
    """The override value is used even if PEP621 data is present."""
    (convert_command.base_path / "pyproject.toml").write_text(
        '[project]\nname="test-name"', encoding="utf-8"
    )
    assert convert_command.input_app_name("OVERRIDE") == "OVERRIDE"


def test_no_pep621_data(convert_command, monkeypatch):
    """The app directory is used if there is no PEP621-name."""
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)
    convert_command.base_path /= "test-app-name"
    convert_command.input_app_name(None)

    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["variable"] == "app name"
    assert m_input_text.call_args.kwargs["default"] == "test-app-name"


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
    """A placeholder is used if both the PEP621-name and the app directory has invalid
    names."""
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)
    convert_command.base_path /= "!app_name"
    convert_command.input_app_name(None)

    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["variable"] == "app name"
    assert m_input_text.call_args.kwargs["default"] == "hello-world"


def test_hint_is_canonicalized(convert_command, monkeypatch):
    """The app directory name is canonicalized."""
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)
    convert_command.base_path /= "test-app_name"
    convert_command.input_app_name(None)

    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["variable"] == "app name"
    assert m_input_text.call_args.kwargs["default"] == "test-app-name"
