from unittest.mock import call

import pytest

from briefcase.console import InputDisabled


@pytest.mark.parametrize(
    "options, value, expected, default",
    [
        (["A", "B", "C", "D", "E", "F"], "1", "A", None),
        (["A", "B", "C", "D", "E", "F"], "3", "C", None),
        (["A", "B", "C", "D", "E", "F"], "3", "C", "A"),
        (["A", "B", "C", "D", "E", "F"], "", "D", "D"),
        ([("key1", "A"), ("key2", "B"), ("key3", "C"), ("key4", "D")], "1", "key1", None),
        ([("key1", "A"), ("key2", "B"), ("key3", "C"), ("key4", "D")], "3", "key3", None),
        ([("key1", "A"), ("key2", "B"), ("key3", "C"), ("key4", "D")], "3", "key3", "key1"),
        ([("key1", "A"), ("key2", "B"), ("key3", "C"), ("key4", "D")], "", "key4", "key4"),
        ({"key1": "A", "key2": "B", "key3": "C", "key4": "D"}, "1", "key1", None),
        ({"key1": "A", "key2": "B", "key3": "C", "key4": "D"}, "3", "key3", None),
        ({"key1": "A", "key2": "B", "key3": "C", "key4": "D"}, "3", "key3", "key1"),
        ({"key1": "A", "key2": "B", "key3": "C", "key4": "D"}, "", "key4", "key4"),
    ]
)
def test_selection_input(console, options, value, expected, default):
    prompt = "> "

    console._input.side_effect = [value]

    actual = console.selection_input(
        prompt=prompt,
        options=options,
        default=default,
    )

    assert actual == expected
    console._input.assert_called_once_with(prompt)


def test_bad_input(console):
    "If the user enters bad input, they are shown an error and reprompted"
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    console._input.side_effect = ["8", "10", "G", "ASDF", "3"]

    actual = console.selection_input(prompt=prompt, options=options)

    assert actual == "C"
    assert console._input.call_count == 5
    assert console._input.call_args_list[0] == call(prompt)
    assert console._input.call_args_list[1] == call(prompt)
    assert console._input.call_args_list[2] == call(prompt)
    assert console._input.call_args_list[3] == call(prompt)
    assert console._input.call_args_list[4] == call(prompt)


def test_disabled(disabled_console):
    prompt = "> "
    options = ["A", "B", "C", "D", "E", "F"]

    actual = disabled_console.selection_input(
        prompt=prompt,
        options=options,
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
            options=options,
            default=None,
        )

    disabled_console._input.assert_not_called()


@pytest.mark.parametrize(
    "options",
    (
            ["A", "B", "C", "D"],
            [("key1", "A"), ("key2", "B"), ("key3", "C"), ("key4", "D")],
            {"key1": "A", "key2": "B", "key3": "C", "key4": "D"},
    )
)
def test_intro_and_choices(console, capsys, options):
    "Ensure that intro and choices are properly printed"

    console._input.side_effect = ["1"]

    intro_text = """
    Line 1 of intro
    Line 2 of intro

    Line 3 of intro"""
    console.selection_input(intro=intro_text, prompt="> ", options=options)

    expected = intro_text + "\n\n" + "  1) A\n  2) B\n  3) C\n  4) D\n\n"

    assert capsys.readouterr().out == expected
