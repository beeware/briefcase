import pytest


def test_overrides_are_used_for_console(convert_command):
    overrides = {"console_app": "Console"}
    out = convert_command.build_gui_context({}, overrides)
    assert out == {"console_app": True, "gui_framework": "None"}


def test_overrides_are_used_for_GUI(convert_command):
    overrides = {"console_app": "GUI"}
    out = convert_command.build_gui_context({}, overrides)
    assert out == {"console_app": False, "gui_framework": "None"}


@pytest.mark.parametrize(
    "input, result",
    [
        # A GUI app
        (["1"], False),
        # A console app
        (["2"], True),
        # Default value is False (GUI app)
        ([""], False),
        # Invalid values are rejected until a valid value is provided.
        (["x", "y", "2"], True),
    ],
)
def test_app_type(convert_command, input, result):
    """The user can be asked for the app type."""
    convert_command.input.values = input
    out = convert_command.input_console_app(None)
    assert out == result
