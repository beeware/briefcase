from unittest.mock import call

import pytest

from briefcase.console import InputDisabled
from briefcase.exceptions import BriefcaseCommandError


@pytest.mark.parametrize(
    "value, expected", [
        ("Value", "Value"),
        ("", "Default"),
    ]
)
def test_text_input(console, value, expected):
    prompt = "> "
    default = "Default"

    console._input.return_value = value

    actual = console.text_input(prompt=prompt, default=default)

    assert actual == expected
    console._input.assert_called_once_with(prompt)


def test_disabled(disabled_console):
    "If input is disabled, the default is returned"
    prompt = "> "

    actual = disabled_console.text_input(prompt=prompt, default="Default")

    assert actual == "Default"
    disabled_console._input.assert_not_called()


def test_disabled_no_default(disabled_console):
    "If input is disabled and there is no default, an error is raised"
    prompt = "> "

    with pytest.raises(InputDisabled):
        disabled_console.text_input(prompt=prompt, default=None)

    disabled_console._input.assert_not_called()


def test_validator(console, capsys):
    "If the user enters text and there's validation, the user is prompted until valid text is entered"
    prompt = "> "

    console._input.side_effect = ["bad", "not bad"]

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")

    console.text_input(prompt=prompt, validator=validator)

    assert console._input.call_count == 2
    assert console._input.call_args_list[0] == call(prompt)
    assert console._input.call_args_list[1] == call(prompt)

    assert capsys.readouterr().out == "\nInvalid value; That's bad...\n\n"


def test_input_disabled_validator(disabled_console):
    "If input is disabled, and validation fails, an error is raised"
    prompt = "> "

    def validator(text):
        if text == "bad":
            raise ValueError("That's bad...")

    with pytest.raises(BriefcaseCommandError):
        disabled_console.text_input(prompt=prompt, validator=validator, default="bad")


def test_assembled_prompt(console):
    "If a prompt isn't provided, ensure the prompt is properly assembled"
    console._input.side_effect = ["BSD"]
    console.text_input(input_name="Project License", default="MIT")

    console._input.assert_called_once_with("Project License [MIT]: ")


def test_prompt_capitalization(console):
    console._input.side_effect = ["www.example.com"]
    console.text_input(input_name="user's URL", default="example.com")

    console._input.assert_called_once_with("User's URL [example.com]: ")


def test_intro(console, capsys):
    "Ensure that intro is printed with expected line breaks"
    intro_text = """
Line 1 of intro
Line 2 of intro

Line 3 of intro"""
    console.text_input(intro=intro_text, prompt="> ")

    assert capsys.readouterr().out == '\nLine 1 of intro\nLine 2 of intro\n\nLine 3 of intro\n\n'
