import pytest

from briefcase.console import InputDisabled


def test_call_returns_user_input_when_enabled(console):
    "If input wrapper is enabled, call returns user input"
    value = "abs"
    prompt = "> "
    console._input.return_value = value

    actual_value = console(prompt=prompt)

    assert actual_value == value
    console._input.assert_called_once_with(prompt)


def test_call_raise_exception_when_disabled(disabled_console):
    "If input wrapper is disabled, call raise an exception"
    prompt = "> "

    with pytest.raises(InputDisabled):
        disabled_console(prompt=prompt)
    disabled_console._input.assert_not_called()
