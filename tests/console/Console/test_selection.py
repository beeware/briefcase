from unittest.mock import call

import pytest

from briefcase.console import InputDisabled
from tests.utils import default_rich_prompt


@pytest.mark.parametrize(
    "value, expected, default, transform",
    [
        ("A", "A", None, None),
        ("C", "C", None, None),
        ("", "D", "D", None),
        ("c", "C", None, str.upper),
    ],
)
def test_selection(console, value, expected, default, transform):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console.input.side_effect = [value]

    actual = console._selection(
        prompt=prompt,
        choices=options,
        default=default,
        transform=transform,
    )

    assert actual == expected
    console.input.assert_called_once_with(default_rich_prompt(prompt), markup=True)


def test_bad_input(console):
    """If the user enters bad input, they are shown an error and reprompted."""
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console.input.side_effect = ["G", "Q", "C"]

    actual = console._selection(prompt=prompt, choices=options)

    assert actual == "C"
    assert console.input.call_count == 3
    assert console.input.call_args_list[0] == call(
        default_rich_prompt(prompt), markup=True
    )
    assert console.input.call_args_list[1] == call(
        default_rich_prompt(prompt), markup=True
    )
    assert console.input.call_args_list[2] == call(
        default_rich_prompt(prompt), markup=True
    )


def test_disabled(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    actual = disabled_console._selection(prompt=prompt, choices=options, default="C")

    assert actual == "C"
    disabled_console.input.assert_not_called()


def test_disabled_no_default(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    with pytest.raises(InputDisabled):
        disabled_console._selection(
            prompt=prompt,
            choices=options,
            default=None,
        )

    disabled_console.input.assert_not_called()
