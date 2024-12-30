def test_overrides_are_used(convert_command):
    overrides = {"gui_framework": "Toga", "console_app": "Console"}
    out = convert_command.build_gui_context({}, overrides)
    assert out == {"gui_framework": "None", "console_app": True}
    assert overrides == {"gui_framework": "Toga"}
