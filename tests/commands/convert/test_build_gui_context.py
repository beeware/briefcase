def test_overrides_are_used_for_console(convert_command):
    overrides = {"gui_framework": "Toga", "console_app": "Console"}
    out = convert_command.build_gui_context({}, overrides)
    assert out["gui_framework"] == "None"
    assert overrides["gui_framework"] == "Toga"
    assert out["console_app"] == "true"


def test_overrides_are_used_for_GUI(convert_command):
    overrides = {"console_app": "GUI"}
    out = convert_command.build_gui_context({}, overrides)
    assert out["gui_framework"] == "None"
    assert out["console_app"] == "false"
