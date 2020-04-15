from unittest.mock import call


def test_selection_input_returns_first_option(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    value = options[0]

    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 choices=options)

    assert actual_value == value
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_selection_input_returns_middle_option(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    value = options[2]

    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 choices=options)

    assert actual_value == value
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_selection_input_returns_last_option(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    value = options[-1]

    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 choices=options)

    assert actual_value == value
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_selection_input_ask_again_for_input_if_user_enter_value_not_in_options(
        input_wrapper
):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    existing_value = options[2]

    input_wrapper._actual_input.side_effect = ["G", existing_value]

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 choices=options)

    assert actual_value == existing_value
    assert input_wrapper._actual_input.call_count == 2
    assert input_wrapper._actual_input.call_args_list[0] == call(prompt)
    assert input_wrapper._actual_input.call_args_list[1] == call(prompt)


def test_selection_input_returns_default_when_user_did_not_inert_value(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    default = options[2]

    input_wrapper._actual_input.return_value = ""

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 default=default,
                                                 choices=options)

    assert actual_value == default
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_selection_input_returns_default_on_second_try(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    default = options[2]

    input_wrapper._actual_input.side_effect = ["H", ""]

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 default=default,
                                                 choices=options)

    assert actual_value == default
    assert input_wrapper._actual_input.call_count == 2
    assert input_wrapper._actual_input.call_args_list[0] == call(prompt)
    assert input_wrapper._actual_input.call_args_list[1] == call(prompt)


def test_selection_input_returns_default_when_input_wrapper_is_disabled(
        disabled_input_wrapper
):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    default = options[2]

    actual_value = disabled_input_wrapper.selection_input(
        prompt=prompt, default=default, choices=options
    )

    assert actual_value == default
    disabled_input_wrapper._actual_input.assert_not_called()


def test_selection_input_returns_middle_option_using_transform(input_wrapper):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]
    value = "d"

    input_wrapper._actual_input.return_value = value

    actual_value = input_wrapper.selection_input(
        prompt=prompt, choices=options, transform=str.upper
    )

    assert actual_value == "D"
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_selection_input_returns_transformed_value_on_second_try(
        input_wrapper
):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    input_wrapper._actual_input.side_effect = ["G", "d"]

    actual_value = input_wrapper.selection_input(prompt=prompt,
                                                 choices=options,
                                                 transform=str.upper)

    assert actual_value == "D"
    assert input_wrapper._actual_input.call_count == 2
    assert input_wrapper._actual_input.call_args_list[0] == call(prompt)
    assert input_wrapper._actual_input.call_args_list[1] == call(prompt)
