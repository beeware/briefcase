def test_text_input_returns_user_input_when_enabled(input_wrapper):

    prompt = "> "
    value = "Value"
    default = "Default"

    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper.text_input(prompt=prompt, default=default)

    assert actual_value == value
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_text_input_returns_default_if_user_does_not_enter_value(input_wrapper):

    prompt = "> "
    default = "Default"

    input_wrapper._actual_input.return_value = ""

    actual_value = input_wrapper.text_input(prompt=prompt, default=default)

    assert actual_value == default
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_text_input_returns_default_if_input_wrapper_is_disabled(
        disabled_input_wrapper
):

    prompt = "> "
    default = "Default"

    actual_value = disabled_input_wrapper.text_input(prompt=prompt, default=default)

    assert actual_value == default
    disabled_input_wrapper._actual_input.assert_not_called()
