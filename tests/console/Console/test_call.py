import pytest

from briefcase.console import InputDisabled


def test_call_returns_user_input_when_enabled(console):
    """If input wrapper is enabled, call returns user input."""
    value = "abs"
    prompt = "> "
    console.input.return_value = value

    actual_value = console(prompt=prompt)

    assert actual_value == value
    console.input.assert_called_once_with(prompt, markup=False)


def test_call_raise_exception_when_disabled(disabled_console):
    """If input wrapper is disabled, call raise an exception."""
    prompt = "> "

    with pytest.raises(InputDisabled):
        disabled_console(prompt=prompt)
    disabled_console.input.assert_not_called()


def test_call_raise_keyboardinterrupt_for_eoferror(console):
    """Ensure KeyboardInterrupt is raised when users send EOF to an input
    prompt."""
    console.input.side_effect = EOFError()

    with pytest.raises(KeyboardInterrupt):
        console(prompt="")
