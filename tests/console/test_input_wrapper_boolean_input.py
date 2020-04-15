from unittest.mock import call


def test_boolean_input_returns_true_when_user_enters_y(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [y,N]: "
    input_wrapper._actual_input.return_value = "y"

    result = input_wrapper.boolean_input(question=question)

    assert result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_true_when_user_enters_yes(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [y,N]: "
    input_wrapper._actual_input.return_value = "yes"

    result = input_wrapper.boolean_input(question=question)

    assert result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_true_when_user_enters_yes_with_upper_case(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [y,N]: "
    input_wrapper._actual_input.return_value = "yEs"

    result = input_wrapper.boolean_input(question=question)

    assert result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_false_when_user_enters_n(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [Y,n]: "
    input_wrapper._actual_input.return_value = "n"

    result = input_wrapper.boolean_input(question=question, default=True)

    assert not result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_false_when_user_enters_no(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [Y,n]: "
    input_wrapper._actual_input.return_value = "no"

    result = input_wrapper.boolean_input(question=question, default=True)

    assert not result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_false_when_user_enters_no_with_upper_case(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [Y,n]: "
    input_wrapper._actual_input.return_value = "nO"

    result = input_wrapper.boolean_input(question=question, default=True)

    assert not result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_ask_again_if_input_value_is_invalid(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [Y,n]: "
    input_wrapper._actual_input.side_effect = ["bla", "n"]

    result = input_wrapper.boolean_input(question=question, default=True)

    assert not result
    assert input_wrapper._actual_input.call_count == 2
    assert input_wrapper._actual_input.call_args_list[0] == call(prompt)
    assert input_wrapper._actual_input.call_args_list[1] == call(prompt)


def test_boolean_input_returns_false_as_default_if_it_was_not_specified(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [y,N]: "
    input_wrapper._actual_input.return_value = ""

    result = input_wrapper.boolean_input(question=question)

    assert not result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_false_as_default_if_default_is_false(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [y,N]: "
    input_wrapper._actual_input.return_value = ""

    result = input_wrapper.boolean_input(question=question, default=False)

    assert not result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_true_as_default_if_default_is_true(input_wrapper):

    question = "Are you handsome?"
    prompt = "Are you handsome? [Y,n]: "
    input_wrapper._actual_input.return_value = ""

    result = input_wrapper.boolean_input(question=question, default=True)

    assert result
    input_wrapper._actual_input.assert_called_once_with(prompt)


def test_boolean_input_returns_default_if_disabled(disabled_input_wrapper):

    question = "Are you handsome?"

    result = disabled_input_wrapper.boolean_input(question=question, default=True)

    assert result
    disabled_input_wrapper._actual_input.assert_not_called()
