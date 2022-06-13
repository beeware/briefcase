import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    "user_input, expected",
    [
        ("y", True),
        ("Y", True),
        ("yes", True),
        ("YES", True),
        ("Yes", True),
        ("YeS", True),
        ("Yay", True),
        ("Yaaaas!", True),
        ("n", False),
        ("N", False),
        ("No", False),
        ("NO", False),
        ("Nay", False),
        ("never!", False),
    ],
)
def test_boolean_input(console, user_input, expected):
    question = "Are you handsome"
    prompt = "Are you handsome [y/N]? "
    console.input.side_effect = [user_input]

    result = console.boolean_input(question=question)

    assert result == expected
    console.input.assert_called_once_with(prompt, markup=False)


def test_boolean_default_true(console):
    """If True is the default, it is returned."""
    question = "Are you handsome"
    prompt = "Are you handsome [Y/n]? "
    console.input.side_effect = [""]

    result = console.boolean_input(question=question, default=True)

    assert result
    console.input.assert_called_once_with(prompt, markup=False)


def test_boolean_default_false(console):
    """If False is the default, it is returned."""
    question = "Are you handsome"
    prompt = "Are you handsome [y/N]? "
    console.input.side_effect = [""]

    result = console.boolean_input(question=question, default=False)

    assert not result
    console.input.assert_called_once_with(prompt, markup=False)


def test_boolean_default_None(console):
    """If no default is specified, no response is not accepted."""
    question = "Are you handsome"
    console.input.side_effect = ["", "y"]

    result = console.boolean_input(question=question, default=None)

    assert result
    assert console.input.call_count == 2


def test_bad_input(console):
    question = "Are you handsome"
    console.input.side_effect = ["pork", "ham", "spam", "Yam"]

    result = console.boolean_input(question=question)

    assert result
    assert console.input.call_count == 4


def test_disabled(disabled_console):
    """If input is disabled, the default is returned."""
    question = "Are you handsome "

    result = disabled_console.boolean_input(question=question)

    assert not result
    disabled_console.input.assert_not_called()


def test_disabled_no_default(disabled_console):
    """If input is disabled and there is no default, an error is raised."""
    question = "Are you handsome "

    with pytest.raises(InputDisabled):
        disabled_console.boolean_input(question=question, default=None)

    disabled_console.input.assert_not_called()
