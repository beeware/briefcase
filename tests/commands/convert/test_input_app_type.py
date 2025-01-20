import pytest


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
    convert_command.console.values = input
    out = convert_command.input_app_type(None)
    assert out == result


@pytest.mark.parametrize(
    "override, result",
    [
        # Console is any spelling generates a console app
        ("console", True),
        ("Console", True),
        # Anything else is a GUI app
        ("GUI", False),
        ("gui", False),
        ("Gui", False),
    ],
)
def test_input_app_type_override(convert_command, override, result):
    """The app type is resilient to case changes in the override value."""
    out = convert_command.input_app_type(override)
    assert out == result
