import pytest
from rich.markup import escape

from briefcase.console import InputDisabled
from tests.utils import default_rich_prompt


def test_call_returns_user_input_when_enabled(console):
    """If input wrapper is enabled, call returns user input."""
    value = "abs"
    prompt = "> "
    console._console_impl.input.return_value = value

    actual_value = console.input(prompt=prompt)

    assert actual_value == value
    console._console_impl.input.assert_called_once_with(
        default_rich_prompt(prompt), markup=True
    )


def test_call_returns_user_input_when_enabled_with_markup_prompt(console):
    """If input wrapper is enabled, call returns user input with a prompt with existing
    markup."""
    value = "abs"
    prompt = f"[red]{escape('this is prompt with escaped [markup] text')}[/red]"
    console._console_impl.input.return_value = value

    actual_value = console.input(prompt=prompt, markup=True)

    assert actual_value == value
    console._console_impl.input.assert_called_once_with(prompt, markup=True)


def test_call_raise_exception_when_disabled(disabled_console):
    """If input wrapper is disabled, call raise an exception."""
    prompt = "> "

    with pytest.raises(InputDisabled):
        disabled_console.input(prompt=prompt)
    disabled_console._console_impl.input.assert_not_called()


def test_call_raise_keyboardinterrupt_for_eoferror(console):
    """Ensure KeyboardInterrupt is raised when users send EOF to an input prompt."""
    console._console_impl.input.side_effect = EOFError()

    with pytest.raises(KeyboardInterrupt):
        console.input(prompt="")
