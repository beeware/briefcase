from unittest.mock import ANY, MagicMock


def test_default_and_intro_is_used(convert_command, monkeypatch):
    mock_input_text = MagicMock()
    monkeypatch.setattr(convert_command, "input_text", mock_input_text)

    def get_source_dir_hint(*args, **kwargs):
        return "SOME_DIRECTORY", "SOME_DESCRIPTION"

    monkeypatch.setattr(convert_command, "get_source_dir_hint", get_source_dir_hint)

    convert_command.input_source_dir("app-name", "app_name", None)
    mock_input_text.assert_called_once_with(
        intro="SOME_DESCRIPTION",
        variable="source directory",
        default="SOME_DIRECTORY",
        validator=ANY,
        override_value=None,
    )


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


def test_prompted_source_dir(convert_command):
    """You can type in the source dir."""
    (convert_command.base_path / "src/app_name").mkdir(parents=True)
    (convert_command.base_path / "src/app_name" / "__main__.py").write_text(
        "", encoding="utf-8"
    )
    convert_command.input.values = ["src/app_name"]

    assert (
        convert_command.input_source_dir("app-name", "app_name", None) == "src/app_name"
    )
