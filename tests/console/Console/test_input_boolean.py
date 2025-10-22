import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    ("user_input", "expected"),
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
def test_boolean(console, user_input, expected):
    question = "Are you handsome"
    prompt = "Are you handsome [y/N]? "
    console.values = [user_input]

    result = console.input_boolean(question=question)

    assert result == expected
    assert console.prompts == [prompt]


def test_boolean_default_true(console):
    """If True is the default, it is returned."""
    question = "Are you handsome"
    prompt = "Are you handsome [Y/n]? "
    console.values = [""]

    result = console.input_boolean(question=question, default=True)

    assert result
    assert console.prompts == [prompt]


def test_boolean_default_false(console):
    """If False is the default, it is returned."""
    question = "Are you handsome"
    prompt = "Are you handsome [y/N]? "
    console.values = [""]

    result = console.input_boolean(question=question, default=False)

    assert not result
    assert console.prompts == [prompt]


def test_boolean_default_None(console):
    """If no default is specified, no response is not accepted."""
    question = "Are you handsome"
    console.values = ["", "y"]

    result = console.input_boolean(question=question, default=None)

    assert result
    assert console.prompts == [f"{question} [y/n]? "] * 2


def test_bad_input(console):
    question = "Are you handsome"
    console.values = ["pork", "ham", "spam", "Yam"]

    result = console.input_boolean(question=question)

    assert result
    assert console.prompts == [f"{question} [y/N]? "] * 4


def test_disabled(disabled_console):
    """If input is disabled, the default is returned."""
    question = "Are you handsome "

    result = disabled_console.input_boolean(question=question)

    assert not result
    assert disabled_console.prompts == []


def test_disabled_no_default(disabled_console):
    """If input is disabled and there is no default, an error is raised."""
    question = "Are you handsome "

    with pytest.raises(InputDisabled):
        disabled_console.input_boolean(question=question, default=None)

    assert disabled_console.prompts == []
