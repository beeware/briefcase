import pytest

from briefcase.console import InputWrapperDisabledError


def test_call_returns_user_input_when_enabled(input_wrapper):
    "If input wrapper is enabled, call returns user input"
    value = "abs"
    prompt = "> "
    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper(prompt=prompt)

    assert actual_value == value
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_call_raise_exception_when_disabled(disabled_input_wrapper):
    "If input wrapper is disabled, call raise an exception"
    prompt = "> "

    with pytest.raises(InputWrapperDisabledError):
        disabled_input_wrapper(prompt=prompt)
    disabled_input_wrapper._actual_input.assert_not_called()
