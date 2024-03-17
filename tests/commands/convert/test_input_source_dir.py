from unittest.mock import MagicMock


def test_default_and_intro_is_used(convert_command, monkeypatch):
    m_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", m_input_text)

    def get_source_dir_hint(*args, **kwargs):
        return "SOME_DIRECTORY", "SOME_DESCRIPTION"

    monkeypatch.setattr(convert_command, "get_source_dir_hint", get_source_dir_hint)

    convert_command.input_source_dir("app-name", "app_name", None)
    m_input_text.assert_called_once()
    assert m_input_text.call_args.kwargs["intro"] == "SOME_DESCRIPTION"
    assert m_input_text.call_args.kwargs["default"] == "SOME_DIRECTORY"


def test_default_and_intro_uses_override(convert_command, monkeypatch):
    def get_source_dir_hint(*args, **kwargs):
        return "SOME_DIRECTORY", "SOME_DESCRIPTION"

    monkeypatch.setattr(convert_command, "get_source_dir_hint", get_source_dir_hint)
    (convert_command.base_path / "OVERRIDE_VALUE" / "app_name").mkdir(parents=True)
    (
        convert_command.base_path / "OVERRIDE_VALUE" / "app_name" / "__main__.py"
    ).write_text("", encoding="utf-8")
    assert (
        convert_command.input_source_dir(
            "app-name", "app_name", "OVERRIDE_VALUE/app_name"
        )
        == "OVERRIDE_VALUE/app_name"
    )
