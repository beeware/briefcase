import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    ("value", "expected", "default", "transform"),
    [
        ("A", "A", None, None),
        ("C", "C", None, None),
        ("", "D", "D", None),
        ("c", "C", None, str.upper),
    ],
)
def test_input_selection(console, value, expected, default, transform):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console.values = [value]

    actual = console.input_selection(
        prompt=prompt,
        choices=options,
        default=default,
        transform=transform,
    )

    assert actual == expected
    assert console.prompts == [prompt]


def test_bad_input(console):
    """If the user enters bad input, they are shown an error and reprompted."""
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console.values = ["G", "Q", "C"]

    actual = console.input_selection(prompt=prompt, choices=options)

    assert actual == "C"
    assert console.prompts == [prompt] * 3


def test_disabled(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    actual = disabled_console.input_selection(
        prompt=prompt, choices=options, default="C"
    )

    assert actual == "C"
    assert disabled_console.prompts == []


def test_disabled_no_default(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    with pytest.raises(InputDisabled):
        disabled_console.input_selection(
            prompt=prompt,
            choices=options,
            default=None,
        )

    assert disabled_console.prompts == []
