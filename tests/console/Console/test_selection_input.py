from unittest.mock import call

import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    "value, expected, default, transform", [
        ("A", "A", None, None),
        ("C", "C", None, None),
        ("", "D", "D", None),
        ("c", "C", None, str.upper),
    ]
)
def test_selection_input(console, value, expected, default, transform):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console._input.side_effect = [value]

    actual = console.selection_input(
        prompt=prompt,
        choices=options,
        default=default,
        transform=transform,
    )

    assert actual == expected
    console._input.assert_called_once_with(prompt)


def test_bad_input(console):
    "If the user enters bad input, they are shown an error and reprompted"
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console._input.side_effect = ["G", "Q", "C"]

    actual = console.selection_input(prompt=prompt, choices=options)

    assert actual == "C"
    assert console._input.call_count == 3
    assert console._input.call_args_list[0] == call(prompt)
    assert console._input.call_args_list[1] == call(prompt)
    assert console._input.call_args_list[2] == call(prompt)


def test_disabled(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    actual = disabled_console.selection_input(
        prompt=prompt,
        choices=options,
        default="C"
    )

    assert actual == "C"
    disabled_console._input.assert_not_called()


def test_disabled_no_default(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    with pytest.raises(InputDisabled):
        disabled_console.selection_input(
            prompt=prompt,
            choices=options,
            default=None,
        )

    disabled_console._input.assert_not_called()
