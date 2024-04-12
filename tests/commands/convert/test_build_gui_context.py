def test_overrides_are_not_used(convert_command):
    overrides = {"gui_framework": "Toga"}
    out = convert_command.build_gui_context({}, overrides)
    assert out == {"gui_framework": "None"}
    assert overrides == {"gui_framework": "Toga"}
