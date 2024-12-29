from unittest.mock import MagicMock


def test_overrides_are_used_for_console(convert_command):
    overrides = {"console_app": "Console"}
    out = convert_command.build_gui_context({}, overrides)
    assert out["console_app"] == "true"


def test_overrides_are_used_for_GUI(convert_command):
    overrides = {"console_app": "GUI"}
    out = convert_command.build_gui_context({}, overrides)
    assert out["console_app"] == "false"


def test_input_called_properly(convert_command, monkeypatch):
    mock_select_option = MagicMock()
    monkeypatch.setattr(convert_command, "select_option", mock_select_option)

    convert_command.input_console_app(None)

    mock_select_option.assert_called_once_with(
        intro="Is this a GUI application or a console application?",
        variable="interface style",
        default=None,
        options=["GUI", "Console"],
        override_value=None,
    )


def test_input_is_used_GUI(convert_command, monkeypatch):
    convert_command.input.values = ["1"]
    out = convert_command.input_console_app(None)
    assert not out


def test_input_is_used_Console(convert_command, monkeypatch):
    convert_command.input.values = ["2"]
    out = convert_command.input_console_app(None)
    assert out
